#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Класс для работы с обратной связью в базе знаний КиберНексус
Поддерживает оба формата: JSON и SQLite
"""

import json
import sqlite3
import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple
import datetime

# Импортируем модели данных для обратной связи
from .feedback_models import (
    FeedbackItem, Comment, Suggestion, ErrorReport, FeatureRequest,
    FeedbackType, FeedbackStatus, FeedbackPriority, create_feedback_item
)


class FeedbackAccessor:
    """Класс для доступа к данным обратной связи"""
    
    def __init__(self, storage_type: str = "json", path: str = "./feedback", kb_path: str = None):
        """
        Инициализация доступа к обратной связи
        
        Args:
            storage_type: Тип хранилища ("json" или "sqlite")
            path: Путь к файлу или директории с данными обратной связи
            kb_path: Путь к базе знаний (для связывания сущностей)
        """
        self.storage_type = storage_type.lower()
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
        """Загрузка данных обратной связи из JSON-файла"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"Данные обратной связи успешно загружены из {self.path}")
        except FileNotFoundError:
            print(f"Файл не найден: {self.path}. Создаётся новый файл обратной связи.")
            self.data = {
                "feedback_info": {
                    "title": "Обратная связь по базе знаний КиберНексус",
                    "version": "1.0",
                    "last_updated": datetime.datetime.now().isoformat()
                },
                "items": []
            }
            self._save_json()
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка формата JSON в файле {self.path}")
    
    def _save_json(self):
        """Сохранение данных обратной связи в JSON-файл"""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        # Обновляем дату последнего обновления
        self.data["feedback_info"]["last_updated"] = datetime.datetime.now().isoformat()
        print(f"Данные обратной связи сохранены в {self.path}")
    
    def _connect_sqlite(self):
        """Подключение к базе данных SQLite"""
        try:
            self.db = sqlite3.connect(self.path)
            self.db.row_factory = sqlite3.Row
            print(f"Подключение к базе данных SQLite установлено: {self.path}")
            
            # Проверка наличия необходимых таблиц
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_items'")
            if not cursor.fetchone():
                print("Создание структуры базы данных обратной связи...")
                self._create_sqlite_schema()
        except sqlite3.Error as e:
            raise ConnectionError(f"Ошибка подключения к SQLite базе данных: {e}")
    
    def _create_sqlite_schema(self):
        """Создание схемы базы данных SQLite для обратной связи"""
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_feedback.sql')
        
        try:
            with open(script_path, 'r', encoding='utf-8') as schema_file:
                schema = schema_file.read()
                
            self.db.executescript(schema)
            self.db.commit()
            print("Структура базы данных обратной связи успешно создана")
        except sqlite3.Error as e:
            self.db.rollback()
            raise Exception(f"Ошибка создания структуры базы данных: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл схемы не найден: {script_path}")
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.storage_type == "sqlite" and self.db:
            self.db.close()
            print("Соединение с базой данных закрыто")
    
    def add_feedback(self, feedback_item: Union[FeedbackItem, Dict[str, Any]]) -> int:
        """
        Добавление новой обратной связи
        
        Args:
            feedback_item: Объект обратной связи или словарь с данными
            
        Returns:
            ID добавленной обратной связи
        """
        # Если передан словарь, преобразуем его в объект
        if isinstance(feedback_item, dict):
            feedback_item = create_feedback_item(feedback_item)
        
        if self.storage_type == "json":
            # Генерируем ID для новой обратной связи
            max_id = 0
            for item in self.data.get("items", []):
                if item.get("id", 0) > max_id:
                    max_id = item.get("id", 0)
            
            new_id = max_id + 1
            feedback_item.id = new_id
            
            # Добавляем обратную связь в список
            if "items" not in self.data:
                self.data["items"] = []
            
            self.data["items"].append(feedback_item.to_dict())
            self._save_json()
            
            return new_id
        else:
            cursor = self.db.cursor()
            
            try:
                # Начинаем транзакцию
                cursor.execute("BEGIN TRANSACTION")
                
                # Добавляем основную информацию
                cursor.execute(
                    """
                    INSERT INTO feedback_items
                    (type, user_id, user_name, user_email, content, entity_type, entity_id, 
                     status, priority, created_at, assigned_to, upvotes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback_item.type.value,
                        feedback_item.user_id,
                        feedback_item.user_name,
                        feedback_item.user_email,
                        feedback_item.content,
                        feedback_item.entity_type,
                        feedback_item.entity_id,
                        feedback_item.status.value,
                        feedback_item.priority.value,
                        feedback_item.created_at,
                        feedback_item.assigned_to,
                        feedback_item.upvotes
                    )
                )
                
                # Получаем ID добавленной записи
                cursor.execute("SELECT last_insert_rowid()")
                feedback_id = cursor.fetchone()[0]
                
                # Добавляем теги
                for tag in feedback_item.tags:
                    cursor.execute(
                        "INSERT INTO feedback_tags (feedback_id, tag) VALUES (?, ?)",
                        (feedback_id, tag)
                    )
                
                # Добавляем вложения
                for attachment in feedback_item.attachments:
                    cursor.execute(
                        """
                        INSERT INTO feedback_attachments 
                        (feedback_id, filename, content_type, file_path, file_size, uploaded_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            feedback_id,
                            attachment.get("filename", ""),
                            attachment.get("content_type", ""),
                            attachment.get("file_path", ""),
                            attachment.get("file_size", 0),
                            datetime.datetime.now().isoformat()
                        )
                    )
                
                # Добавляем специфические данные в зависимости от типа обратной связи
                if isinstance(feedback_item, Suggestion):
                    cursor.execute(
                        "INSERT INTO suggestions (feedback_id, benefits) VALUES (?, ?)",
                        (feedback_id, feedback_item.benefits)
                    )
                elif isinstance(feedback_item, ErrorReport):
                    cursor.execute(
                        "INSERT INTO error_reports (feedback_id, error_type, expected_behavior) VALUES (?, ?, ?)",
                        (feedback_id, feedback_item.error_type, feedback_item.expected_behavior)
                    )
                elif isinstance(feedback_item, FeatureRequest):
                    cursor.execute(
                        "INSERT INTO feature_requests (feedback_id, use_case, business_value) VALUES (?, ?, ?)",
                        (feedback_id, feedback_item.use_case, feedback_item.business_value)
                    )
                
                # Добавляем запись в историю статусов
                cursor.execute(
                    """
                    INSERT INTO feedback_status_history 
                    (feedback_id, old_status, new_status, changed_by, changed_at, comment)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback_id,
                        None,
                        feedback_item.status.value,
                        feedback_item.user_id,
                        feedback_item.created_at,
                        "Создана новая запись обратной связи"
                    )
                )
                
                # Завершаем транзакцию
                cursor.execute("COMMIT")
                
                return feedback_id
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
    
    def get_feedback(self, feedback_id: int) -> Optional[FeedbackItem]:
        """
        Получение обратной связи по ID
        
        Args:
            feedback_id: ID обратной связи
            
        Returns:
            Объект обратной связи или None, если не найдено
        """
        if self.storage_type == "json":
            for item in self.data.get("items", []):
                if item.get("id") == feedback_id:
                    return create_feedback_item(item)
            return None
        else:
            cursor = self.db.cursor()
            
            # Получаем основную информацию
            cursor.execute("SELECT * FROM feedback_items WHERE id = ?", (feedback_id,))
            item = cursor.fetchone()
            
            if not item:
                return None
            
            # Преобразуем в словарь
            result = dict(item)
            
            # Получаем теги
            cursor.execute("SELECT tag FROM feedback_tags WHERE feedback_id = ?", (feedback_id,))
            result["tags"] = [row["tag"] for row in cursor.fetchall()]
            
            # Получаем вложения
            cursor.execute("SELECT * FROM feedback_attachments WHERE feedback_id = ?", (feedback_id,))
            result["attachments"] = [dict(row) for row in cursor.fetchall()]
            
            # Получаем дополнительную информацию в зависимости от типа
            if result["type"] == FeedbackType.SUGGESTION.value:
                cursor.execute("SELECT benefits FROM suggestions WHERE feedback_id = ?", (feedback_id,))
                suggestion_data = cursor.fetchone()
                if suggestion_data:
                    result["benefits"] = suggestion_data["benefits"]
            
            elif result["type"] == FeedbackType.ERROR_REPORT.value:
                cursor.execute(
                    "SELECT error_type, expected_behavior FROM error_reports WHERE feedback_id = ?", 
                    (feedback_id,)
                )
                error_data = cursor.fetchone()
                if error_data:
                    result["error_type"] = error_data["error_type"]
                    result["expected_behavior"] = error_data["expected_behavior"]
            
            elif result["type"] == FeedbackType.FEATURE_REQUEST.value:
                cursor.execute(
                    "SELECT use_case, business_value FROM feature_requests WHERE feedback_id = ?", 
                    (feedback_id,)
                )
                feature_data = cursor.fetchone()
                if feature_data:
                    result["use_case"] = feature_data["use_case"]
                    result["business_value"] = feature_data["business_value"]
            
            # Создаем объект соответствующего типа
            return create_feedback_item(result)
    
    def update_feedback(self, feedback_id: int, update_data: Dict[str, Any], changed_by: str = None) -> bool:
        """
        Обновление существующей обратной связи
        
        Args:
            feedback_id: ID обратной связи
            update_data: Данные для обновления
            changed_by: ID пользователя, выполняющего обновление
            
        Returns:
            True, если обновление успешно, иначе False
        """
        if self.storage_type == "json":
            for i, item in enumerate(self.data.get("items", [])):
                if item.get("id") == feedback_id:
                    # Сохраняем старый статус для истории
                    old_status = item.get("status")
                    
                    # Обновляем данные
                    for key, value in update_data.items():
                        item[key] = value
                    
                    # Устанавливаем дату обновления
                    item["updated_at"] = datetime.datetime.now().isoformat()
                    
                    # Если статус изменился, добавляем запись в историю
                    if "status" in update_data and old_status != update_data["status"]:
                        if "status_history" not in self.data:
                            self.data["status_history"] = []
                        
                        self.data["status_history"].append({
                            "feedback_id": feedback_id,
                            "old_status": old_status,
                            "new_status": update_data["status"],
                            "changed_by": changed_by,
                            "changed_at": datetime.datetime.now().isoformat(),
                            "comment": update_data.get("status_comment", "")
                        })
                    
                    self._save_json()
                    return True
            
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                # Получаем текущую запись для определения изменений
                cursor.execute("SELECT * FROM feedback_items WHERE id = ?", (feedback_id,))
                current_item = cursor.fetchone()
                
                if not current_item:
                    return False
                
                # Начинаем транзакцию
                cursor.execute("BEGIN TRANSACTION")
                
                # Обновляем основные поля
                update_fields = []
                update_values = []
                
                # Список полей, которые можно обновить
                updatable_fields = [
                    "type", "user_id", "user_name", "user_email", "content", 
                    "entity_type", "entity_id", "status", "priority", "assigned_to", "upvotes"
                ]
                
                for field in updatable_fields:
                    if field in update_data:
                        update_fields.append(f"{field} = ?")
                        update_values.append(update_data[field])
                
                # Если есть поля для обновления
                if update_fields:
                    # Добавляем значения для WHERE-условия
                    update_values.append(feedback_id)
                    
                    # Формируем и выполняем запрос
                    update_query = f"UPDATE feedback_items SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(update_query, update_values)
                
                # Обновляем теги, если они указаны
                if "tags" in update_data:
                    # Удаляем существующие теги
                    cursor.execute("DELETE FROM feedback_tags WHERE feedback_id = ?", (feedback_id,))
                    
                    # Добавляем новые теги
                    for tag in update_data["tags"]:
                        cursor.execute(
                            "INSERT INTO feedback_tags (feedback_id, tag) VALUES (?, ?)",
                            (feedback_id, tag)
                        )
                
                # Обновляем специфические данные в зависимости от типа
                if "type" in update_data:
                    feedback_type = update_data["type"]
                    
                    if feedback_type == FeedbackType.SUGGESTION.value and "benefits" in update_data:
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO suggestions (feedback_id, benefits) 
                            VALUES (?, ?)
                            """,
                            (feedback_id, update_data["benefits"])
                        )
                    
                    elif feedback_type == FeedbackType.ERROR_REPORT.value:
                        if "error_type" in update_data or "expected_behavior" in update_data:
                            # Получаем текущие данные
                            cursor.execute(
                                "SELECT * FROM error_reports WHERE feedback_id = ?", 
                                (feedback_id,)
                            )
                            current_error = cursor.fetchone()
                            
                            error_type = update_data.get("error_type", 
                                                      current_error["error_type"] if current_error else "")
                            expected_behavior = update_data.get("expected_behavior", 
                                                            current_error["expected_behavior"] if current_error else "")
                            
                            cursor.execute(
                                """
                                INSERT OR REPLACE INTO error_reports 
                                (feedback_id, error_type, expected_behavior) 
                                VALUES (?, ?, ?)
                                """,
                                (feedback_id, error_type, expected_behavior)
                            )
                    
                    elif feedback_type == FeedbackType.FEATURE_REQUEST.value:
                        if "use_case" in update_data or "business_value" in update_data:
                            # Получаем текущие данные
                            cursor.execute(
                                "SELECT * FROM feature_requests WHERE feedback_id = ?", 
                                (feedback_id,)
                            )
                            current_feature = cursor.fetchone()
                            
                            use_case = update_data.get("use_case", 
                                                    current_feature["use_case"] if current_feature else "")
                            business_value = update_data.get("business_value", 
                                                          current_feature["business_value"] if current_feature else "")
                            
                            cursor.execute(
                                """
                                INSERT OR REPLACE INTO feature_requests 
                                (feedback_id, use_case, business_value) 
                                VALUES (?, ?, ?)
                                """,
                                (feedback_id, use_case, business_value)
                            )
                
                # Если статус изменился, добавляем запись в историю
                if "status" in update_data and current_item["status"] != update_data["status"]:
                    cursor.execute(
                        """
                        INSERT INTO feedback_status_history 
                        (feedback_id, old_status, new_status, changed_by, changed_at, comment)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            feedback_id,
                            current_item["status"],
                            update_data["status"],
                            changed_by,
                            datetime.datetime.now().isoformat(),
                            update_data.get("status_comment", "")
                        )
                    )
                
                # Завершаем транзакцию
                cursor.execute("COMMIT")
                
                return True
            except Exception as e:
                cursor.execute("ROLLBACK")
                print(f"Ошибка при обновлении обратной связи: {e}")
                return False
    
    def delete_feedback(self, feedback_id: int) -> bool:
        """
        Удаление обратной связи по ID
        
        Args:
            feedback_id: ID обратной связи
            
        Returns:
            True, если удаление успешно, иначе False
        """
        if self.storage_type == "json":
            for i, item in enumerate(self.data.get("items", [])):
                if item.get("id") == feedback_id:
                    self.data["items"].pop(i)
                    self._save_json()
                    return True
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                # В SQLite все связанные записи будут удалены благодаря ON DELETE CASCADE
                cursor.execute("DELETE FROM feedback_items WHERE id = ?", (feedback_id,))
                self.db.commit()
                
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                print(f"Ошибка при удалении обратной связи: {e}")
                return False
    
    def get_feedback_list(
        self, 
        feedback_type: str = None, 
        status: str = None, 
        entity_type: str = None, 
        entity_id: str = None,
        user_id: str = None,
        tags: List[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[FeedbackItem]:
        """
        Получение списка обратной связи с возможностью фильтрации и сортировки
        
        Args:
            feedback_type: Тип обратной связи
            status: Статус обработки
            entity_type: Тип сущности
            entity_id: ID сущности
            user_id: ID пользователя
            tags: Список тегов для фильтрации
            limit: Ограничение количества результатов
            offset: Смещение для пагинации
            sort_by: Поле для сортировки
            sort_order: Порядок сортировки ("asc" или "desc")
            
        Returns:
            Список объектов обратной связи
        """
        if self.storage_type == "json":
            # Фильтрация
            filtered_items = self.data.get("items", [])
            
            if feedback_type:
                filtered_items = [item for item in filtered_items if item.get("type") == feedback_type]
            
            if status:
                filtered_items = [item for item in filtered_items if item.get("status") == status]
            
            if entity_type:
                filtered_items = [item for item in filtered_items if item.get("entity_type") == entity_type]
            
            if entity_id:
                filtered_items = [item for item in filtered_items if item.get("entity_id") == entity_id]
            
            if user_id:
                filtered_items = [item for item in filtered_items if item.get("user_id") == user_id]
            
            if tags:
                filtered_items = [
                    item for item in filtered_items 
                    if any(tag in item.get("tags", []) for tag in tags)
                ]
            
            # Сортировка
            reverse = sort_order.lower() == "desc"
            filtered_items.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
            
            # Пагинация
            paginated_items = filtered_items[offset:offset + limit]
            
            # Преобразование в объекты
            return [create_feedback_item(item) for item in paginated_items]
        else:
            cursor = self.db.cursor()
            
            # Формируем базовый запрос
            query = """
            SELECT fi.* FROM feedback_items fi
            """
            
            # Условия для WHERE
            conditions = []
            params = []
            
            # Если требуется фильтрация по тегам, добавляем JOIN
            if tags:
                query += """
                JOIN feedback_tags ft ON fi.id = ft.feedback_id
                """
                conditions.append("ft.tag IN ({})".format(",".join(["?" for _ in tags])))
                params.extend(tags)
            
            # Добавляем остальные условия
            if feedback_type:
                conditions.append("fi.type = ?")
                params.append(feedback_type)
            
            if status:
                conditions.append("fi.status = ?")
                params.append(status)
            
            if entity_type:
                conditions.append("fi.entity_type = ?")
                params.append(entity_type)
            
            if entity_id:
                conditions.append("fi.entity_id = ?")
                params.append(entity_id)
            
            if user_id:
                conditions.append("fi.user_id = ?")
                params.append(user_id)
            
            # Добавляем WHERE, если есть условия
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            # Если фильтрация по тегам, добавляем GROUP BY для исключения дубликатов
            if tags:
                query += " GROUP BY fi.id"
            
            # Добавляем сортировку
            query += f" ORDER BY fi.{sort_by} {sort_order}"
            
            # Добавляем пагинацию
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            # Выполняем запрос
            cursor.execute(query, params)
            items = cursor.fetchall()
            
            # Преобразуем результаты в объекты
            result = []
            for item in items:
                feedback_id = item["id"]
                item_dict = dict(item)
                
                # Получаем теги
                cursor.execute("SELECT tag FROM feedback_tags WHERE feedback_id = ?", (feedback_id,))
                item_dict["tags"] = [row["tag"] for row in cursor.fetchall()]
                
                # Получаем вложения
                cursor.execute("SELECT * FROM feedback_attachments WHERE feedback_id = ?", (feedback_id,))
                item_dict["attachments"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем дополнительную информацию в зависимости от типа
                if item["type"] == FeedbackType.SUGGESTION.value:
                    cursor.execute("SELECT benefits FROM suggestions WHERE feedback_id = ?", (feedback_id,))
                    suggestion_data = cursor.fetchone()
                    if suggestion_data:
                        item_dict["benefits"] = suggestion_data["benefits"]
                
                elif item["type"] == FeedbackType.ERROR_REPORT.value:
                    cursor.execute(
                        "SELECT error_type, expected_behavior FROM error_reports WHERE feedback_id = ?", 
                        (feedback_id,)
                    )
                    error_data = cursor.fetchone()
                    if error_data:
                        item_dict["error_type"] = error_data["error_type"]
                        item_dict["expected_behavior"] = error_data["expected_behavior"]
                
                elif item["type"] == FeedbackType.FEATURE_REQUEST.value:
                    cursor.execute(
                        "SELECT use_case, business_value FROM feature_requests WHERE feedback_id = ?", 
                        (feedback_id,)
                    )
                    feature_data = cursor.fetchone()
                    if feature_data:
                        item_dict["use_case"] = feature_data["use_case"]
                        item_dict["business_value"] = feature_data["business_value"]
                
                # Создаем объект и добавляем в результат
                result.append(create_feedback_item(item_dict))
            
            return result
    
    def search_feedback(self, query: str, limit: int = 20) -> List[FeedbackItem]:
        """
        Полнотекстовый поиск по обратной связи
        
        Args:
            query: Текст запроса
            limit: Ограничение количества результатов
            
        Returns:
            Список объектов обратной связи
        """
        if self.storage_type == "json":
            # Простой поиск по тексту в JSON
            query_lower = query.lower()
            results = []
            
            for item in self.data.get("items", []):
                # Проверяем содержимое обратной связи
                content = item.get("content", "").lower()
                if query_lower in content:
                    results.append(create_feedback_item(item))
                    continue
                
                # Проверяем теги
                tags = " ".join(item.get("tags", [])).lower()
                if query_lower in tags:
                    results.append(create_feedback_item(item))
                    continue
                
                # Проверяем имя пользователя
                user_name = item.get("user_name", "").lower()
                if query_lower in user_name:
                    results.append(create_feedback_item(item))
                    continue
            
            return results[:limit]
        else:
            cursor = self.db.cursor()
            
            # Подготовка запроса для полнотекстового поиска
            search_query = ' '.join(f'"{word}"' for word in re.findall(r'\w+', query))
            
            # Выполняем поиск
            cursor.execute(
                """
                SELECT fi.* FROM feedback_items fi
                JOIN feedback_search fs ON fi.id = fs.rowid
                WHERE feedback_search MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (search_query, limit)
            )
            items = cursor.fetchall()
            
            # Преобразуем результаты в объекты
            result = []
            for item in items:
                feedback_id = item["id"]
                item_dict = dict(item)
                
                # Получа
                # Получаем теги
                cursor.execute("SELECT tag FROM feedback_tags WHERE feedback_id = ?", (feedback_id,))
                item_dict["tags"] = [row["tag"] for row in cursor.fetchall()]
                
                # Получаем вложения
                cursor.execute("SELECT * FROM feedback_attachments WHERE feedback_id = ?", (feedback_id,))
                item_dict["attachments"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем дополнительную информацию в зависимости от типа
                if item["type"] == FeedbackType.SUGGESTION.value:
                    cursor.execute("SELECT benefits FROM suggestions WHERE feedback_id = ?", (feedback_id,))
                    suggestion_data = cursor.fetchone()
                    if suggestion_data:
                        item_dict["benefits"] = suggestion_data["benefits"]
                
                elif item["type"] == FeedbackType.ERROR_REPORT.value:
                    cursor.execute(
                        "SELECT error_type, expected_behavior FROM error_reports WHERE feedback_id = ?", 
                        (feedback_id,)
                    )
                    error_data = cursor.fetchone()
                    if error_data:
                        item_dict["error_type"] = error_data["error_type"]
                        item_dict["expected_behavior"] = error_data["expected_behavior"]
                
                elif item["type"] == FeedbackType.FEATURE_REQUEST.value:
                    cursor.execute(
                        "SELECT use_case, business_value FROM feature_requests WHERE feedback_id = ?", 
                        (feedback_id,)
                    )
                    feature_data = cursor.fetchone()
                    if feature_data:
                        item_dict["use_case"] = feature_data["use_case"]
                        item_dict["business_value"] = feature_data["business_value"]
                
                # Создаем объект и добавляем в результат
                result.append(create_feedback_item(item_dict))
            
            return result
    
    def get_status_history(self, feedback_id: int) -> List[Dict[str, Any]]:
        """
        Получение истории изменений статуса обратной связи
        
        Args:
            feedback_id: ID обратной связи
            
        Returns:
            Список записей истории изменений
        """
        if self.storage_type == "json":
            history = []
            for item in self.data.get("status_history", []):
                if item.get("feedback_id") == feedback_id:
                    history.append(item)
            
            # Сортируем по дате изменения
            history.sort(key=lambda x: x.get("changed_at", ""))
            return history
        else:
            cursor = self.db.cursor()
            
            cursor.execute(
                """
                SELECT * FROM feedback_status_history 
                WHERE feedback_id = ? 
                ORDER BY changed_at
                """,
                (feedback_id,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add_comment(self, feedback_id: int, user_id: str, user_name: str, content: str) -> int:
        """
        Добавление комментария к обратной связи
        
        Args:
            feedback_id: ID обратной связи
            user_id: ID пользователя
            user_name: Имя пользователя
            content: Содержание комментария
            
        Returns:
            ID добавленного комментария или -1 в случае ошибки
        """
        if self.storage_type == "json":
            # Проверяем существование обратной связи
            feedback_exists = False
            for item in self.data.get("items", []):
                if item.get("id") == feedback_id:
                    feedback_exists = True
                    break
            
            if not feedback_exists:
                return -1
            
            # Создаем структуру для комментариев, если её нет
            if "comments" not in self.data:
                self.data["comments"] = []
            
            # Генерируем ID для нового комментария
            max_id = 0
            for comment in self.data["comments"]:
                if comment.get("id", 0) > max_id:
                    max_id = comment.get("id", 0)
            
            comment_id = max_id + 1
            
            # Добавляем комментарий
            self.data["comments"].append({
                "id": comment_id,
                "feedback_id": feedback_id,
                "user_id": user_id,
                "user_name": user_name,
                "content": content,
                "created_at": datetime.datetime.now().isoformat()
            })
            
            self._save_json()
            return comment_id
        else:
            cursor = self.db.cursor()
            
            try:
                # Проверяем существование обратной связи
                cursor.execute("SELECT id FROM feedback_items WHERE id = ?", (feedback_id,))
                if not cursor.fetchone():
                    return -1
                
                # Добавляем комментарий
                cursor.execute(
                    """
                    INSERT INTO feedback_comments 
                    (feedback_id, user_id, user_name, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        feedback_id,
                        user_id,
                        user_name,
                        content,
                        datetime.datetime.now().isoformat()
                    )
                )
                
                self.db.commit()
                
                # Получаем ID добавленного комментария
                cursor.execute("SELECT last_insert_rowid()")
                return cursor.fetchone()[0]
            except Exception as e:
                self.db.rollback()
                print(f"Ошибка при добавлении комментария: {e}")
                return -1
    
    def get_comments(self, feedback_id: int) -> List[Dict[str, Any]]:
        """
        Получение комментариев к обратной связи
        
        Args:
            feedback_id: ID обратной связи
            
        Returns:
            Список комментариев
        """
        if self.storage_type == "json":
            comments = []
            for comment in self.data.get("comments", []):
                if comment.get("feedback_id") == feedback_id:
                    comments.append(comment)
            
            # Сортируем по дате создания
            comments.sort(key=lambda x: x.get("created_at", ""))
            return comments
        else:
            cursor = self.db.cursor()
            
            cursor.execute(
                """
                SELECT * FROM feedback_comments 
                WHERE feedback_id = ? 
                ORDER BY created_at
                """,
                (feedback_id,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add_tag(self, feedback_id: int, tag: str) -> bool:
        """
        Добавление тега к обратной связи
        
        Args:
            feedback_id: ID обратной связи
            tag: Тег для добавления
            
        Returns:
            True, если тег добавлен успешно, иначе False
        """
        if self.storage_type == "json":
            for item in self.data.get("items", []):
                if item.get("id") == feedback_id:
                    if "tags" not in item:
                        item["tags"] = []
                    
                    # Проверяем, что тег еще не добавлен
                    if tag not in item["tags"]:
                        item["tags"].append(tag)
                        self._save_json()
                    
                    return True
            
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                # Проверяем существование обратной связи
                cursor.execute("SELECT id FROM feedback_items WHERE id = ?", (feedback_id,))
                if not cursor.fetchone():
                    return False
                
                # Проверяем, существует ли уже такой тег
                cursor.execute(
                    "SELECT feedback_id FROM feedback_tags WHERE feedback_id = ? AND tag = ?",
                    (feedback_id, tag)
                )
                
                if not cursor.fetchone():
                    # Добавляем тег
                    cursor.execute(
                        "INSERT INTO feedback_tags (feedback_id, tag) VALUES (?, ?)",
                        (feedback_id, tag)
                    )
                    
                    self.db.commit()
                
                return True
            except Exception as e:
                self.db.rollback()
                print(f"Ошибка при добавлении тега: {e}")
                return False
    
    def remove_tag(self, feedback_id: int, tag: str) -> bool:
        """
        Удаление тега из обратной связи
        
        Args:
            feedback_id: ID обратной связи
            tag: Тег для удаления
            
        Returns:
            True, если тег удален успешно, иначе False
        """
        if self.storage_type == "json":
            for item in self.data.get("items", []):
                if item.get("id") == feedback_id:
                    if "tags" in item and tag in item["tags"]:
                        item["tags"].remove(tag)
                        self._save_json()
                        return True
            
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                cursor.execute(
                    "DELETE FROM feedback_tags WHERE feedback_id = ? AND tag = ?",
                    (feedback_id, tag)
                )
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                print(f"Ошибка при удалении тега: {e}")
                return False
    
    def upvote_feedback(self, feedback_id: int) -> bool:
        """
        Увеличение счетчика голосов за обратную связь
        
        Args:
            feedback_id: ID обратной связи
            
        Returns:
            True, если счетчик увеличен успешно, иначе False
        """
        if self.storage_type == "json":
            for item in self.data.get("items", []):
                if item.get("id") == feedback_id:
                    item["upvotes"] = item.get("upvotes", 0) + 1
                    self._save_json()
                    return True
            
            return False
        else:
            cursor = self.db.cursor()
            
            try:
                cursor.execute(
                    "UPDATE feedback_items SET upvotes = upvotes + 1 WHERE id = ?",
                    (feedback_id,)
                )
                
                self.db.commit()
                return cursor.rowcount > 0
            except Exception as e:
                self.db.rollback()
                print(f"Ошибка при увеличении счетчика голосов: {e}")
                return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по обратной связи
        
        Returns:
            Словарь со статистическими данными
        """
        if self.storage_type == "json":
            items = self.data.get("items", [])
            
            # Подсчет по типам
            type_counts = {}
            for item in items:
                item_type = item.get("type", "unknown")
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            # Подсчет по статусам
            status_counts = {}
            for item in items:
                status = item.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Наиболее популярные теги
            tag_counts = {}
            for item in items:
                for tag in item.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Сортируем теги по популярности
            popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_items": len(items),
                "type_counts": type_counts,
                "status_counts": status_counts,
                "popular_tags": dict(popular_tags)
            }
        else:
            cursor = self.db.cursor()
            
            # Общее количество
            cursor.execute("SELECT COUNT(*) as count FROM feedback_items")
            total_items = cursor.fetchone()["count"]
            
            # Подсчет по типам
            cursor.execute(
                """
                SELECT type, COUNT(*) as count 
                FROM feedback_items 
                GROUP BY type
                """
            )
            type_counts = {row["type"]: row["count"] for row in cursor.fetchall()}
            
            # Подсчет по статусам
            cursor.execute(
                """
                SELECT status, COUNT(*) as count 
                FROM feedback_items 
                GROUP BY status
                """
            )
            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            # Наиболее популярные теги
            cursor.execute(
                """
                SELECT tag, COUNT(*) as count 
                FROM feedback_tags 
                GROUP BY tag 
                ORDER BY count DESC 
                LIMIT 10
                """
            )
            popular_tags = {row["tag"]: row["count"] for row in cursor.fetchall()}
            
            return {
                "total_items": total_items,
                "type_counts": type_counts,
                "status_counts": status_counts,
                "popular_tags": popular_tags
            }
    
    def export_to_json(self, output_path: str) -> None:
        """
        Экспорт данных обратной связи в JSON-файл
        
        Args:
            output_path: Путь к файлу для экспорта
        """
        if self.storage_type == "json":
            # Просто копируем текущие данные
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"Данные обратной связи экспортированы в {output_path}")
        else:
            # Экспортируем данные из SQLite в JSON
            export_data = {
                "feedback_info": {
                    "title": "Обратная связь по базе знаний КиберНексус",
                    "version": "1.0",
                    "last_updated": datetime.datetime.now().isoformat()
                },
                "items": [],
                "comments": [],
                "status_history": []
            }
            
            cursor = self.db.cursor()
            
            # Получаем все записи обратной связи
            cursor.execute("SELECT * FROM feedback_items")
            items = cursor.fetchall()
            
            for item in items:
                feedback_id = item["id"]
                item_dict = dict(item)
                
                # Получаем теги
                cursor.execute("SELECT tag FROM feedback_tags WHERE feedback_id = ?", (feedback_id,))
                item_dict["tags"] = [row["tag"] for row in cursor.fetchall()]
                
                # Получаем вложения
                cursor.execute("SELECT * FROM feedback_attachments WHERE feedback_id = ?", (feedback_id,))
                item_dict["attachments"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем дополнительную информацию в зависимости от типа
                if item["type"] == FeedbackType.SUGGESTION.value:
                    cursor.execute("SELECT benefits FROM suggestions WHERE feedback_id = ?", (feedback_id,))
                    suggestion_data = cursor.fetchone()
                    if suggestion_data:
                        item_dict["benefits"] = suggestion_data["benefits"]
                
                elif item["type"] == FeedbackType.ERROR_REPORT.value:
                    cursor.execute(
                        "SELECT error_type, expected_behavior FROM error_reports WHERE feedback_id = ?", 
                        (feedback_id,)
                    )
                    error_data = cursor.fetchone()
                    if error_data:
                        item_dict["error_type"] = error_data["error_type"]
                        item_dict["expected_behavior"] = error_data["expected_behavior"]
                
                elif item["type"] == FeedbackType.FEATURE_REQUEST.value:
                    cursor.execute(
                        "SELECT use_case, business_value FROM feature_requests WHERE feedback_id = ?", 
                        (feedback_id,)
                    )
                    feature_data = cursor.fetchone()
                    if feature_data:
                        item_dict["use_case"] = feature_data["use_case"]
                        item_dict["business_value"] = feature_data["business_value"]
                
                export_data["items"].append(item_dict)
            
            # Получаем все комментарии
            cursor.execute("SELECT * FROM feedback_comments")
            export_data["comments"] = [dict(row) for row in cursor.fetchall()]
            
            # Получаем историю изменений статусов
            cursor.execute("SELECT * FROM feedback_status_history")
            export_data["status_history"] = [dict(row) for row in cursor.fetchall()]
            
            # Сохраняем данные в JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"Данные обратной связи экспортированы в {output_path}")
    
    def import_from_json(self, input_path: str) -> None:
        """
        Импорт данных обратной связи из JSON-файла
        
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
                print(f"Данные обратной связи импортированы из {input_path}")
            else:
                cursor = self.db.cursor()
                
                try:
                    # Начинаем транзакцию
                    cursor.execute("BEGIN TRANSACTION")
                    
                    # Очищаем существующие данные
                    cursor.execute("DELETE FROM feedback_items")
                    
                    # Импортируем данные
                    for item in import_data.get("items", []):
                        # Добавляем основную информацию
                        cursor.execute(
                            """
                            INSERT INTO feedback_items
                            (id, type, user_id, user_name, user_email, content, entity_type, entity_id, 
                             status, priority, created_at, updated_at, assigned_to, upvotes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                item.get("id"),
                                item.get("type"),
                                item.get("user_id"),
                                item.get("user_name"),
                                item.get("user_email"),
                                item.get("content"),
                                item.get("entity_type"),
                                item.get("entity_id"),
                                item.get("status"),
                                item.get("priority"),
                                item.get("created_at"),
                                item.get("updated_at"),
                                item.get("assigned_to"),
                                item.get("upvotes", 0)
                            )
                        )
                        
                        feedback_id = item.get("id")
                        
                        # Добавляем теги
                        for tag in item.get("tags", []):
                            cursor.execute(
                                "INSERT INTO feedback_tags (feedback_id, tag) VALUES (?, ?)",
                                (feedback_id, tag)
                            )
                        
                        # Добавляем вложения
                        for attachment in item.get("attachments", []):
                            cursor.execute(
                                """
                                INSERT INTO feedback_attachments 
                                (feedback_id, filename, content_type, file_path, file_size, uploaded_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    feedback_id,
                                    attachment.get("filename", ""),
                                    attachment.get("content_type", ""),
                                    attachment.get("file_path", ""),
                                    attachment.get("file_size", 0),
                                    attachment.get("uploaded_at", datetime.datetime.now().isoformat())
                                )
                            )
                        
                        # Добавляем специфические данные в зависимости от типа
                        if item.get("type") == FeedbackType.SUGGESTION.value and "benefits" in item:
                            cursor.execute(
                                "INSERT INTO suggestions (feedback_id, benefits) VALUES (?, ?)",
                                (feedback_id, item.get("benefits"))
                            )
                        
                        elif item.get("type") == FeedbackType.ERROR_REPORT.value:
                            if "error_type" in item or "expected_behavior" in item:
                                cursor.execute(
                                    """
                                    INSERT INTO error_reports 
                                    (feedback_id, error_type, expected_behavior) 
                                    VALUES (?, ?, ?)
                                    """,
                                    (
                                        feedback_id,
                                        item.get("error_type", ""),
                                        item.get("expected_behavior", "")
                                    )
                                )
                        
                        elif item.get("type") == FeedbackType.FEATURE_REQUEST.value:
                            if "use_case" in item or "business_value" in item:
                                cursor.execute(
                                    """
                                    INSERT INTO feature_requests 
                                    (feedback_id, use_case, business_value) 
                                    VALUES (?, ?, ?)
                                    """,
                                    (
                                        feedback_id,
                                        item.get("use_case", ""),
                                        item.get("business_value", "")
                                    )
                                )
                    
                    # Импортируем комментарии
                    for comment in import_data.get("comments", []):
                        cursor.execute(
                            """
                            INSERT INTO feedback_comments 
                            (id, feedback_id, user_id, user_name, content, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                comment.get("id"),
                                comment.get("feedback_id"),
                                comment.get("user_id"),
                                comment.get("user_name"),
                                comment.get("content"),
                                comment.get("created_at")
                            )
                        )
                    
                    # Импортируем историю изменений статусов
                    for history in import_data.get("status_history", []):
                        cursor.execute(
                            """
                            INSERT INTO feedback_status_history 
                            (id, feedback_id, old_status, new_status, changed_by, changed_at, comment)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                history.get("id"),
                                history.get("feedback_id"),
                                history.get("old_status"),
                                history.get("new_status"),
                                history.get("changed_by"),
                                history.get("changed_at"),
                                history.get("comment")
                            )
                        )
                    
                    # Завершаем транзакцию
                    cursor.execute("COMMIT")
                    print(f"Данные обратной связи импортированы из {input_path}")
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise Exception(f"Ошибка при импорте данных: {e}")
        except Exception as e:
            raise Exception(f"Ошибка при импорте из JSON: {e}")
