#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для работы с базой данных обучения персонала по кибербезопасности
Поддерживает форматы JSON и SQLite
"""

import json
import sqlite3
import os
import re
import datetime
from typing import List, Dict, Any, Optional, Union, Tuple


class TrainingAccessor:
    """Класс для доступа к данным обучения персонала"""
    
    def __init__(self, storage_type: str = "json", path: str = "./training_data"):
        """
        Инициализация доступа к данным обучения
        
        Args:
            storage_type: Тип хранилища ("json" или "sqlite")
            path: Путь к файлу или директории с данными обучения
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
        """Загрузка данных обучения из JSON-файла"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"Данные обучения успешно загружены из {self.path}")
        except FileNotFoundError:
            print(f"Файл не найден: {self.path}. Создаётся новая база данных обучения.")
            self.data = {
                "training_info": {
                    "title": "База данных обучения персонала по кибербезопасности",
                    "version": "1.0",
                    "last_updated": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "description": "Обучающие материалы для сотрудников"
                },
                "categories": [],
                "difficulty_levels": [
                    {"id": 1, "name": "Начальный", "description": "Для новичков без опыта в кибербезопасности"},
                    {"id": 2, "name": "Базовый", "description": "Основы кибербезопасности"},
                    {"id": 3, "name": "Средний", "description": "Для сотрудников с базовыми знаниями"},
                    {"id": 4, "name": "Продвинутый", "description": "Для специалистов по безопасности"},
                    {"id": 5, "name": "Эксперт", "description": "Для экспертов в области кибербезопасности"}
                ],
                "roles": [],
                "courses": [],
                "employees": []
            }
            self._save_json()
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка формата JSON в файле {self.path}")
    
    def _save_json(self):
        """Сохранение данных обучения в JSON-файл"""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Данные обучения сохранены в {self.path}")
    
    def _connect_sqlite(self):
        """Подключение к базе данных SQLite"""
        try:
            self.db = sqlite3.connect(self.path)
            self.db.row_factory = sqlite3.Row
            print(f"Подключение к базе данных SQLite установлено: {self.path}")
            
            # Проверка наличия необходимых таблиц
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_courses'")
            if not cursor.fetchone():
                print("Создание структуры базы данных обучения...")
                self._create_sqlite_schema()
        except sqlite3.Error as e:
            raise ConnectionError(f"Ошибка подключения к SQLite базе данных: {e}")
    
    def _create_sqlite_schema(self):
        """Создание схемы базы данных SQLite для обучения"""
        with open('modules/training/schema_training.sql', 'r', encoding='utf-8') as schema_file:
            schema = schema_file.read()
            
        try:
            self.db.executescript(schema)
            
            # Добавляем базовые уровни сложности
            self._initialize_basic_data()
            
            self.db.commit()
            print("Структура базы данных обучения успешно создана")
        except sqlite3.Error as e:
            self.db.rollback()
            raise Exception(f"Ошибка создания структуры базы данных: {e}")
    
    def _initialize_basic_data(self):
        """Инициализация базовых данных для SQLite (уровни сложности, типы материалов)"""
        cursor = self.db.cursor()
        
        # Добавляем уровни сложности
        difficulty_levels = [
            (1, "Начальный", "Для новичков без опыта в кибербезопасности"),
            (2, "Базовый", "Основы кибербезопасности"),
            (3, "Средний", "Для сотрудников с базовыми знаниями"),
            (4, "Продвинутый", "Для специалистов по безопасности"),
            (5, "Эксперт", "Для экспертов в области кибербезопасности")
        ]
        
        cursor.executemany(
            "INSERT INTO training_difficulty_levels (id, name, description) VALUES (?, ?, ?)",
            difficulty_levels
        )
        
        # Добавляем типы материалов
        material_types = [
            (1, "Текст", "Текстовые материалы и статьи"),
            (2, "Видео", "Видеоуроки и презентации"),
            (3, "Интерактив", "Интерактивные материалы и симуляции"),
            (4, "Практика", "Практические задания и лабораторные работы"),
            (5, "Внешний ресурс", "Ссылки на внешние ресурсы")
        ]
        
        cursor.executemany(
            "INSERT INTO material_types (id, name, description) VALUES (?, ?, ?)",
            material_types
        )
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.storage_type == "sqlite" and self.db:
            self.db.close()
            print("Соединение с базой данных закрыто")
    
    # ===========================================================================
    # Методы для работы с категориями обучения
    # ===========================================================================
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Получение списка всех категорий обучения
        
        Returns:
            Список категорий с их атрибутами
        """
        if self.storage_type == "json":
            return self.data.get("categories", [])
        else:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT id, name, description, parent_id, order_index FROM training_categories ORDER BY order_index"
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_category(self, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации о категории по ID
        
        Args:
            category_id: Идентификатор категории
            
        Returns:
            Словарь с информацией о категории или None, если категория не найдена
        """
        if self.storage_type == "json":
            for category in self.data.get("categories", []):
                if category.get("id") == category_id:
                    return category
            return None
        else:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT id, name, description, parent_id, order_index FROM training_categories WHERE id = ?",
                (category_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    
   def add_category(self, category_data: Dict[str, Any]) -> int:
       """
       Добавление новой категории обучения
       
       Args:
           category_data: Данные о категории (name, description, parent_id, order_index)
           
       Returns:
           ID добавленной категории
       """
       name = category_data.get("name")
       if not name:
           raise ValueError("Название категории обязательно")
       
       description = category_data.get("description", "")
       parent_id = category_data.get("parent_id")
       order_index = category_data.get("order_index")
       
       if self.storage_type == "json":
           categories = self.data.get("categories", [])
           
           # Генерируем новый ID
           new_id = 1
           if categories:
               new_id = max(cat.get("id", 0) for cat in categories) + 1
           
           # Создаем новую категорию
           new_category = {
               "id": new_id,
               "name": name,
               "description": description
           }
           
           if parent_id is not None:
               new_category["parent_id"] = parent_id
           
           if order_index is not None:
               new_category["order_index"] = order_index
           
           # Добавляем в список категорий
           categories.append(new_category)
           self.data["categories"] = categories
           self._save_json()
           
           return new_id
       else:
           cursor = self.db.cursor()
           
           try:
               cursor.execute(
                   """
                   INSERT INTO training_categories (name, description, parent_id, order_index)
                   VALUES (?, ?, ?, ?)
                   """,
                   (name, description, parent_id, order_index)
               )
               
               # Получаем ID добавленной категории
               cursor.execute("SELECT last_insert_rowid()")
               category_id = cursor.fetchone()[0]
               
               self.db.commit()
               return category_id
           except Exception as e:
               self.db.rollback()
               raise e
   
   def update_category(self, category_id: int, category_data: Dict[str, Any]) -> bool:
       """
       Обновление информации о категории
       
       Args:
           category_id: ID категории
           category_data: Обновленные данные о категории
           
       Returns:
           True в случае успешного обновления, иначе False
       """
       if self.storage_type == "json":
           for i, category in enumerate(self.data.get("categories", [])):
               if category.get("id") == category_id:
                   # Обновляем данные
                   self.data["categories"][i].update(category_data)
                   self._save_json()
                   return True
           return False
       else:
           cursor = self.db.cursor()
           
           # Формируем запрос на обновление только тех полей, которые переданы
           fields = []
           params = []
           
           for key, value in category_data.items():
               if key in ["name", "description", "parent_id", "order_index"]:
                   fields.append(f"{key} = ?")
                   params.append(value)
           
           if not fields:
               return False
           
           # Добавляем ID в конец списка параметров
           params.append(category_id)
           
           try:
               cursor.execute(
                   f"UPDATE training_categories SET {', '.join(fields)} WHERE id = ?",
                   params
               )
               
               self.db.commit()
               return cursor.rowcount > 0
           except Exception as e:
               self.db.rollback()
               raise e
   
   def delete_category(self, category_id: int) -> bool:
       """
       Удаление категории по ID
       
       Args:
           category_id: Идентификатор категории
           
       Returns:
           True, если категория успешно удалена, иначе False
       """
       if self.storage_type == "json":
           for i, category in enumerate(self.data.get("categories", [])):
               if category.get("id") == category_id:
                   self.data["categories"].pop(i)
                   
                   # Обновляем parent_id для дочерних категорий
                   for child in self.data["categories"]:
                       if child.get("parent_id") == category_id:
                           child["parent_id"] = None
                   
                   self._save_json()
                   return True
           return False
       else:
           cursor = self.db.cursor()
           
           try:
               # Обновляем parent_id для дочерних категорий
               cursor.execute(
                   "UPDATE training_categories SET parent_id = NULL WHERE parent_id = ?",
                   (category_id,)
               )
               
               # Удаляем категорию
               cursor.execute("DELETE FROM training_categories WHERE id = ?", (category_id,))
               
               self.db.commit()
               return cursor.rowcount > 0
           except Exception as e:
               self.db.rollback()
               raise e
   
   # ===========================================================================
   # Методы для работы с курсами
   # ===========================================================================
   
   def get_courses(self, category_id: Optional[int] = None, role_id: Optional[int] = None) -> List[Dict[str, Any]]:
       """
       Получение списка всех курсов, опционально фильтрация по категории или роли
       
       Args:
           category_id: ID категории для фильтрации (опционально)
           role_id: ID роли для фильтрации (опционально)
           
       Returns:
           Список курсов с их атрибутами
       """
       if self.storage_type == "json":
           courses = self.data.get("courses", [])
           
           # Фильтрация по категории
           if category_id is not None:
               courses = [course for course in courses if course.get("category_id") == category_id]
           
           # Фильтрация по роли
           if role_id is not None:
               courses = [
                   course for course in courses 
                   if any(role == role_id for role in course.get("target_roles", []))
               ]
           
           return courses
       else:
           cursor = self.db.cursor()
           
           query = """
               SELECT c.* FROM training_courses c
           """
           
           params = []
           
           # Фильтрация по роли
           if role_id is not None:
               query += """
                   JOIN course_target_roles r ON c.id = r.course_id
                   WHERE r.role_id = ?
               """
               params.append(role_id)
               
               # Если есть и категория, добавляем AND
               if category_id is not None:
                   query += " AND c.category_id = ?"
                   params.append(category_id)
           elif category_id is not None:
               # Если только категория
               query += " WHERE c.category_id = ?"
               params.append(category_id)
           
           cursor.execute(query, params)
           
           courses = []
           for row in cursor.fetchall():
               course_data = dict(row)
               
               # Получаем целевые роли
               cursor.execute(
                   "SELECT role_id FROM course_target_roles WHERE course_id = ?",
                   (course_data["id"],)
               )
               course_data["target_roles"] = [r["role_id"] for r in cursor.fetchall()]
               
               courses.append(course_data)
           
           return courses
   
   def get_course(self, course_id: int) -> Optional[Dict[str, Any]]:
       """
       Получение информации о курсе по ID
       
       Args:
           course_id: Идентификатор курса
           
       Returns:
           Словарь с информацией о курсе или None, если курс не найден
       """
       if self.storage_type == "json":
           for course in self.data.get("courses", []):
               if course.get("id") == course_id:
                   return course
           return None
       else:
           cursor = self.db.cursor()
           cursor.execute(
               "SELECT * FROM training_courses WHERE id = ?",
               (course_id,)
           )
           result = cursor.fetchone()
           
           if not result:
               return None
               
           course_data = dict(result)
           
           # Получаем целевые роли
           cursor.execute(
               "SELECT role_id FROM course_target_roles WHERE course_id = ?",
               (course_id,)
           )
           course_data["target_roles"] = [row["role_id"] for row in cursor.fetchall()]
           
           # Получаем связанные продукты
           cursor.execute(
               "SELECT product_id FROM course_products WHERE course_id = ?",
               (course_id,)
           )
           course_data["related_products"] = [row["product_id"] for row in cursor.fetchall()]
           
           # Получаем модули курса
           cursor.execute(
               "SELECT * FROM training_modules WHERE course_id = ? ORDER BY order_index",
               (course_id,)
           )
           course_data["modules"] = [dict(row) for row in cursor.fetchall()]
           
           return course_data
   
   def add_course(self, course_data: Dict[str, Any]) -> int:
       """
       Добавление нового курса
       
       Args:
           course_data: Данные о курсе (title, description, category_id, ...)
           
       Returns:
           ID добавленного курса
       """
       title = course_data.get("title")
       if not title:
           raise ValueError("Название курса обязательно")
       
       description = course_data.get("description", "")
       category_id = course_data.get("category_id")
       difficulty_level_id = course_data.get("difficulty_level_id")
       duration_minutes = course_data.get("duration_minutes")
       is_required = course_data.get("is_required", False)
       is_certification = course_data.get("is_certification", False)
       certification_validity_days = course_data.get("certification_validity_days")
       version = course_data.get("version", "1.0")
       author = course_data.get("author", "")
       
       target_roles = course_data.get("target_roles", [])
       related_products = course_data.get("related_products", [])
       
       # Текущая дата для создания/обновления
       current_date = datetime.datetime.now().strftime("%Y-%m-%d")
       
       if self.storage_type == "json":
           courses = self.data.get("courses", [])
           
           # Генерируем новый ID
           new_id = 1
           if courses:
               new_id = max(course.get("id", 0) for course in courses) + 1
           
           # Создаем новый курс
           new_course = {
               "id": new_id,
               "title": title,
               "description": description,
               "category_id": category_id,
               "difficulty_level_id": difficulty_level_id,
               "duration_minutes": duration_minutes,
               "is_required": is_required,
               "is_certification": is_certification,
               "certification_validity_days": certification_validity_days,
               "creation_date": current_date,
               "last_updated": current_date,
               "version": version,
               "author": author,
               "target_roles": target_roles,
               "related_products": related_products,
               "modules": []
           }
           
           # Добавляем в список курсов
           courses.append(new_course)
           self.data["courses"] = courses
           self._save_json()
           
           return new_id
       else:
           cursor = self.db.cursor()
           
           try:
               cursor.execute(
                   """
                   INSERT INTO training_courses (
                       title, description, category_id, difficulty_level_id, 
                       duration_minutes, is_required, is_certification, 
                       certification_validity_days, creation_date, last_updated, 
                       version, author
                   )
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   """,
                   (
                       title, description, category_id, difficulty_level_id,
                       duration_minutes, is_required, is_certification,
                       certification_validity_days, current_date, current_date,
                       version, author
                   )
               )
               
               # Получаем ID добавленного курса
               cursor.execute("SELECT last_insert_rowid()")
               course_id = cursor.fetchone()[0]
               
               # Добавляем целевые роли
               for role_id in target_roles:
                   cursor.execute(
                       "INSERT INTO course_target_roles (course_id, role_id) VALUES (?, ?)",
                       (course_id, role_id)
                   )
               
               # Добавляем связанные продукты
               for product_id in related_products:
                   cursor.execute(
                       "INSERT INTO course_products (course_id, product_id) VALUES (?, ?)",
                       (course_id, product_id)
                   )
               
               # Добавляем в поисковый индекс
               cursor.execute(
                   """
                   INSERT INTO training_search_index 
                   (content, category, title, entity_type, entity_id)
                   VALUES (?, ?, ?, ?, ?)
                   """,
                   (
                       title + " " + description,
                       str(category_id),
                       title,
                       "course",
                       course_id
                   )
               )
               
               self.db.commit()
               return course_id
           except Exception as e:
               self.db.rollback()
               raise e
               
   def search_training(self, query: str) -> List[Dict[str, Any]]:
       """
       Поиск по обучающим материалам
       
       Args:
           query: Поисковый запрос
           
       Returns:
           Список найденных элементов
       """
       if self.storage_type == "json":
           results = []
           query_lower = query.lower()
           
           # Поиск по курсам
           for course in self.data.get("courses", []):
               course_text = json.dumps(course, ensure_ascii=False).lower()
               if query_lower in course_text:
                   results.append({
                       "type": "course",
                       "id": course.get("id"),
                       "title": course.get("title", ""),
                       "content": course.get("description", "")
                   })
               
               # Поиск по модулям
               for module in course.get("modules", []):
                   module_text = json.dumps(module, ensure_ascii=False).lower()
                   if query_lower in module_text:
                       results.append({
                           "type": "module",
                           "id": module.get("id"),
                           "course_id": course.get("id"),
                           "title": module.get("title", ""),
                           "content": module.get("description", "")
                       })
                   
                   # Поиск по материалам
                   for material in module.get("materials", []):
                       material_text = json.dumps(material, ensure_ascii=False).lower()
                       if query_lower in material_text:
                           results.append({
                               "type": "material",
                               "id": material.get("id"),
                               "module_id": module.get("id"),
                               "course_id": course.get("id"),
                               "title": material.get("title", ""),
                               "content": material.get("description", "")
                           })
                   
                   # Поиск по тестам
                   for test in module.get("tests", []):
                       test_text = json.dumps(test, ensure_ascii=False).lower()
                       if query_lower in test_text:
                           results.append({
                               "type": "test",
                               "id": test.get("id"),
                               "module_id": module.get("id"),
                               "course_id": course.get("id"),
                               "title": test.get("title", ""),
                               "content": test.get("description", "")
                           })
           
           return results
       else:
           cursor = self.db.cursor()
           
           # Подготовка запроса для полнотекстового поиска
           query = ' '.join(f'"{word}"' for word in re.findall(r'\w+', query))
           
           cursor.execute(
               """
               SELECT * FROM training_search_index
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
               
               if entity_type == "course":
                   cursor.execute("SELECT title, description FROM training_courses WHERE id = ?", (entity_id,))
                   data = cursor.fetchone()
                   if data:
                       result_data["title"] = data["title"]
                       result_data["content"] = data["description"]
               
               elif entity_type == "module":
                   cursor.execute("SELECT title, description, course_id FROM training_modules WHERE id = ?", (entity_id,))
                   data = cursor.fetchone()
                   if data:
                       result_data["title"] = data["title"]
                       result_data["content"] = data["description"]
                       result_data["course_id"] = data["course_id"]
               
               elif entity_type == "material":
                   cursor.execute("SELECT title, description, module_id FROM training_materials WHERE id = ?", (entity_id,))
                   data = cursor.fetchone()
                   if data:
                       result_data["title"] = data["title"]
                       result_data["content"] = data["description"]
                       result_data["module_id"] = data["module_id"]
                       
                       # Получаем ID курса
                       cursor.execute("SELECT course_id FROM training_modules WHERE id = ?", (data["module_id"],))
                       module_data = cursor.fetchone()
                       if module_data:
                           result_data["course_id"] = module_data["course_id"]
               
               elif entity_type == "test":
                   cursor.execute("SELECT title, description, module_id FROM training_tests WHERE id = ?", (entity_id,))
                   data = cursor.fetchone()
                   if data:
                       result_data["title"] = data["title"]
                       result_data["content"] = data["description"]
                       result_data["module_id"] = data["module_id"]
                       
                       # Получаем ID курса
                       cursor.execute("SELECT course_id FROM training_modules WHERE id = ?", (data["module_id"],))
                       module_data = cursor.fetchone()
                       if module_data:
                           result_data["course_id"] = module_data["course_id"]
               
               results.append(result_data)
           
           return results
