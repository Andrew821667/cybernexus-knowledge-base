#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для работы с данными фреймворков MITRE ATT&CK и NIST в базе знаний КиберНексус
"""

import json
import sqlite3
import os
import requests
from typing import List, Dict, Any, Optional, Union, Tuple

class MitreNistAccessor:
    """Класс для работы с данными MITRE ATT&CK и NIST"""
    
    def __init__(self, knowledge_base_accessor=None):
        """
        Инициализация модуля
        
        Args:
            knowledge_base_accessor: Экземпляр основного класса для доступа к базе знаний
        """
        self.kb_accessor = knowledge_base_accessor
        self.storage_type = knowledge_base_accessor.storage_type if knowledge_base_accessor else "json"
        self.path = knowledge_base_accessor.path if knowledge_base_accessor else "./knowledge_base"
        self.db = knowledge_base_accessor.db if knowledge_base_accessor and self.storage_type == "sqlite" else None
        self.data = knowledge_base_accessor.data if knowledge_base_accessor and self.storage_type == "json" else None
        
        # Проверка и создание структуры для MITRE и NIST если хранилище JSON
        if self.storage_type == "json" and self.data:
            self._ensure_mitre_nist_structure()
        
        # Инициализация схемы SQLite, если необходимо
        if self.storage_type == "sqlite" and self.db:
            self._initialize_schema()
    
    def _ensure_mitre_nist_structure(self):
        """Создает структуру для MITRE и NIST в JSON-хранилище, если она отсутствует"""
        if "mitre_attack" not in self.data:
            self.data["mitre_attack"] = {
                "tactics": {},
                "techniques": {},
                "subtechniques": {}
            }
        
        if "nist" not in self.data:
            self.data["nist"] = {
                "categories": {},
                "controls": {}
            }
        
        # Сохраняем изменения в файл, если это не внешний экземпляр KnowledgeBaseAccessor
        if not self.kb_accessor:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def _initialize_schema(self):
        """Инициализирует схему в SQLite, если таблицы не существуют"""
        if self.db:
            cursor = self.db.cursor()
            
            # Проверяем наличие таблиц MITRE и NIST
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mitre_tactics'")
            result = cursor.fetchone()
            
            if not result:
                # Загружаем и применяем схему
                schema_path = os.path.join(os.path.dirname(__file__), 'schema_mitre_nist.sql')
                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema = f.read()
                    try:
                        self.db.executescript(schema)
                        self.db.commit()
                        print("Схема MITRE ATT&CK и NIST успешно создана")
                    except sqlite3.Error as e:
                        self.db.rollback()
                        raise Exception(f"Ошибка создания схемы MITRE ATT&CK и NIST: {e}")
                else:
                    raise FileNotFoundError(f"Файл схемы {schema_path} не найден")

    # Методы для работы с тактиками MITRE ATT&CK
    
    def get_mitre_tactics(self) -> List[Dict[str, Any]]:
        """
        Получение списка всех тактик MITRE ATT&CK
        
        Returns:
            Список словарей с информацией о тактиках
        """
        if self.storage_type == "json":
            tactics = []
            for tactic_id, tactic_data in self.data.get("mitre_attack", {}).get("tactics", {}).items():
                tactic = tactic_data.copy()
                tactic["id"] = tactic_id
                tactics.append(tactic)
            return tactics
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM mitre_tactics ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_mitre_tactic(self, tactic_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о тактике MITRE ATT&CK по ID
        
        Args:
            tactic_id: Идентификатор тактики (например, 'TA0001')
            
        Returns:
            Словарь с информацией о тактике или None, если тактика не найдена
        """
        if self.storage_type == "json":
            tactic_data = self.data.get("mitre_attack", {}).get("tactics", {}).get(tactic_id)
            if tactic_data:
                result = tactic_data.copy()
                result["id"] = tactic_id
                return result
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM mitre_tactics WHERE id = ?", (tactic_id,))
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
    
    def add_mitre_tactic(self, tactic_data: Dict[str, Any]) -> str:
        """
        Добавление новой тактики MITRE ATT&CK
        
        Args:
            tactic_data: Данные о тактике, включая id, name, description, url
            
        Returns:
            ID добавленной тактики
        """
        tactic_id = tactic_data.get("id")
        if not tactic_id:
            raise ValueError("ID тактики обязателен")
        
        name = tactic_data.get("name", "")
        description = tactic_data.get("description", "")
        url = tactic_data.get("url", "")
        
        if self.storage_type == "json":
            # Создаем структуру, если она отсутствует
            if "mitre_attack" not in self.data:
                self.data["mitre_attack"] = {"tactics": {}, "techniques": {}, "subtechniques": {}}
            
            # Проверяем существование тактики с таким ID
            if tactic_id in self.data["mitre_attack"]["tactics"]:
                raise ValueError(f"Тактика с ID {tactic_id} уже существует")
            
            # Добавляем тактику
            self.data["mitre_attack"]["tactics"][tactic_id] = {
                "name": name,
                "description": description,
                "url": url
            }
            
            # Сохраняем изменения, если это не внешний экземпляр
            if not self.kb_accessor:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            elif hasattr(self.kb_accessor, '_save_json'):
                self.kb_accessor._save_json()
            
            return tactic_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование тактики
            cursor.execute("SELECT id FROM mitre_tactics WHERE id = ?", (tactic_id,))
            if cursor.fetchone():
                raise ValueError(f"Тактика с ID {tactic_id} уже существует")
            
            # Добавляем тактику
            try:
                cursor.execute(
                    """
                    INSERT INTO mitre_tactics (id, name, description, url)
                    VALUES (?, ?, ?, ?)
                    """,
                    (tactic_id, name, description, url)
                )
                
                # Обновляем индекс поиска
                cursor.execute(
                    """
                    INSERT INTO search_index 
                    (content, section, subsection, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name + " " + description,
                        "MITRE ATT&CK",
                        "Tactics",
                        "mitre_tactic",
                        tactic_id
                    )
                )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
            return tactic_id

    # Методы для работы с техниками MITRE ATT&CK
    
    def get_mitre_techniques(self, tactic_id: str = None) -> List[Dict[str, Any]]:
        """
        Получение списка техник MITRE ATT&CK
        
        Args:
            tactic_id: Опциональный ID тактики для фильтрации техник
            
        Returns:
            Список словарей с информацией о техниках
        """
        if self.storage_type == "json":
            techniques = []
            for tech_id, tech_data in self.data.get("mitre_attack", {}).get("techniques", {}).items():
                if tactic_id is None or tactic_id in tech_data.get("tactics", []):
                    technique = tech_data.copy()
                    technique["id"] = tech_id
                    techniques.append(technique)
            return techniques
        else:
            cursor = self.db.cursor()
            
            if tactic_id:
                cursor.execute("""
                    SELECT t.* FROM mitre_techniques t
                    JOIN mitre_tactic_technique_mappings m ON t.id = m.technique_id
                    WHERE m.tactic_id = ?
                    ORDER BY t.id
                """, (tactic_id,))
            else:
                cursor.execute("SELECT * FROM mitre_techniques ORDER BY id")
                
            techniques = [dict(row) for row in cursor.fetchall()]
            
            # Для каждой техники добавляем список связанных тактик
            for technique in techniques:
                tech_id = technique["id"]
                cursor.execute("""
                    SELECT tactic_id FROM mitre_tactic_technique_mappings
                    WHERE technique_id = ?
                """, (tech_id,))
                technique["tactics"] = [row["tactic_id"] for row in cursor.fetchall()]
                
                # Добавляем подтехники, если они есть
                cursor.execute("SELECT * FROM mitre_subtechniques WHERE parent_technique_id = ?", (tech_id,))
                technique["subtechniques"] = [dict(row) for row in cursor.fetchall()]
            
            return techniques
    
    def add_mitre_technique(self, technique_data: Dict[str, Any]) -> str:
        """
        Добавление новой техники MITRE ATT&CK
        
        Args:
            technique_data: Данные о технике, включая id, name, description, url, 
                           detection, mitigation и список тактик (tactics)
            
        Returns:
            ID добавленной техники
        """
        technique_id = technique_data.get("id")
        if not technique_id:
            raise ValueError("ID техники обязателен")
        
        name = technique_data.get("name", "")
        description = technique_data.get("description", "")
        url = technique_data.get("url", "")
        detection = technique_data.get("detection", "")
        mitigation = technique_data.get("mitigation", "")
        tactics = technique_data.get("tactics", [])
        
        if self.storage_type == "json":
            # Создаем структуру, если она отсутствует
            if "mitre_attack" not in self.data:
                self.data["mitre_attack"] = {"tactics": {}, "techniques": {}, "subtechniques": {}}
            
            # Проверяем существование техники с таким ID
            if technique_id in self.data["mitre_attack"]["techniques"]:
                raise ValueError(f"Техника с ID {technique_id} уже существует")
            
            # Добавляем технику
            self.data["mitre_attack"]["techniques"][technique_id] = {
                "name": name,
                "description": description,
                "url": url,
                "detection": detection,
                "mitigation": mitigation,
                "tactics": tactics
            }
            
            # Сохраняем изменения, если это не внешний экземпляр
            if not self.kb_accessor:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            elif hasattr(self.kb_accessor, '_save_json'):
                self.kb_accessor._save_json()
            
            return technique_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование техники
            cursor.execute("SELECT id FROM mitre_techniques WHERE id = ?", (technique_id,))
            if cursor.fetchone():
                raise ValueError(f"Техника с ID {technique_id} уже существует")
            
            try:
                # Начинаем транзакцию
                cursor.execute("BEGIN TRANSACTION")
                
                # Добавляем технику
                cursor.execute(
                    """
                    INSERT INTO mitre_techniques (id, name, description, url, detection, mitigation)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (technique_id, name, description, url, detection, mitigation)
                )
                
                # Добавляем связи с тактиками
                for tactic_id in tactics:
                    cursor.execute(
                        """
                        INSERT INTO mitre_tactic_technique_mappings (tactic_id, technique_id)
                        VALUES (?, ?)
                        """,
                        (tactic_id, technique_id)
                    )
                
                # Обновляем индекс поиска
                cursor.execute(
                    """
                    INSERT INTO search_index 
                    (content, section, subsection, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name + " " + description + " " + detection + " " + mitigation,
                        "MITRE ATT&CK",
                        "Techniques",
                        "mitre_technique",
                        technique_id
                    )
                )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
            return technique_id

    def add_mitre_subtechnique(self, subtechnique_data: Dict[str, Any]) -> str:
        """
        Добавление новой подтехники MITRE ATT&CK
        
        Args:
            subtechnique_data: Данные о подтехнике, включая id, parent_technique_id, 
                              name, description, url, detection, mitigation
            
        Returns:
            ID добавленной подтехники
        """
        subtechnique_id = subtechnique_data.get("id")
        if not subtechnique_id:
            raise ValueError("ID подтехники обязателен")
        
        parent_technique_id = subtechnique_data.get("parent_technique_id")
        if not parent_technique_id:
            raise ValueError("ID родительской техники обязателен")
        
        name = subtechnique_data.get("name", "")
        description = subtechnique_data.get("description", "")
        url = subtechnique_data.get("url", "")
        detection = subtechnique_data.get("detection", "")
        mitigation = subtechnique_data.get("mitigation", "")
        
        if self.storage_type == "json":
            # Создаем структуру, если она отсутствует
            if "mitre_attack" not in self.data:
                self.data["mitre_attack"] = {"tactics": {}, "techniques": {}, "subtechniques": {}}
            
            # Проверяем существование подтехники с таким ID
            if subtechnique_id in self.data["mitre_attack"]["subtechniques"]:
                raise ValueError(f"Подтехника с ID {subtechnique_id} уже существует")
            
            # Проверяем существование родительской техники
            if parent_technique_id not in self.data["mitre_attack"]["techniques"]:
                raise ValueError(f"Родительская техника с ID {parent_technique_id} не найдена")
            
            # Добавляем подтехнику
            self.data["mitre_attack"]["subtechniques"][subtechnique_id] = {
                "parent_technique_id": parent_technique_id,
                "name": name,
                "description": description,
                "url": url,
                "detection": detection,
                "mitigation": mitigation
            }
            
            # Сохраняем изменения, если это не внешний экземпляр
            if not self.kb_accessor:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            elif hasattr(self.kb_accessor, '_save_json'):
                self.kb_accessor._save_json()
            
            return subtechnique_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование подтехники
            cursor.execute("SELECT id FROM mitre_subtechniques WHERE id = ?", (subtechnique_id,))
            if cursor.fetchone():
                raise ValueError(f"Подтехника с ID {subtechnique_id} уже существует")
            
            # Проверяем существование родительской техники
            cursor.execute("SELECT id FROM mitre_techniques WHERE id = ?", (parent_technique_id,))
            if not cursor.fetchone():
                raise ValueError(f"Родительская техника с ID {parent_technique_id} не найдена")
            
            try:
                cursor.execute(
                    """
                    INSERT INTO mitre_subtechniques (
                        id, parent_technique_id, name, description, url, detection, mitigation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (subtechnique_id, parent_technique_id, name, description, url, detection, mitigation)
                )
                
                # Обновляем индекс поиска
                cursor.execute(
                    """
                    INSERT INTO search_index 
                    (content, section, subsection, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name + " " + description + " " + detection + " " + mitigation,
                        "MITRE ATT&CK",
                        "Subtechniques",
                        "mitre_subtechnique",
                        subtechnique_id
                    )
                )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
            return subtechnique_id
    
    # Методы для работы с NIST
    
    def get_nist_categories(self, framework: str = None) -> List[Dict[str, Any]]:
        """
        Получение списка категорий NIST
        
        Args:
            framework: Опциональный фильтр по фреймворку (например, 'CSF', '800-53')
            
        Returns:
            Список словарей с информацией о категориях
        """
        if self.storage_type == "json":
            categories = []
            for category_id, category_data in self.data.get("nist", {}).get("categories", {}).items():
                if framework is None or category_data.get("framework") == framework:
                    category = category_data.copy()
                    category["id"] = category_id
                    categories.append(category)
            return categories
        else:
            cursor = self.db.cursor()
            
            if framework:
                cursor.execute("SELECT * FROM nist_categories WHERE framework = ? ORDER BY id", (framework,))
            else:
                cursor.execute("SELECT * FROM nist_categories ORDER BY framework, id")
                
            return [dict(row) for row in cursor.fetchall()]
    
    def add_nist_category(self, category_data: Dict[str, Any]) -> str:
        """
        Добавление новой категории NIST
        
        Args:
            category_data: Данные о категории, включая id, name, framework, description
            
        Returns:
            ID добавленной категории
        """
        category_id = category_data.get("id")
        if not category_id:
            raise ValueError("ID категории обязателен")
        
        name = category_data.get("name", "")
        framework = category_data.get("framework", "")
        description = category_data.get("description", "")
        
        if not framework:
            raise ValueError("Фреймворк NIST обязателен (например, 'CSF', '800-53')")
        
        if self.storage_type == "json":
            # Создаем структуру, если она отсутствует
            if "nist" not in self.data:
                self.data["nist"] = {"categories": {}, "controls": {}}
            
            # Проверяем существование категории с таким ID
            if category_id in self.data["nist"]["categories"]:
                raise ValueError(f"Категория с ID {category_id} уже существует")
            
            # Добавляем категорию
            self.data["nist"]["categories"][category_id] = {
                "name": name,
                "framework": framework,
                "description": description
            }
            
            # Сохраняем изменения, если это не внешний экземпляр
            if not self.kb_accessor:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
            elif hasattr(self.kb_accessor, '_save_json'):
                self.kb_accessor._save_json()
            
            return category_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование категории
            cursor.execute("SELECT id FROM nist_categories WHERE id = ?", (category_id,))
            if cursor.fetchone():
                raise ValueError(f"Категория с ID {category_id} уже существует")
            
            try:
                cursor.execute(
                    """
                    INSERT INTO nist_categories (id, name, framework, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (category_id, name, framework, description)
                )
                
                # Обновляем индекс поиска
                cursor.execute(
                    """
                    INSERT INTO search_index 
                    (content, section, subsection, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name + " " + description,
                        "NIST",
                        framework,
                        "nist_category",
                        category_id
                    )
                )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
            return category_id

    # Методы для связывания с другими элементами базы знаний
    
    def link_term_to_mitre(self, term_id: Union[str, int], mitre_id: str, mapping_type: str) -> bool:
        """
        Связывание термина с элементом MITRE ATT&CK
        
        Args:
            term_id: ID термина
            mitre_id: ID элемента MITRE ATT&CK
            mapping_type: Тип связи ('tactic', 'technique', 'subtechnique')
            
        Returns:
            True если связывание успешно, иначе False
        """
        # Проверяем тип связи
        if mapping_type not in ['tactic', 'technique', 'subtechnique']:
            raise ValueError("Недопустимый тип связи. Используйте 'tactic', 'technique' или 'subtechnique'")
        
        if self.storage_type == "json":
            # Преобразуем term_id в строку для поиска в JSON
            term_id_str = str(term_id)
            
            # Находим термин в базе знаний
            found = False
            for section in self.data.get("sections", []):
                if section.get("id") == "concepts_basics":
                    for subsection in section.get("subsections", []):
                        if subsection.get("id") == "basic_terms":
                            content = subsection.get("content", {})
                            for term_key, term_data in content.items():
                                if term_key == term_id_str or term_data.get("id") == term_id_str:
                                    found = True
                                    
                                    # Добавляем связи с MITRE
                                    if "mitre_links" not in term_data:
                                        term_data["mitre_links"] = []
                                    
                                    # Проверяем существование связи
                                    link_exists = False
                                    for link in term_data["mitre_links"]:
                                        if link.get("mitre_id") == mitre_id and link.get("mapping_type") == mapping_type:
                                            link_exists = True
                                            break
                                    
                                    if not link_exists:
                                        term_data["mitre_links"].append({
                                            "mitre_id": mitre_id,
                                            "mapping_type": mapping_type
                                        })
                                    
                                    # Сохраняем изменения
                                    if not self.kb_accessor:
                                        with open(self.path, 'w', encoding='utf-8') as f:
                                            json.dump(self.data, f, ensure_ascii=False, indent=2)
                                    elif hasattr(self.kb_accessor, '_save_json'):
                                        self.kb_accessor._save_json()
                                    
                                    return True
            
            if not found:
                raise ValueError(f"Термин с ID {term_id} не найден")
            
            return False
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование термина
            cursor.execute("SELECT id FROM terms WHERE id = ?", (term_id,))
            if not cursor.fetchone():
                raise ValueError(f"Термин с ID {term_id} не найден")
            
            # Проверяем существование элемента MITRE
            if mapping_type == 'tactic':
                cursor.execute("SELECT id FROM mitre_tactics WHERE id = ?", (mitre_id,))
            elif mapping_type == 'technique':
                cursor.execute("SELECT id FROM mitre_techniques WHERE id = ?", (mitre_id,))
            elif mapping_type == 'subtechnique':
                cursor.execute("SELECT id FROM mitre_subtechniques WHERE id = ?", (mitre_id,))
                
            if not cursor.fetchone():
                raise ValueError(f"Элемент MITRE с ID {mitre_id} не найден")
            
            try:
                # Проверяем существование связи
                cursor.execute(
                    """
                    SELECT * FROM term_mitre_mappings 
                    WHERE term_id = ? AND mitre_id = ? AND mapping_type = ?
                    """,
                    (term_id, mitre_id, mapping_type)
                )
                
                if cursor.fetchone():
                    return False  # Связь уже существует
                
                # Добавляем связь
                cursor.execute(
                    """
                    INSERT INTO term_mitre_mappings (term_id, mitre_id, mapping_type)
                    VALUES (?, ?, ?)
                    """,
                    (term_id, mitre_id, mapping_type)
                )
                
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                raise e
    
    def link_product_to_mitre(self, product_id: str, mitre_id: str, mapping_type: str, 
                             effectiveness: str = "Medium", description: str = "") -> bool:
        """
        Связывание продукта с элементом MITRE ATT&CK (какие техники блокирует)
        
        Args:
            product_id: ID продукта
            mitre_id: ID элемента MITRE ATT&CK
            mapping_type: Тип связи ('tactic', 'technique', 'subtechnique')
            effectiveness: Эффективность ('High', 'Medium', 'Low')
            description: Описание связи
            
        Returns:
            True если связывание успешно, иначе False
        """
        # Проверяем тип связи
        if mapping_type not in ['tactic', 'technique', 'subtechnique']:
            raise ValueError("Недопустимый тип связи. Используйте 'tactic', 'technique' или 'subtechnique'")
        
        # Проверяем эффективность
        if effectiveness not in ['High', 'Medium', 'Low']:
            raise ValueError("Недопустимый уровень эффективности. Используйте 'High', 'Medium' или 'Low'")
        
        if self.storage_type == "json":
            # Находим продукт в базе знаний
            found = False
            for section in self.data.get("sections", []):
                if section.get("id") == "products":
                    for subsection in section.get("subsections", []):
                        if subsection.get("id") == product_id:
                            found = True
                            
                            # Добавляем связи с MITRE
                            if "mitre_mappings" not in subsection:
                                subsection["mitre_mappings"] = []
                            
                            # Проверяем существование связи
                            link_exists = False
                            for link in subsection.get("mitre_mappings", []):
                                if link.get("mitre_id") == mitre_id and link.get("mapping_type") == mapping_type:
                                    link["effectiveness"] = effectiveness
                                    link["description"] = description
                                    link_exists = True
                                    break
                            
                            if not link_exists:
                                subsection["mitre_mappings"].append({
                                    "mitre_id": mitre_id,
                                    "mapping_type": mapping_type,
                                    "effectiveness": effectiveness,
                                    "description": description
                                })
                            
                            # Сохраняем изменения
                            if not self.kb_accessor:
                                with open(self.path, 'w', encoding='utf-8') as f:
                                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                            elif hasattr(self.kb_accessor, '_save_json'):
                                self.kb_accessor._save_json()
                            
                            return True
            
            if not found:
                raise ValueError(f"Продукт с ID {product_id} не найден")
            
            return False
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование продукта
            cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            if not cursor.fetchone():
                raise ValueError(f"Продукт с ID {product_id} не найден")
            
            # Проверяем существование элемента MITRE
            if mapping_type == 'tactic':
                cursor.execute("SELECT id FROM mitre_tactics WHERE id = ?", (mitre_id,))
            elif mapping_type == 'technique':
                cursor.execute("SELECT id FROM mitre_techniques WHERE id = ?", (mitre_id,))
            elif mapping_type == 'subtechnique':
                cursor.execute("SELECT id FROM mitre_subtechniques WHERE id = ?", (mitre_id,))
                
            if not cursor.fetchone():
                raise ValueError(f"Элемент MITRE с ID {mitre_id} не найден")
            
            try:
                # Проверяем существование связи
                cursor.execute(
                    """
                    SELECT * FROM product_mitre_mappings 
                    WHERE product_id = ? AND mitre_id = ? AND mapping_type = ?
                    """,
                    (product_id, mitre_id, mapping_type)
                )
                
                if cursor.fetchone():
                    # Обновляем существующую связь
                    cursor.execute(
                        """
                        UPDATE product_mitre_mappings
                        SET effectiveness = ?, description = ?
                        WHERE product_id = ? AND mitre_id = ? AND mapping_type = ?
                        """,
                        (effectiveness, description, product_id, mitre_id, mapping_type)
                    )
                else:
                    # Добавляем новую связь
                    cursor.execute(
                        """
                        INSERT INTO product_mitre_mappings (product_id, mitre_id, mapping_type, effectiveness, description)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (product_id, mitre_id, mapping_type, effectiveness, description)
                    )
                
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                raise e
