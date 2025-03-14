#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Библиотека для работы с базой знаний по кибербезопасности
Поддерживает два формата: JSON и SQLite
"""

import json
import sqlite3
import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple


class KnowledgeBaseAccessor:
    """Класс для доступа к базе знаний по кибербезопасности"""
    
    def __init__(self, storage_type: str = "json", path: str = "./knowledge_base"):
        """
        Инициализация доступа к базе знаний
        
        Args:
            storage_type: Тип хранилища ("json" или "sqlite")
            path: Путь к файлу или директории с базой знаний
        """
        self.storage_type = storage_type.lower()
        self.path = path
        self.db = None
        self.data = None
        
        if self.storage_type == "json":
            self._load_json()
        elif self.storage_type == "sqlite":
            self._connect_sqlite()
        else:
            raise ValueError(f"Неподдерживаемый тип хранилища: {storage_type}. Используйте 'json' или 'sqlite'.")
    
    def _load_json(self):
        """Загрузка базы знаний из JSON-файла"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"База знаний успешно загружена из {self.path}")
        except FileNotFoundError:
            print(f"Файл не найден: {self.path}. Создаётся новая база знаний.")
            self.data = {
                "database_info": {
                    "title": "База знаний по кибербезопасности",
                    "version": "1.0",
                    "last_updated": "",
                    "description": "База знаний компании по AI-решениям для кибербезопасности"
                },
                "company": {},
                "sections": []
            }
            self._save_json()
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка формата JSON в файле {self.path}")
    
    def _save_json(self):
        """Сохранение базы знаний в JSON-файл"""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"База знаний сохранена в {self.path}")
    
    def _connect_sqlite(self):
        """Подключение к базе данных SQLite"""
        try:
            self.db = sqlite3.connect(self.path)
            self.db.row_factory = sqlite3.Row
            print(f"Подключение к базе данных SQLite установлено: {self.path}")
            
            # Проверка наличия необходимых таблиц
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='database_info'")
            if not cursor.fetchone():
                print("Создание структуры базы данных...")
                self._create_sqlite_schema()
        except sqlite3.Error as e:
            raise ConnectionError(f"Ошибка подключения к SQLite базе данных: {e}")
    
    def _create_sqlite_schema(self):
        """Создание схемы базы данных SQLite"""
        with open('schema.sql', 'r', encoding='utf-8') as schema_file:
            schema = schema_file.read()
            
        try:
            self.db.executescript(schema)
            self.db.commit()
            print("Структура базы данных успешно создана")
        except sqlite3.Error as e:
            self.db.rollback()
            raise Exception(f"Ошибка создания структуры базы данных: {e}")
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.storage_type == "sqlite" and self.db:
            self.db.close()
            print("Соединение с базой данных закрыто")

    def get_company_info(self) -> Dict[str, Any]:
        """Получение информации о компании"""
        if self.storage_type == "json":
            return self.data.get("company", {})
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM company LIMIT 1")
            result = cursor.fetchone()
            if result:
                return dict(result)
            return {}
    
    def get_sections(self) -> List[Dict[str, Any]]:
        """Получение списка всех разделов"""
        if self.storage_type == "json":
            return self.data.get("sections", [])
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM sections ORDER BY order_index")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_section(self, section_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о разделе по ID
        
        Args:
            section_id: Идентификатор раздела
            
        Returns:
            Словарь с информацией о разделе или None, если раздел не найден
        """
        if self.storage_type == "json":
            for section in self.data.get("sections", []):
                if section.get("id") == section_id:
                    return section
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM sections WHERE id = ?", (section_id,))
            result = cursor.fetchone()
            if result:
                section_data = dict(result)
                
                # Добавляем подразделы
                cursor.execute("SELECT * FROM subsections WHERE section_id = ? ORDER BY order_index", (section_id,))
                section_data["subsections"] = [dict(row) for row in cursor.fetchall()]
                
                return section_data
            return None
    
    def get_subsection(self, section_id: str, subsection_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о подразделе
        
        Args:
            section_id: Идентификатор раздела
            subsection_id: Идентификатор подраздела
            
        Returns:
            Словарь с информацией о подразделе или None, если подраздел не найден
        """
        if self.storage_type == "json":
            section = self.get_section(section_id)
            if section:
                for subsection in section.get("subsections", []):
                    if subsection.get("id") == subsection_id:
                        return subsection
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT * FROM subsections WHERE id = ? AND section_id = ?",
                (subsection_id, section_id)
            )
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о продукте по ID
        
        Args:
            product_id: Идентификатор продукта
            
        Returns:
            Словарь с информацией о продукте или None, если продукт не найден
        """
        if self.storage_type == "json":
            # Ищем продукт в соответствующем разделе
            for section in self.data.get("sections", []):
                if section.get("id") == "products":
                    for subsection in section.get("subsections", []):
                        if subsection.get("id") == product_id:
                            return subsection
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
                
            product_data = dict(result)
            
            # Получаем целевую аудиторию
            cursor.execute("SELECT audience FROM product_audience WHERE product_id = ?", (product_id,))
            product_data["target_audience"] = [row["audience"] for row in cursor.fetchall()]
            
            # Получаем особенности
            cursor.execute("SELECT feature FROM product_features WHERE product_id = ?", (product_id,))
            product_data["key_features"] = [row["feature"] for row in cursor.fetchall()]
            
            # Получаем технические характеристики
            cursor.execute("SELECT * FROM product_technology WHERE product_id = ?", (product_id,))
            tech_result = cursor.fetchone()
            if tech_result:
                tech_data = dict(tech_result)
                
                # Получаем источники данных
                cursor.execute(
                    "SELECT data_source FROM product_data_sources WHERE technology_id = ?", 
                    (tech_data["id"],)
                )
                tech_data["data_sources"] = [row["data_source"] for row in cursor.fetchall()]
                
                product_data["technology"] = tech_data
            
            # Получаем кейсы
            cursor.execute("SELECT * FROM case_studies WHERE product_id = ?", (product_id,))
            product_data["case_studies"] = [dict(row) for row in cursor.fetchall()]
            
            return product_data
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Полнотекстовый поиск по базе знаний
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных элементов
        """
        if self.storage_type == "json":
            # Простой поиск по тексту в JSON
            results = []
            query_lower = query.lower()
            
            # Поиск в информации о компании
            company_info = self.data.get("company", {})
            company_text = json.dumps(company_info, ensure_ascii=False).lower()
            if query_lower in company_text:
                results.append({
                    "type": "company_info",
                    "title": company_info.get("name", "Компания"),
                    "content": company_info.get("description", "")
                })
            
            # Поиск в разделах и подразделах
            for section in self.data.get("sections", []):
                section_text = json.dumps(section, ensure_ascii=False).lower()
                if query_lower in section_text:
                    results.append({
                        "type": "section",
                        "id": section.get("id"),
                        "title": section.get("name", ""),
                        "content": section.get("description", "")
                    })
                
                for subsection in section.get("subsections", []):
                    subsection_text = json.dumps(subsection, ensure_ascii=False).lower()
                    if query_lower in subsection_text:
                        results.append({
                            "type": "subsection",
                            "section_id": section.get("id"),
                            "id": subsection.get("id"),
                            "title": subsection.get("name", ""),
                            "content": str(subsection.get("content", ""))[:100] + "..."
                        })
            
            return results
        else:
            # Полнотекстовый поиск в SQLite
            cursor = self.db.cursor()
            
            # Подготовка запроса для полнотекстового поиска
            query = ' '.join(f'"{word}"' for word in re.findall(r'\w+', query))
            
            cursor.execute(
                """
                SELECT * FROM search_index
                WHERE content MATCH ?
                ORDER BY rank
                LIMIT 20
                """,
                (query,)
            )
            
            results = []
            for row in cursor.fetchall():
                result_data = dict(row)
                
                # Получаем дополнительные данные в зависимости от типа
                entity_type = result_data["entity_type"]
                entity_id = result_data["entity_id"]
                
                if entity_type == "section":
                    cursor.execute("SELECT name, description FROM sections WHERE id = ?", (entity_id,))
                    section_data = cursor.fetchone()
                    if section_data:
                        result_data["title"] = section_data["name"]
                        result_data["content"] = section_data["description"]
                
                elif entity_type == "subsection":
                    cursor.execute("SELECT name FROM subsections WHERE id = ?", (entity_id,))
                    subsection_data = cursor.fetchone()
                    if subsection_data:
                        result_data["title"] = subsection_data["name"]
                
                elif entity_type == "term":
                    cursor.execute("SELECT term, definition FROM terms WHERE id = ?", (entity_id,))
                    term_data = cursor.fetchone()
                    if term_data:
                        result_data["title"] = term_data["term"]
                        result_data["content"] = term_data["definition"]
                
                elif entity_type == "product":
                    cursor.execute("SELECT name, description FROM products WHERE id = ?", (entity_id,))
                    product_data = cursor.fetchone()
                    if product_data:
                        result_data["title"] = product_data["name"]
                        result_data["content"] = product_data["description"]
                
                results.append(result_data)
            
            return results
    
    def add_section(self, section_data: Dict[str, Any]) -> str:
        """
        Добавление нового раздела
        
        Args:
            section_data: Данные о разделе
            
        Returns:
            ID добавленного раздела
        """
        section_id = section_data.get("id")
        if not section_id:
            raise ValueError("ID раздела обязателен")
        
        if self.storage_type == "json":
            # Проверяем существование раздела с таким ID
            for section in self.data.get("sections", []):
                if section.get("id") == section_id:
                    raise ValueError(f"Раздел с ID {section_id} уже существует")
            
            # Добавляем новый раздел
            if "sections" not in self.data:
                self.data["sections"] = []
            
            self.data["sections"].append(section_data)
            self._save_json()
            
            return section_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование раздела
            cursor.execute("SELECT id FROM sections WHERE id = ?", (section_id,))
            if cursor.fetchone():
                raise ValueError(f"Раздел с ID {section_id} уже существует")
            
            # Получаем максимальный индекс для сортировки
            cursor.execute("SELECT MAX(order_index) FROM sections")
            result = cursor.fetchone()
            max_order = result[0] if result[0] is not None else 0
            
            # Добавляем раздел
            cursor.execute(
                """
                INSERT INTO sections (id, name, description, order_index)
                VALUES (?, ?, ?, ?)
                """,
                (
                    section_id,
                    section_data.get("name", ""),
                    section_data.get("description", ""),
                    max_order + 1
                )
            )
            
            # Добавляем подразделы
            for i, subsection in enumerate(section_data.get("subsections", [])):
                cursor.execute(
                    """
                    INSERT INTO subsections (id, section_id, name, order_index)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        subsection.get("id", f"{section_id}_sub{i}"),
                        section_id,
                        subsection.get("name", ""),
                        i
                    )
                )
            
            self.db.commit()
            return section_id
    
    def add_product(self, product_data: Dict[str, Any]) -> str:
        """
        Добавление нового продукта
        
        Args:
            product_data: Данные о продукте
            
        Returns:
            ID добавленного продукта
        """
        product_id = product_data.get("id")
        if not product_id:
            raise ValueError("ID продукта обязателен")
        
        if self.storage_type == "json":
            # Проверяем наличие раздела продуктов
            products_section = None
            for section in self.data.get("sections", []):
                if section.get("id") == "products":
                    products_section = section
                    break
            
            # Создаем раздел продуктов, если его нет
            if not products_section:
                products_section = {
                    "id": "products",
                    "name": "Продукты",
                    "description": "Продукты компании по кибербезопасности",
                    "subsections": []
                }
                self.data["sections"].append(products_section)
            
            # Проверяем существование продукта с таким ID
            for subsection in products_section.get("subsections", []):
                if subsection.get("id") == product_id:
                    raise ValueError(f"Продукт с ID {product_id} уже существует")
            
            # Добавляем продукт как подраздел
            if "subsections" not in products_section:
                products_section["subsections"] = []
            
            products_section["subsections"].append(product_data)
            self._save_json()
            
            return product_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем существование продукта
            cursor.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            if cursor.fetchone():
                raise ValueError(f"Продукт с ID {product_id} уже существует")
            
            # Добавляем продукт
            try:
                cursor.execute(
                    """
                    INSERT INTO products (id, name, description, subsection_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        product_data.get("name", ""),
                        product_data.get("description", ""),
                        product_data.get("subsection_id")
                    )
                )
                
                # Добавляем целевую аудиторию
                for audience in product_data.get("target_audience", []):
                    cursor.execute(
                        "INSERT INTO product_audience (product_id, audience) VALUES (?, ?)",
                        (product_id, audience)
                    )
                
                # Добавляем ключевые особенности
                for feature in product_data.get("key_features", []):
                    cursor.execute(
                        "INSERT INTO product_features (product_id, feature) VALUES (?, ?)",
                        (product_id, feature)
                    )
                
                # Добавляем технические характеристики
                tech_data = product_data.get("technology", {})
                if tech_data:
                    cursor.execute(
                        """
                        INSERT INTO product_technology 
                        (product_id, core, architecture, visualization)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            product_id,
                            tech_data.get("core", ""),
                            tech_data.get("architecture", ""),
                            tech_data.get("visualization", "")
                        )
                    )
                    
                    # Получаем ID добавленной технологии
                    cursor.execute("SELECT last_insert_rowid()")
                    tech_id = cursor.fetchone()[0]
                    
                    # Добавляем источники данных
                    for source in tech_data.get("data_sources", []):
                        cursor.execute(
                            "INSERT INTO product_data_sources (technology_id, data_source) VALUES (?, ?)",
                            (tech_id, source)
                        )
                
                # Добавляем кейсы
                for case in product_data.get("case_studies", []):
                    cursor.execute(
                        """
                        INSERT INTO case_studies 
                        (product_id, customer, challenge, solution, results)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            product_id,
                            case.get("customer", ""),
                            case.get("challenge", ""),
                            case.get("solution", ""),
                            case.get("results", "")
                        )
                    )
                
                # Обновляем индекс поиска
                cursor.execute(
                    """
                    INSERT INTO search_index 
                    (content, section, subsection, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        product_data.get("name", "") + " " + product_data.get("description", ""),
                        "Продукты",
                        product_data.get("name", ""),
                        "product",
                        product_id
                    )
                )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
            return product_id
    
    def add_term(self, term_data: Dict[str, Any], section_id: str = "concepts_basics", subsection_id: str = "basic_terms") -> int:
        """
        Добавление нового термина
        
        Args:
            term_data: Данные о термине
            section_id: ID раздела (по умолчанию "concepts_basics")
            subsection_id: ID подраздела (по умолчанию "basic_terms")
            
        Returns:
            ID добавленного термина
        """
        term = term_data.get("term")
        if not term:
            raise ValueError("Название термина обязательно")
        
        definition = term_data.get("definition", "")
        
        if self.storage_type == "json":
            # Находим раздел и подраздел
            section = self.get_section(section_id)
            if not section:
                raise ValueError(f"Раздел с ID {section_id} не найден")
            
            subsection = None
            for sub in section.get("subsections", []):
                if sub.get("id") == subsection_id:
                    subsection = sub
                    break
            
            if not subsection:
                raise ValueError(f"Подраздел с ID {subsection_id} не найден")
            
            # Добавляем/обновляем контент подраздела
            if "content" not in subsection:
                subsection["content"] = {}
            
            # Создаем идентификатор для термина
            term_id = term.lower().replace(" ", "_")
            
            # Добавляем термин
            subsection["content"][term_id] = term_data
            
            self._save_json()
            return term_id
        else:
            cursor = self.db.cursor()
            
            # Проверяем наличие подраздела
            cursor.execute(
                "SELECT id FROM subsections WHERE id = ? AND section_id = ?",
                (subsection_id, section_id)
            )
            if not cursor.fetchone():
                raise ValueError(f"Подраздел с ID {subsection_id} в разделе {section_id} не найден")
            
            try:
                # Добавляем термин
                cursor.execute(
                    """
                    INSERT INTO terms (subsection_id, term, definition)
                    VALUES (?, ?, ?)
                    """,
                    (subsection_id, term, definition)
                )
                
                # Получаем ID добавленного термина
                cursor.execute("SELECT last_insert_rowid()")
                term_id = cursor.fetchone()[0]
                
                # Добавляем связанные термины
                for related_term in term_data.get("related_terms", []):
                    cursor.execute(
                        "INSERT INTO related_terms (term_id, related_term) VALUES (?, ?)",
                        (term_id, related_term)
                    )
                
                # Обновляем индекс поиска
                cursor.execute(
                    """
                    INSERT INTO search_index 
                    (content, section, subsection, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        term + " " + definition,
                        section_id,
                        subsection_id,
                        "term",
                        term_id
                    )
                )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
            
            return term_id
    
    def update_company_info(self, company_data: Dict[str, Any]) -> None:
        """
        Обновление информации о компании
        
        Args:
            company_data: Данные о компании
        """
        if self.storage_type == "json":
            self.data["company"] = company_data
            self._save_json()
        else:
            cursor = self.db.cursor()
            
            # Проверяем наличие записи о компании
            cursor.execute("SELECT id FROM company LIMIT 1")
            result = cursor.fetchone()
            
            try:
                if result:
                    # Обновляем существующую запись
                    cursor.execute(
                        """
                        UPDATE company
                        SET name = ?, description = ?, mission = ?, unique_value = ?, foundation_year = ?
                        WHERE id = ?
                        """,
                        (
                            company_data.get("name", ""),
                            company_data.get("description", ""),
                            company_data.get("mission", ""),
                            company_data.get("unique_value", ""),
                            company_data.get("foundation_year"),
                            result[0]
                        )
                    )
                else:
                    # Создаем новую запись
                    cursor.execute(
                        """
                        INSERT INTO company
                        (name, description, mission, unique_value, foundation_year)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            company_data.get("name", ""),
                            company_data.get("description", ""),
                            company_data.get("mission", ""),
                            company_data.get("unique_value", ""),
                            company_data.get("foundation_year")
                        )
                    )
                
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                raise e
    
    def remove_section(self, section_id: str) -> bool:
        """
        Удаление раздела по ID
        
        Args:
            section_id: Идентификатор раздела
            
        Returns:
            True, если раздел успешно удален, иначе False
        """
        if self.storage_type == "json":
            for i, section in enumerate(self.data.get("sections", [])):
                if section.get("id") == section_id:
                    self.data["sections"].pop(i)
                    self._save_json()
                    return True
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                cursor.execute("DELETE FROM sections WHERE id = ?", (section_id,))
                
                # Каскадное удаление произойдет автоматически благодаря 
                # ограничениям ON DELETE CASCADE в схеме базы данных
                
                self.db.commit()
                
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    def export_to_json(self, output_path: str) -> None:
        """
        Экспорт базы знаний в формат JSON
        
        Args:
            output_path: Путь к файлу для экспорта
        """
        if self.storage_type == "json":
            # Просто копируем текущий файл
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"База знаний экспортирована в {output_path}")
        else:
            # Преобразуем данные из SQLite в JSON
            export_data = {
                "database_info": {},
                "company": {},
                "sections": []
            }
            
            cursor = self.db.cursor()
            
            # Получаем информацию о базе данных
            cursor.execute("SELECT * FROM database_info LIMIT 1")
            db_info = cursor.fetchone()
            if db_info:
                export_data["database_info"] = dict(db_info)
            
            # Получаем информацию о компании
            cursor.execute("SELECT * FROM company LIMIT 1")
            company_info = cursor.fetchone()
            if company_info:
                export_data["company"] = dict(company_info)
            
            # Получаем все разделы
            cursor.execute("SELECT * FROM sections ORDER BY order_index")
            sections = [dict(row) for row in cursor.fetchall()]
            
            for section in sections:
                section_id = section["id"]
                
                # Получаем подразделы для каждого раздела
                cursor.execute("SELECT * FROM subsections WHERE section_id = ? ORDER BY order_index", (section_id,))
                subsections = [dict(row) for row in cursor.fetchall()]
                
                section["subsections"] = []
                
                for subsection in subsections:
                    subsection_id = subsection["id"]
                    
                    # В зависимости от типа подраздела, получаем соответствующий контент
                    if "basic_terms" in subsection_id:
                        # Получаем термины
                        cursor.execute("SELECT * FROM terms WHERE subsection_id = ?", (subsection_id,))
                        terms = [dict(row) for row in cursor.fetchall()]
                        
                        subsection["content"] = {}
                        
                        for term in terms:
                            term_id = term["id"]
                            term_name = term["term"].lower().replace(" ", "_")
                            
                            # Получаем связанные термины
                            cursor.execute("SELECT related_term FROM related_terms WHERE term_id = ?", (term_id,))
                            related_terms = [row["related_term"] for row in cursor.fetchall()]
                            
                            subsection["content"][term_name] = {
                                "term": term["term"],
                                "definition": term["definition"],
                                "related_terms": related_terms
                            }
                    
                    section["subsections"].append(subsection)
                
                export_data["sections"].append(section)
            
            # Сохраняем экспортированные данные
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"База знаний экспортирована в {output_path}")
    
    def import_from_json(self, input_path: str) -> None:
        """
        Импорт базы знаний из формата JSON
        
        Args:
            input_path: Путь к файлу для импорта
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if self.storage_type == "json":
                # Просто заменяем текущие данные
                self.data = import_data
                self._save_json()
                print(f"База знаний импортирована из {input_path}")
            else:
                # Импортируем данные в SQLite
                cursor = self.db.cursor()
                
                # Очищаем текущие данные
                try:
                    cursor.execute("DELETE FROM database_info")
                    cursor.execute("DELETE FROM company")
                    cursor.execute("DELETE FROM sections")
                    
                    # Информация о базе данных
                    db_info = import_data.get("database_info", {})
                    if db_info:
                        cursor.execute(
                            """
                            INSERT INTO database_info (title, version, last_updated, description)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                db_info.get("title", ""),
                                db_info.get("version", "1.0"),
                                db_info.get("last_updated", ""),
                                db_info.get("description", "")
                            )
                        )
                    
                    # Информация о компании
                    company_info = import_data.get("company", {})
                    if company_info:
                        cursor.execute(
                            """
                            INSERT INTO company (name, description, mission, unique_value, foundation_year)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                company_info.get("name", ""),
                                company_info.get("description", ""),
                                company_info.get("mission", ""),
                                company_info.get("unique_value", ""),
                                company_info.get("foundation_year")
                            )
                        )
                    
                    # Импорт разделов и подразделов
                    for i, section in enumerate(import_data.get("sections", [])):
                        section_id = section.get("id", f"section_{i}")
                        
                        cursor.execute(
                            """
                            INSERT INTO sections (id, name, description, order_index)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                section_id,
                                section.get("name", ""),
                                section.get("description", ""),
                                i
                            )
                        )
                        
                        # Импорт подразделов
                        for j, subsection in enumerate(section.get("subsections", [])):
                            subsection_id = subsection.get("id", f"{section_id}_sub_{j}")
                            
                            cursor.execute(
                                """
                                INSERT INTO subsections (id, section_id, name, order_index)
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    subsection_id,
                                    section_id,
                                    subsection.get("name", ""),
                                    j
                                )
                            )
                            
                            # Импорт содержимого подраздела в зависимости от типа
                            content = subsection.get("content", {})
                            
                            if content and "basic_terms" in subsection_id:
                                # Импорт терминов
                                for term_id, term_data in content.items():
                                    cursor.execute(
                                        """
                                        INSERT INTO terms (subsection_id, term, definition)
                                        VALUES (?, ?, ?)
                                        """,
                                        (
                                            subsection_id,
                                            term_data.get("term", ""),
                                            term_data.get("definition", "")
                                        )
                                    )
                                    
                                    # Получаем ID добавленного термина
                                    cursor.execute("SELECT last_insert_rowid()")
                                    new_term_id = cursor.fetchone()[0]
                                    
                                    # Добавляем связанные термины
                                    for related_term in term_data.get("related_terms", []):
                                        cursor.execute(
                                            """
                                            INSERT INTO related_terms (term_id, related_term)
                                            VALUES (?, ?)
                                            """,
                                            (new_term_id, related_term)
                                        )
                                    
                                    # Обновляем индекс поиска
                                    cursor.execute(
                                        """
                                        INSERT INTO search_index 
                                        (content, section, subsection, entity_type, entity_id)
                                        VALUES (?, ?, ?, ?, ?)
                                        """,
                                        (
                                            term_data.get("term", "") + " " + term_data.get("definition", ""),
                                            section_id,
                                            subsection_id,
                                            "term",
                                            new_term_id
                                        )
                                    )
                    
                    self.db.commit()
                    print(f"База знаний импортирована из {input_path}")
                except Exception as e:
                    self.db.rollback()
                    raise Exception(f"Ошибка при импорте данных: {e}")
        except Exception as e:
            raise Exception(f"Ошибка при импорте из JSON: {e}")
