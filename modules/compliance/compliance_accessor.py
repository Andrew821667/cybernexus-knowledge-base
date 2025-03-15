#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Библиотека для работы с данными о соответствии нормативным требованиям
Поддерживает два формата: JSON и SQLite
"""

import json
import sqlite3
import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime


class ComplianceAccessor:
    """Класс для доступа к данным о соответствии нормативным требованиям"""
    
    def __init__(self, storage_type: str = "json", path: str = None, kb_path: str = None):
        """
        Инициализация доступа к данным о соответствии нормативным требованиям
        
        Args:
            storage_type: Тип хранилища ("json" или "sqlite")
            path: Путь к файлу или директории с данными о соответствии
            kb_path: Путь к основной базе знаний (для связи с продуктами)
        """
        self.storage_type = storage_type.lower()
        
        # Определение путей по умолчанию
        if path is None:
            if self.storage_type == "json":
                self.path = "compliance_data.json"
            else:
                self.path = "compliance_data.db"
        else:
            self.path = path
        
        self.kb_path = kb_path
        self.db = None
        self.data = None
        
        if self.storage_type == "json":
            self._load_json()
        elif self.storage_type == "sqlite":
            self._connect_sqlite()
        else:
            raise ValueError(f"Неподдерживаемый тип хранилища: {storage_type}. Используйте 'json' или 'sqlite'.")
    
    def _load_json(self):
        """Загрузка данных о соответствии из JSON-файла"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"Данные о соответствии успешно загружены из {self.path}")
        except FileNotFoundError:
            print(f"Файл не найден: {self.path}. Создаётся новая структура данных.")
            self.data = {
                "compliance_documents": [],
                "compliance_requirements": [],
                "compliance_controls": [],
                "requirement_control_mapping": [],
                "product_compliance_mapping": [],
                "compliance_reports": [],
                "compliance_gaps": []
            }
            self._save_json()
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка формата JSON в файле {self.path}")
    
    def _save_json(self):
        """Сохранение данных о соответствии в JSON-файл"""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)) if os.path.dirname(self.path) else '.', exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Данные о соответствии сохранены в {self.path}")
    
    def _connect_sqlite(self):
        """Подключение к базе данных SQLite"""
        try:
            self.db = sqlite3.connect(self.path)
            self.db.row_factory = sqlite3.Row
            print(f"Подключение к базе данных SQLite установлено: {self.path}")
            
            # Проверка наличия необходимых таблиц
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compliance_documents'")
            if not cursor.fetchone():
                print("Создание структуры базы данных...")
                self._create_sqlite_schema()
        except sqlite3.Error as e:
            raise ConnectionError(f"Ошибка подключения к SQLite базе данных: {e}")
    
    def _create_sqlite_schema(self):
        """Создание схемы базы данных SQLite"""
        schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_compliance.sql')
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as schema_file:
                schema = schema_file.read()
                
            self.db.executescript(schema)
            self.db.commit()
            print("Структура базы данных успешно создана")
        except sqlite3.Error as e:
            self.db.rollback()
            raise Exception(f"Ошибка создания структуры базы данных: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл схемы не найден: {schema_path}")
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.storage_type == "sqlite" and self.db:
            self.db.close()
            print("Соединение с базой данных закрыто")
            
    # Методы для работы с нормативными документами
    
    def get_compliance_documents(self) -> List[Dict[str, Any]]:
        """Получение списка всех нормативных документов"""
        if self.storage_type == "json":
            return self.data.get("compliance_documents", [])
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM compliance_documents ORDER BY code")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_compliance_document(self, document_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о нормативном документе по ID
        
        Args:
            document_id: Идентификатор документа
            
        Returns:
            Словарь с информацией о документе или None, если документ не найден
        """
        if self.storage_type == "json":
            for document in self.data.get("compliance_documents", []):
                if document.get("id") == document_id:
                    return document
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM compliance_documents WHERE id = ?", (document_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    
    def get_compliance_document_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о нормативном документе по коду
        
        Args:
            code: Код документа (например, "GDPR", "152-ФЗ")
            
        Returns:
            Словарь с информацией о документе или None, если документ не найден
        """
        if self.storage_type == "json":
            for document in self.data.get("compliance_documents", []):
                if document.get("code") == code:
                    return document
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM compliance_documents WHERE code = ?", (code,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    
    def add_compliance_document(self, document_data: Dict[str, Any]) -> int:
        """
        Добавление нового нормативного документа
        
        Args:
            document_data: Данные о документе
            
        Returns:
            ID добавленного документа
        """
        # Проверка обязательных полей
        if not document_data.get("code") or not document_data.get("name"):
            raise ValueError("Код и название документа обязательны")
        
        if self.storage_type == "json":
            # Генерация ID
            documents = self.data.get("compliance_documents", [])
            if not documents:
                new_id = 1
            else:
                new_id = max(doc.get("id", 0) for doc in documents) + 1
            
            # Добавление ID в данные
            document_data["id"] = new_id
            
            # Добавление документа
            documents.append(document_data)
            self.data["compliance_documents"] = documents
            
            self._save_json()
            return new_id
        else:
            cursor = self.db.cursor()
            
            # Подготовка данных и полей для запроса
            fields = []
            values = []
            placeholders = []
            
            for key, value in document_data.items():
                if key != "id":  # ID будет сгенерирован автоматически
                    fields.append(key)
                    values.append(value)
                    placeholders.append("?")
            
            # Формирование SQL-запроса
            query = f"""
            INSERT INTO compliance_documents ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            """
            
            try:
                cursor.execute(query, values)
                
                # Получение ID добавленного документа
                cursor.execute("SELECT last_insert_rowid()")
                new_id = cursor.fetchone()[0]
                
                # Добавление в индекс поиска
                cursor.execute(
                    """
                    INSERT INTO compliance_search_index 
                    (content, document_code, document_name, requirement_code, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_data.get("description", "") + " " + document_data.get("scope", ""),
                        document_data.get("code", ""),
                        document_data.get("name", ""),
                        "",
                        "document",
                        new_id
                    )
                )
                
                self.db.commit()
                return new_id
            except Exception as e:
                self.db.rollback()
                raise e
    
    def update_compliance_document(self, document_id: int, document_data: Dict[str, Any]) -> bool:
        """
        Обновление информации о нормативном документе
        
        Args:
            document_id: Идентификатор документа
            document_data: Новые данные о документе
            
        Returns:
            True, если обновление выполнено успешно, иначе False
        """
        if self.storage_type == "json":
            documents = self.data.get("compliance_documents", [])
            for i, document in enumerate(documents):
                if document.get("id") == document_id:
                    # Сохраняем ID
                    document_data["id"] = document_id
                    
                    # Обновляем документ
                    documents[i] = document_data
                    self.data["compliance_documents"] = documents
                    
                    self._save_json()
                    return True
            return False
        else:
            cursor = self.db.cursor()
            
            # Подготовка данных и полей для запроса
            set_clauses = []
            values = []
            
            for key, value in document_data.items():
                if key != "id":  # ID не обновляем
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            # Добавляем ID для условия WHERE
            values.append(document_id)
            
            # Формирование SQL-запроса
            query = f"""
            UPDATE compliance_documents
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            try:
                cursor.execute(query, values)
                
                # Обновление индекса поиска
                cursor.execute("DELETE FROM compliance_search_index WHERE entity_type = 'document' AND entity_id = ?", (document_id,))
                cursor.execute(
                    """
                    INSERT INTO compliance_search_index 
                    (content, document_code, document_name, requirement_code, entity_type, entity_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_data.get("description", "") + " " + document_data.get("scope", ""),
                        document_data.get("code", ""),
                        document_data.get("name", ""),
                        "",
                        "document",
                        document_id
                    )
                )
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    def delete_compliance_document(self, document_id: int) -> bool:
        """
        Удаление нормативного документа
        
        Args:
            document_id: Идентификатор документа
            
        Returns:
            True, если удаление выполнено успешно, иначе False
        """
        if self.storage_type == "json":
            documents = self.data.get("compliance_documents", [])
            requirements = self.data.get("compliance_requirements", [])
            
            # Удаляем зависимые требования
            requirements = [req for req in requirements if req.get("document_id") != document_id]
            self.data["compliance_requirements"] = requirements
            
            # Удаляем документ
            documents = [doc for doc in documents if doc.get("id") != document_id]
            self.data["compliance_documents"] = documents
            
            self._save_json()
            return True
        else:
            cursor = self.db.cursor()
            
            try:
                # Удаление из индекса поиска
                cursor.execute("DELETE FROM compliance_search_index WHERE entity_type = 'document' AND entity_id = ?", (document_id,))
                
                # Удаление документа (зависимые записи удалятся автоматически из-за каскадного удаления)
                cursor.execute("DELETE FROM compliance_documents WHERE id = ?", (document_id,))
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    # Методы для работы с контрольными мерами
    
    def get_compliance_controls(self) -> List[Dict[str, Any]]:
        """Получение списка всех контрольных мер"""
        if self.storage_type == "json":
            return self.data.get("compliance_controls", [])
        else:
            cursor = self
    
    # Методы для работы с контрольными мерами
    
    def get_compliance_controls(self) -> List[Dict[str, Any]]:
        """Получение списка всех контрольных мер"""
        if self.storage_type == "json":
            return self.data.get("compliance_controls", [])
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM compliance_controls ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def get_compliance_control(self, control_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о контрольной мере по ID
        
        Args:
            control_id: Идентификатор контрольной меры
            
        Returns:
            Словарь с информацией о контрольной мере или None, если не найдена
        """
        if self.storage_type == "json":
            for control in self.data.get("compliance_controls", []):
                if control.get("id") == control_id:
                    return control
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM compliance_controls WHERE id = ?", (control_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    
    def add_compliance_control(self, control_data: Dict[str, Any]) -> int:
        """
        Добавление новой контрольной меры
        
        Args:
            control_data: Данные о контрольной мере
            
        Returns:
            ID добавленной контрольной меры
        """
        # Проверка обязательных полей
        if not control_data.get("name"):
            raise ValueError("Название контрольной меры обязательно")
        
        if self.storage_type == "json":
            # Генерация ID
            controls = self.data.get("compliance_controls", [])
            if not controls:
                new_id = 1
            else:
                new_id = max(control.get("id", 0) for control in controls) + 1
            
            # Добавление ID в данные
            control_data["id"] = new_id
            
            # Добавление контрольной меры
            controls.append(control_data)
            self.data["compliance_controls"] = controls
            
            self._save_json()
            return new_id
        else:
            cursor = self.db.cursor()
            
            # Подготовка данных и полей для запроса
            fields = []
            values = []
            placeholders = []
            
            for key, value in control_data.items():
                if key != "id":  # ID будет сгенерирован автоматически
                    fields.append(key)
                    values.append(value)
                    placeholders.append("?")
            
            # Формирование SQL-запроса
            query = f"""
            INSERT INTO compliance_controls ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            """
            
            try:
                cursor.execute(query, values)
                
                # Получение ID добавленной контрольной меры
                cursor.execute("SELECT last_insert_rowid()")
                new_id = cursor.fetchone()[0]
                
                self.db.commit()
                return new_id
            except Exception as e:
                self.db.rollback()
                raise e
    
    def update_compliance_control(self, control_id: int, control_data: Dict[str, Any]) -> bool:
        """
        Обновление информации о контрольной мере
        
        Args:
            control_id: Идентификатор контрольной меры
            control_data: Новые данные о контрольной мере
            
        Returns:
            True, если обновление выполнено успешно, иначе False
        """
        if self.storage_type == "json":
            controls = self.data.get("compliance_controls", [])
            for i, control in enumerate(controls):
                if control.get("id") == control_id:
                    # Сохраняем ID
                    control_data["id"] = control_id
                    
                    # Обновляем контрольную меру
                    controls[i] = control_data
                    self.data["compliance_controls"] = controls
                    
                    self._save_json()
                    return True
            return False
        else:
            cursor = self.db.cursor()
            
            # Подготовка данных и полей для запроса
            set_clauses = []
            values = []
            
            for key, value in control_data.items():
                if key != "id":  # ID не обновляем
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            # Добавляем ID для условия WHERE
            values.append(control_id)
            
            # Формирование SQL-запроса
            query = f"""
            UPDATE compliance_controls
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            try:
                cursor.execute(query, values)
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    def delete_compliance_control(self, control_id: int) -> bool:
        """
        Удаление контрольной меры
        
        Args:
            control_id: Идентификатор контрольной меры
            
        Returns:
            True, если удаление выполнено успешно, иначе False
        """
        if self.storage_type == "json":
            controls = self.data.get("compliance_controls", [])
            mappings = self.data.get("requirement_control_mapping", [])
            product_mappings = self.data.get("product_compliance_mapping", [])
            
            # Удаляем связи с требованиями
            mappings = [m for m in mappings if m.get("control_id") != control_id]
            self.data["requirement_control_mapping"] = mappings
            
            # Удаляем связи с продуктами
            product_mappings = [m for m in product_mappings if m.get("control_id") != control_id]
            self.data["product_compliance_mapping"] = product_mappings
            
            # Удаляем контрольную меру
            controls = [control for control in controls if control.get("id") != control_id]
            self.data["compliance_controls"] = controls
            
            self._save_json()
            return True
        else:
            cursor = self.db.cursor()
            
            try:
                # Удаление контрольной меры (зависимые записи удалятся автоматически из-за каскадного удаления)
                cursor.execute("DELETE FROM compliance_controls WHERE id = ?", (control_id,))
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    # Методы для работы со связями между требованиями и контрольными мерами
    
    def link_requirement_to_control(self, requirement_id: int, control_id: int) -> bool:
        """
        Связывание требования с контрольной мерой
        
        Args:
            requirement_id: Идентификатор требования
            control_id: Идентификатор контрольной меры
            
        Returns:
            True, если связь создана успешно, иначе False
        """
        # Проверяем существование требования и контрольной меры
        requirement = self.get_compliance_requirement(requirement_id)
        control = self.get_compliance_control(control_id)
        
        if not requirement:
            raise ValueError(f"Требование с ID {requirement_id} не найдено")
        
        if not control:
            raise ValueError(f"Контрольная мера с ID {control_id} не найдена")
        
        if self.storage_type == "json":
            mappings = self.data.get("requirement_control_mapping", [])
            
            # Проверяем, нет ли уже такой связи
            for mapping in mappings:
                if mapping.get("requirement_id") == requirement_id and mapping.get("control_id") == control_id:
                    return True  # Связь уже существует
            
            # Добавляем новую связь
            mappings.append({
                "requirement_id": requirement_id,
                "control_id": control_id
            })
            
            self.data["requirement_control_mapping"] = mappings
            self._save_json()
            return True
        else:
            cursor = self.db.cursor()
            
            # Проверяем, нет ли уже такой связи
            cursor.execute(
                "SELECT 1 FROM requirement_control_mapping WHERE requirement_id = ? AND control_id = ?",
                (requirement_id, control_id)
            )
            
            if cursor.fetchone():
                return True  # Связь уже существует
            
            try:
                # Добавляем новую связь
                cursor.execute(
                    "INSERT INTO requirement_control_mapping (requirement_id, control_id) VALUES (?, ?)",
                    (requirement_id, control_id)
                )
                
                self.db.commit()
                return True
            except Exception as e:
                self.db.rollback()
                raise e
    
    def unlink_requirement_from_control(self, requirement_id: int, control_id: int) -> bool:
        """
        Удаление связи между требованием и контрольной мерой
        
        Args:
            requirement_id: Идентификатор требования
            control_id: Идентификатор контрольной меры
            
        Returns:
            True, если связь удалена успешно, иначе False
        """
        if self.storage_type == "json":
            mappings = self.data.get("requirement_control_mapping", [])
            
            # Удаляем связь
            new_mappings = [
                m for m in mappings 
                if not (m.get("requirement_id") == requirement_id and m.get("control_id") == control_id)
            ]
            
            if len(new_mappings) < len(mappings):
                self.data["requirement_control_mapping"] = new_mappings
                self._save_json()
                return True
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                cursor.execute(
                    "DELETE FROM requirement_control_mapping WHERE requirement_id = ? AND control_id = ?",
                    (requirement_id, control_id)
                )
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    def get_controls_for_requirement(self, requirement_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка контрольных мер, связанных с требованием
        
        Args:
            requirement_id: Идентификатор требования
            
        Returns:
            Список контрольных мер
        """
        if self.storage_type == "json":
            mappings = self.data.get("requirement_control_mapping", [])
            controls = self.data.get("compliance_controls", [])
            
            # Находим все ID контрольных мер, связанных с требованием
            control_ids = [m.get("control_id") for m in mappings if m.get("requirement_id") == requirement_id]
            
            # Возвращаем данные о контрольных мерах
            return [control for control in controls if control.get("id") in control_ids]
        else:
            cursor = self.db.cursor()
            
            cursor.execute("""
                SELECT c.* FROM compliance_controls c
                JOIN requirement_control_mapping m ON c.id = m.control_id
                WHERE m.requirement_id = ?
                ORDER BY c.name
            """, (requirement_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_requirements_for_control(self, control_id: int) -> List[Dict[str, Any]]:
        """
        Получение списка требований, связанных с контрольной мерой
        
        Args:
            control_id: Идентификатор контрольной меры
            
        Returns:
            Список требований
        """
        if self.storage_type == "json":
            mappings = self.data.get("requirement_control_mapping", [])
            requirements = self.data.get("compliance_requirements", [])
            
            # Находим все ID требований, связанных с контрольной мерой
            requirement_ids = [m.get("requirement_id") for m in mappings if m.get("control_id") == control_id]
            
            # Возвращаем данные о требованиях
            return [req for req in requirements if req.get("id") in requirement_ids]
        else:
            cursor = self.db.cursor()
            
            cursor.execute("""
                SELECT r.* FROM compliance_requirements r
                JOIN requirement_control_mapping m ON r.id = m.requirement_id
                WHERE m.control_id = ?
                ORDER BY r.document_id, r.code
            """, (control_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Методы для работы с несоответствиями (gaps)
    
    def get_compliance_gaps(self, requirement_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получение списка несоответствий
        
        Args:
            requirement_id: Опциональный фильтр по ID требования
            
        Returns:
            Список несоответствий
        """
        if self.storage_type == "json":
            gaps = self.data.get("compliance_gaps", [])
            if requirement_id is not None:
                gaps = [gap for gap in gaps if gap.get("requirement_id") == requirement_id]
            return gaps
        else:
            cursor = self.db.cursor()
            
            if requirement_id is not None:
                cursor.execute("SELECT * FROM compliance_gaps WHERE requirement_id = ? ORDER BY due_date", (requirement_id,))
            else:
                cursor.execute("SELECT * FROM compliance_gaps ORDER BY due_date")
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_compliance_gap(self, gap_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о несоответствии по ID
        
        Args:
            gap_id: Идентификатор несоответствия
            
        Returns:
            Словарь с информацией о несоответствии или None, если не найдено
        """
        if self.storage_type == "json":
            for gap in self.data.get("compliance_gaps", []):
                if gap.get("id") == gap_id:
                    return gap
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM compliance_gaps WHERE id = ?", (gap_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    
    def add_compliance_gap(self, gap_data: Dict[str, Any]) -> int:
        """
        Добавление нового несоответствия
        
        Args:
            gap_data: Данные о несоответствии
            
        Returns:
            ID добавленного несоответствия
        """
        # Проверка обязательных полей
        if not gap_data.get("requirement_id") or not gap_data.get("description"):
            raise ValueError("ID требования и описание несоответствия обязательны")
        
        # Проверяем существование требования
        requirement = self.get_compliance_requirement(gap_data.get("requirement_id"))
        if not requirement:
            raise ValueError(f"Требование с ID {gap_data.get('requirement_id')} не найдено")
        
        if self.storage_type == "json":
            # Генерация ID
            gaps = self.data.get("compliance_gaps", [])
            if not gaps:
                new_id = 1
            else:
                new_id = max(gap.get("id", 0) for gap in gaps) + 1
            
            # Добавление ID в данные
            gap_data["id"] = new_id
            
            # Добавление несоответствия
            gaps.append(gap_data)
            self.data["compliance_gaps"] = gaps
            
            self._save_json()
            return new_id
        else:
            cursor = self.db.cursor()
            
            # Подготовка данных и полей для запроса
            fields = []
            values = []
            placeholders = []
            
            for key, value in gap_data.items():
                if key != "id":  # ID будет сгенерирован автоматически
                    fields.append(key)
                    values.append(value)
                    placeholders.append("?")
            
            # Формирование SQL-запроса
            query = f"""
            INSERT INTO compliance_gaps ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            """
            
            try:
                cursor.execute(query, values)
                
                # Получение ID добавленного несоответствия
                cursor.execute("SELECT last_insert_rowid()")
                new_id = cursor.fetchone()[0]
                
                self.db.commit()
                return new_id
            except Exception as e:
                self.db.rollback()
                raise e
    
    def update_compliance_gap(self, gap_id: int, gap_data: Dict[str, Any]) -> bool:
        """
        Обновление информации о несоответствии
        
        Args:
            gap_id: Идентификатор несоответствия
            gap_data: Новые данные о несоответствии
            
        Returns:
            True, если обновление выполнено успешно, иначе False
        """
        if self.storage_type == "json":
            gaps = self.data.get("compliance_gaps", [])
            for i, gap in enumerate(gaps):
                if gap.get("id") == gap_id:
                    # Сохраняем ID
                    gap_data["id"] = gap_id
                    
                    # Обновляем несоответствие
                    gaps[i] = gap_data
                    self.data["compliance_gaps"] = gaps
                    
                    self._save_json()
                    return True
            return False
        else:
            cursor = self.db.cursor()
            
            # Подготовка данных и полей для запроса
            set_clauses = []
            values = []
            
            for key, value in gap_data.items():
                if key != "id":  # ID не обновляем
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            # Добавляем ID для условия WHERE
            values.append(gap_id)
            
            # Формирование SQL-запроса
            query = f"""
            UPDATE compliance_gaps
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            try:
                cursor.execute(query, values)
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
    
    def delete_compliance_gap(self, gap_id: int) -> bool:
        """
        Удаление несоответствия
        
        Args:
            gap_id: Идентификатор несоответствия
            
        Returns:
            True, если удаление выполнено успешно, иначе False
        """
        if self.storage_type == "json":
            gaps = self.data.get("compliance_gaps", [])
            
            # Удаляем несоответствие
            new_gaps = [gap for gap in gaps if gap.get("id") != gap_id]
            
            if len(new_gaps) < len(gaps):
                self.data["compliance_gaps"] = new_gaps
                self._save_json()
                return True
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                cursor.execute("DELETE FROM compliance_gaps WHERE id = ?", (gap_id,))
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                raise e
