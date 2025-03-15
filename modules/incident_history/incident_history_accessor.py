#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для работы с хронологией инцидентов кибербезопасности.
Позволяет хранить, искать и анализировать исторические данные об инцидентах.
"""

import json
import sqlite3
import os
import re
import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

class IncidentHistoryAccessor:
    """Класс для работы с данными о хронологии инцидентов кибербезопасности"""
    
    def __init__(self, storage_type: str = "json", path: str = None, kb_accessor = None):
        """
        Инициализация модуля хронологии инцидентов
        
        Args:
            storage_type: Тип хранилища ("json" или "sqlite")
            path: Путь к файлу хранилища (если None, используется путь из kb_accessor)
            kb_accessor: Экземпляр KnowledgeBaseAccessor (опционально)
        """
        self.storage_type = storage_type.lower()
        self.kb_accessor = kb_accessor
        self.db = None
        self.data = None
        
        # Определяем путь к хранилищу
        if path:
            self.path = path
        elif kb_accessor:
            # Используем директорию основной базы знаний
            base_path = kb_accessor.path
            if storage_type == "json":
                self.path = os.path.join(os.path.dirname(base_path), "incident_history.json")
            else:
                self.path = os.path.join(os.path.dirname(base_path), "incident_history.db")
        else:
            # Пути по умолчанию
            if storage_type == "json":
                self.path = "incident_history.json"
            else:
                self.path = "incident_history.db"
                
        if self.storage_type == "json":
            self._load_json()
        elif self.storage_type == "sqlite":
            self._connect_sqlite()
        else:
            raise ValueError(f"Неподдерживаемый тип хранилища: {storage_type}. Используйте 'json' или 'sqlite'.")
    
    def _load_json(self):
        """Загрузка данных об инцидентах из JSON-файла"""
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            print(f"Данные об инцидентах успешно загружены из {self.path}")
        except FileNotFoundError:
            print(f"Файл не найден: {self.path}. Создаётся новый файл данных.")
            self.data = {
                "categories": [
                    {"id": 1, "name": "Malware", "description": "Инциденты, связанные с вредоносным ПО, включая вирусы, трояны, шпионское ПО и программы-вымогатели"},
                    {"id": 2, "name": "Data Breach", "description": "Утечка или кража конфиденциальных данных"},
                    {"id": 3, "name": "DDoS", "description": "Распределенные атаки типа \"отказ в обслуживании\""},
                    {"id": 4, "name": "Phishing", "description": "Социальная инженерия, направленная на получение конфиденциальной информации"},
                    {"id": 5, "name": "Zero-day Exploitation", "description": "Эксплуатация ранее неизвестных уязвимостей"},
                    {"id": 6, "name": "Insider Threat", "description": "Угрозы, исходящие от сотрудников организации"},
                    {"id": 7, "name": "Supply Chain Attack", "description": "Атаки через компрометацию цепочки поставок программного обеспечения"},
                    {"id": 8, "name": "APT", "description": "Целенаправленные продвинутые постоянные угрозы"}
                ],
                "incidents": []
            }
            self._save_json()
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка формата JSON в файле {self.path}")
    
    def _save_json(self):
        """Сохранение данных об инцидентах в JSON-файл"""
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Данные об инцидентах сохранены в {self.path}")
    
    def _connect_sqlite(self):
        """Подключение к базе данных SQLite"""
        try:
            self.db = sqlite3.connect(self.path)
            self.db.row_factory = sqlite3.Row
            print(f"Подключение к базе данных SQLite установлено: {self.path}")
            
            # Проверка наличия необходимых таблиц
            cursor = self.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='security_incidents'")
            if not cursor.fetchone():
                print("Создание структуры базы данных...")
                self._create_sqlite_schema()
        except sqlite3.Error as e:
            raise ConnectionError(f"Ошибка подключения к SQLite базе данных: {e}")
    
    def _create_sqlite_schema(self):
        """Создание схемы базы данных SQLite"""
        try:
            # Определяем путь к файлу схемы
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_incident_history.sql')
            
            # Проверяем существование файла схемы
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Файл схемы не найден: {schema_path}")
            
            # Загружаем схему из файла
            with open(schema_path, 'r', encoding='utf-8') as schema_file:
                schema = schema_file.read()
            
            self.db.executescript(schema)
            self.db.commit()
            print("Структура базы данных инцидентов успешно создана")
        except sqlite3.Error as e:
            self.db.rollback()
            raise Exception(f"Ошибка создания структуры базы данных: {e}")
    
    def close(self):
        """Закрытие соединения с базой данных"""
        if self.storage_type == "sqlite" and self.db:
            self.db.close()
            print("Соединение с базой данных инцидентов закрыто")
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Получение всех категорий инцидентов
        
        Returns:
            Список категорий инцидентов
        """
        if self.storage_type == "json":
            return self.data.get("categories", [])
        else:
            cursor = self.db.cursor()
            cursor.execute("SELECT * FROM incident_categories ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def add_category(self, name: str, description: str = "") -> int:
        """
        Добавление новой категории инцидентов
        
        Args:
            name: Название категории
            description: Описание категории
            
        Returns:
            ID добавленной категории
        """
        if not name:
            raise ValueError("Название категории не может быть пустым")
        
        if self.storage_type == "json":
            # Определяем новый ID
            categories = self.data.get("categories", [])
            next_id = max([cat.get("id", 0) for cat in categories] + [0]) + 1
            
            # Добавляем новую категорию
            new_category = {
                "id": next_id,
                "name": name,
                "description": description
            }
            categories.append(new_category)
            self.data["categories"] = categories
            
            self._save_json()
            return next_id
        else:
            cursor = self.db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO incident_categories (name, description) VALUES (?, ?)",
                    (name, description)
                )
                self.db.commit()
                return cursor.lastrowid
            except sqlite3.Error as e:
                self.db.rollback()
                raise Exception(f"Ошибка при добавлении категории: {e}")

    def add_incident(self, incident_data: Dict[str, Any]) -> int:
        """
        Добавление нового инцидента
        
        Args:
            incident_data: Данные об инциденте (словарь)
            
        Returns:
            ID добавленного инцидента
        """
        required_fields = ["title", "description", "date_occurred", "severity"]
        for field in required_fields:
            if field not in incident_data:
                raise ValueError(f"Отсутствует обязательное поле: {field}")
        
        if self.storage_type == "json":
            incidents = self.data.get("incidents", [])
            
            # Определяем новый ID
            next_id = max([inc.get("id", 0) for inc in incidents] + [0]) + 1
            
            # Добавляем новый инцидент
            incident_data["id"] = next_id
            incidents.append(incident_data)
            self.data["incidents"] = incidents
            
            self._save_json()
            return next_id
        else:
            cursor = self.db.cursor()
            try:
                # Начинаем транзакцию
                cursor.execute("BEGIN TRANSACTION")
                
                # Добавляем основную информацию об инциденте
                cursor.execute(
                    """
                    INSERT INTO security_incidents (
                        title, description, date_occurred, date_discovered, date_resolved,
                        severity, category_id, affected_systems, impact_description,
                        estimated_financial_impact, organizations_affected, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_data.get("title"),
                        incident_data.get("description"),
                        incident_data.get("date_occurred"),
                        incident_data.get("date_discovered"),
                        incident_data.get("date_resolved"),
                        incident_data.get("severity"),
                        incident_data.get("category_id"),
                        incident_data.get("affected_systems"),
                        incident_data.get("impact_description"),
                        incident_data.get("estimated_financial_impact"),
                        incident_data.get("organizations_affected"),
                        incident_data.get("source_url")
                    )
                )
                
                # Получаем ID добавленного инцидента
                incident_id = cursor.lastrowid
                
                # Добавляем теги
                for tag in incident_data.get("tags", []):
                    cursor.execute(
                        "INSERT INTO incident_tags (incident_id, tag) VALUES (?, ?)",
                        (incident_id, tag)
                    )
                
                # Добавляем техники MITRE ATT&CK
                for technique in incident_data.get("techniques", []):
                    cursor.execute(
                        """
                        INSERT INTO incident_techniques (incident_id, technique_id, description)
                        VALUES (?, ?, ?)
                        """,
                        (
                            incident_id,
                            technique.get("technique_id"),
                            technique.get("description")
                        )
                    )
                
                # Добавляем фазы инцидента
                for i, phase in enumerate(incident_data.get("phases", [])):
                    cursor.execute(
                        """
                        INSERT INTO incident_phases (incident_id, phase_name, description, order_index)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            incident_id,
                            phase.get("phase_name"),
                            phase.get("description"),
                            i
                        )
                    )
                
                # Добавляем извлеченные уроки
                for lesson in incident_data.get("lessons_learned", []):
                    cursor.execute(
                        """
                        INSERT INTO lessons_learned (incident_id, lesson, recommendation, priority)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            incident_id,
                            lesson.get("lesson"),
                            lesson.get("recommendation"),
                            lesson.get("priority")
                        )
                    )
                    
                    # Получаем ID добавленного урока
                    lesson_id = cursor.lastrowid
                    
                    # Добавляем корректирующие действия
                    for action in lesson.get("corrective_actions", []):
                        cursor.execute(
                            """
                            INSERT INTO corrective_actions (lesson_id, action, status)
                            VALUES (?, ?, ?)
                            """,
                            (
                                lesson_id,
                                action.get("action"),
                                action.get("status")
                            )
                        )
                
                # Добавляем регионы
                for region in incident_data.get("regions", []):
                    cursor.execute(
                        """
                        INSERT INTO incident_regions (incident_id, region, is_source)
                        VALUES (?, ?, ?)
                        """,
                        (
                            incident_id,
                            region.get("region"),
                            region.get("is_source", False)
                        )
                    )
                
                # Обновляем индекс поиска
                content = (
                    incident_data.get("title", "") + " " + 
                    incident_data.get("description", "") + " " + 
                    " ".join(incident_data.get("tags", []))
                )
                
                cursor.execute(
                    """
                    INSERT INTO incident_search_index (content, title, description, incident_id, date_occurred)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        content,
                        incident_data.get("title"),
                        incident_data.get("description"),
                        incident_id,
                        incident_data.get("date_occurred")
                    )
                )
                
                # Завершаем транзакцию
                self.db.commit()
                return incident_id
            except sqlite3.Error as e:
                self.db.rollback()
                raise Exception(f"Ошибка при добавлении инцидента: {e}")
    
    def get_incident(self, incident_id: int) -> Optional[Dict[str, Any]]:
        """
        Получение информации об инциденте по ID
        
        Args:
            incident_id: ID инцидента
            
        Returns:
            Данные об инциденте или None, если инцидент не найден
        """
        if self.storage_type == "json":
            incidents = self.data.get("incidents", [])
            for incident in incidents:
                if incident.get("id") == incident_id:
                    return incident
            return None
        else:
            cursor = self.db.cursor()
            try:
                # Получаем основную информацию об инциденте
                cursor.execute(
                    "SELECT * FROM security_incidents WHERE id = ?", 
                    (incident_id,)
                )
                incident = cursor.fetchone()
                
                if not incident:
                    return None
                
                incident_data = dict(incident)
                
                # Получаем категорию
                if incident_data.get("category_id"):
                    cursor.execute(
                        "SELECT * FROM incident_categories WHERE id = ?",
                        (incident_data.get("category_id"),)
                    )
                    category = cursor.fetchone()
                    if category:
                        incident_data["category"] = dict(category)
                
                # Получаем теги
                cursor.execute(
                    "SELECT tag FROM incident_tags WHERE incident_id = ?",
                    (incident_id,)
                )
                incident_data["tags"] = [row["tag"] for row in cursor.fetchall()]
                
                # Получаем техники MITRE ATT&CK
                cursor.execute(
                    "SELECT technique_id, description FROM incident_techniques WHERE incident_id = ?",
                    (incident_id,)
                )
                incident_data["techniques"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем фазы инцидента
                cursor.execute(
                    """
                    SELECT id, phase_name, description, order_index 
                    FROM incident_phases 
                    WHERE incident_id = ? 
                    ORDER BY order_index
                    """,
                    (incident_id,)
                )
                incident_data["phases"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем извлеченные уроки
                cursor.execute(
                    "SELECT * FROM lessons_learned WHERE incident_id = ?",
                    (incident_id,)
                )
                lessons = [dict(row) for row in cursor.fetchall()]
                
                # Для каждого урока получаем корректирующие действия
                for lesson in lessons:
                    cursor.execute(
                        "SELECT * FROM corrective_actions WHERE lesson_id = ?",
                        (lesson["id"],)
                    )
                    lesson["corrective_actions"] = [dict(row) for row in cursor.fetchall()]
                
                incident_data["lessons_learned"] = lessons
                
                # Получаем регионы
                cursor.execute(
                    "SELECT region, is_source FROM incident_regions WHERE incident_id = ?",
                    (incident_id,)
                )
                incident_data["regions"] = [dict(row) for row in cursor.fetchall()]
                
                return incident_data
            except sqlite3.Error as e:
                raise Exception(f"Ошибка при получении инцидента: {e}")

    def search_incidents(self, query: str = "", **filters) -> List[Dict[str, Any]]:
        """
        Поиск инцидентов по тексту и фильтрам
        
        Args:
            query: Текстовый поисковый запрос
            **filters: Дополнительные фильтры (category_id, severity, date_from, date_to, tags)
            
        Returns:
            Список найденных инцидентов
        """
        if self.storage_type == "json":
            incidents = self.data.get("incidents", [])
            results = []
            
            # Фильтрация по тексту
            if query:
                query_lower = query.lower()
                filtered_incidents = []
                for incident in incidents:
                    incident_text = json.dumps(incident, ensure_ascii=False).lower()
                    if query_lower in incident_text:
                        filtered_incidents.append(incident)
                incidents = filtered_incidents
            
            # Применение дополнительных фильтров
            for incident in incidents:
                match = True
                
                # Фильтр по категории
                if "category_id" in filters and filters["category_id"] is not None:
                    if incident.get("category_id") != filters["category_id"]:
                        match = False
                
                # Фильтр по критичности
                if "severity" in filters and filters["severity"]:
                    if incident.get("severity") != filters["severity"]:
                        match = False
                
                # Фильтр по дате (начиная с)
                if "date_from" in filters and filters["date_from"]:
                    if incident.get("date_occurred", "") < filters["date_from"]:
                        match = False
                
                # Фильтр по дате (до)
                if "date_to" in filters and filters["date_to"]:
                    if incident.get("date_occurred", "") > filters["date_to"]:
                        match = False
                
                # Фильтр по тегам
                if "tags" in filters and filters["tags"]:
                    incident_tags = incident.get("tags", [])
                    if not set(filters["tags"]).issubset(set(incident_tags)):
                        match = False
                
                if match:
                    results.append(incident)
            
            return results
        else:
            cursor = self.db.cursor()
            try:
                # Формируем базовый запрос
                base_query = """
                SELECT si.* 
                FROM security_incidents si
                """
                
                where_clauses = []
                params = []
                
                # Добавляем текстовый поиск
                if query:
                    base_query += " JOIN incident_search_index idx ON si.id = idx.incident_id"
                    where_clauses.append("idx.content MATCH ?")
                    # Подготовка запроса для полнотекстового поиска
                    search_query = ' '.join(f'"{word}"' for word in re.findall(r'\w+', query))
                    params.append(search_query)
                
                # Добавляем фильтры
                if "category_id" in filters and filters["category_id"] is not None:
                    where_clauses.append("si.category_id = ?")
                    params.append(filters["category_id"])
                
                if "severity" in filters and filters["severity"]:
                    where_clauses.append("si.severity = ?")
                    params.append(filters["severity"])
                
                if "date_from" in filters and filters["date_from"]:
                    where_clauses.append("si.date_occurred >= ?")
                    params.append(filters["date_from"])
                
                if "date_to" in filters and filters["date_to"]:
                    where_clauses.append("si.date_occurred <= ?")
                    params.append(filters["date_to"])
                
                # Фильтр по тегам (требует JOIN)
                if "tags" in filters and filters["tags"]:
                    tag_conditions = []
                    for tag in filters["tags"]:
                        base_query += f" JOIN incident_tags t{len(tag_conditions)} ON si.id = t{len(tag_conditions)}.incident_id"
                        tag_conditions.append(f"t{len(tag_conditions)-1}.tag = ?")
                        params.append(tag)
                    
                    where_clauses.extend(tag_conditions)
                
                # Формируем полный запрос
                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)
                
                base_query += " ORDER BY si.date_occurred DESC"
                
                # Выполняем запрос
                cursor.execute(base_query, params)
                incidents = [dict(row) for row in cursor.fetchall()]
                
                # Для каждого инцидента получаем дополнительную информацию
                results = []
                for incident in incidents:
                    results.append(self.get_incident(incident["id"]))
                
                return results
            except sqlite3.Error as e:
                raise Exception(f"Ошибка при поиске инцидентов: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по инцидентам
        
        Returns:
            Словарь со статистикой
        """
        if self.storage_type == "json":
            incidents = self.data.get("incidents", [])
            categories = self.data.get("categories", [])
            
            # Словарь для сопоставления ID категорий с их названиями
            category_names = {cat["id"]: cat["name"] for cat in categories}
            
            # Подсчет количества инцидентов по категориям
            category_stats = {}
            for incident in incidents:
                cat_id = incident.get("category_id")
                if cat_id is not None:
                    cat_name = category_names.get(cat_id, f"Категория {cat_id}")
                    category_stats[cat_name] = category_stats.get(cat_name, 0) + 1
            
            # Подсчет инцидентов по уровням критичности
            severity_stats = {}
            for incident in incidents:
                severity = incident.get("severity", "Unknown")
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
            
            # Подсчет инцидентов по годам и месяцам
            time_stats = {}
            for incident in incidents:
                date_str = incident.get("date_occurred", "")
                if date_str:
                    try:
                        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        year = date.year
                        month = date.month
                        
                        # Статистика по годам
                        if year not in time_stats:
                            time_stats[year] = {"total": 0, "months": {}}
                        
                        time_stats[year]["total"] += 1
                        
                        # Статистика по месяцам
                        if month not in time_stats[year]["months"]:
                            time_stats[year]["months"][month] = 0
                        
                        time_stats[year]["months"][month] += 1
                    except ValueError:
                        # Пропускаем некорректные даты
                        pass
            
            return {
                "total_incidents": len(incidents),
                "categories": category_stats,
                "severities": severity_stats,
                "time_distribution": time_stats
            }
        else:
            cursor = self.db.cursor()
            try:
                stats = {}
                
                # Общее количество инцидентов
                cursor.execute("SELECT COUNT(*) as count FROM security_incidents")
                stats["total_incidents"] = cursor.fetchone()["count"]
                
                # Статистика по категориям
                cursor.execute("""
                    SELECT c.name, COUNT(si.id) as count
                    FROM incident_categories c
                    LEFT JOIN security_incidents si ON c.id = si.category_id
                    GROUP BY c.id
                    ORDER BY count DESC
                """)
                stats["categories"] = {row["name"]: row["count"] for row in cursor.fetchall()}
                
                # Статистика по уровням критичности
                cursor.execute("""
                    SELECT severity, COUNT(*) as count
                    FROM security_incidents
                    GROUP BY severity
                    ORDER BY count DESC
                """)
                stats["severities"] = {row["severity"]: row["count"] for row in cursor.fetchall()}
                
                # Статистика по времени (годам и месяцам)
                cursor.execute("""
                    SELECT 
                        strftime('%Y', date_occurred) as year,
                        strftime('%m', date_occurred) as month,
                        COUNT(*) as count
                    FROM security_incidents
                    WHERE date_occurred IS NOT NULL
                    GROUP BY year, month
                    ORDER BY year, month
                """)
                
                time_stats = {}
                for row in cursor.fetchall():
                    year = int(row["year"])
                    month = int(row["month"])
                    count = row["count"]
                    
                    if year not in time_stats:
                        time_stats[year] = {"total": 0, "months": {}}
                    
                    time_stats[year]["total"] += count
                    time_stats[year]["months"][month] = count
                
                stats["time_distribution"] = time_stats
                
                # Наиболее распространенные теги
                cursor.execute("""
                    SELECT tag, COUNT(*) as count
                    FROM incident_tags
                    GROUP BY tag
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats["top_tags"] = {row["tag"]: row["count"] for row in cursor.fetchall()}
                
                return stats
            except sqlite3.Error as e:
                raise Exception(f"Ошибка при получении статистики: {e}")
    
    def update_incident(self, incident_id: int, incident_data: Dict[str, Any]) -> bool:
        """
        Обновление данных инцидента
        
        Args:
            incident_id: ID инцидента
            incident_data: Новые данные об инциденте
            
        Returns:
            True, если инцидент успешно обновлен, иначе False
        """
        if self.storage_type == "json":
            incidents = self.data.get("incidents", [])
            for i, incident in enumerate(incidents):
                if incident.get("id") == incident_id:
                    # Обновляем инцидент, сохраняя его ID
                    incident_data["id"] = incident_id
                    incidents[i] = incident_data
                    self.data["incidents"] = incidents
                    self._save_json()
                    return True
            return False
        else:
            # Для SQLite удаляем и повторно добавляем инцидент с тем же ID
            cursor = self.db.cursor()
            try:
                # Проверяем существование инцидента
                cursor.execute("SELECT id FROM security_incidents WHERE id = ?", (incident_id,))
                if not cursor.fetchone():
                    return False
                
                # Начинаем транзакцию
                cursor.execute("BEGIN TRANSACTION")
                
                # Удаляем старые данные (каскадное удаление дочерних записей)
                cursor.execute("DELETE FROM security_incidents WHERE id = ?", (incident_id,))
                
                # Устанавливаем ID инцидента
                incident_data["id"] = incident_id
                
                # Добавляем обновленные данные
                cursor.execute(
                    """
                    INSERT INTO security_incidents (
                        id, title, description, date_occurred, date_discovered, date_resolved,
                        severity, category_id, affected_systems, impact_description,
                        estimated_financial_impact, organizations_affected, source_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        incident_data.get("title"),
                        incident_data.get("description"),
                        incident_data.get("date_occurred"),
                        incident_data.get("date_discovered"),
                        incident_data.get("date_resolved"),
                        incident_data.get("severity"),
                        incident_data.get("category_id"),
                        incident_data.get("affected_systems"),
                        incident_data.get("impact_description"),
                        incident_data.get("estimated_financial_impact"),
                        incident_data.get("organizations_affected"),
                        incident_data.get("source_url")
                    )
                )
                
                # Добавляем теги
                for tag in incident_data.get("tags", []):
                    cursor.execute(
                        "INSERT INTO incident_tags (incident_id, tag) VALUES (?, ?)",
                        (incident_id, tag)
                    )
                
                # Добавляем техники MITRE ATT&CK
                for technique in incident_data.get("techniques", []):
                    cursor.execute(
                        """
                        INSERT INTO incident_techniques (incident_id, technique_id, description)
                        VALUES (?, ?, ?)
                        """,
                        (
                            incident_id,
                            technique.get("technique_id"),
                            technique.get("description")
                        )
                    )
                
                # Добавляем фазы инцидента
                for i, phase in enumerate(incident_data.get("phases", [])):
                    cursor.execute(
                        """
                        INSERT INTO incident_phases (incident_id, phase_name, description, order_index)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            incident_id,
                            phase.get("phase_name"),
                            phase.get("description"),
                            i
                        )
                    )
                
                # Добавляем извлеченные уроки
                for lesson in incident_data.get("lessons_learned", []):
                    cursor.execute(
                        """
                        INSERT INTO lessons_learned (incident_id, lesson, recommendation, priority)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            incident_id,
                            lesson.get("lesson"),
                            lesson.get("recommendation"),
                            lesson.get("priority")
                        )
                    )
                    
                    # Получаем ID добавленного урока
                    lesson_id = cursor.lastrowid
                    
                    # Добавляем корректирующие действия
                    for action in lesson.get("corrective_actions", []):
                        cursor.execute(
                            """
                            INSERT INTO corrective_actions (lesson_id, action, status)
                            VALUES (?, ?, ?)
                            """,
                            (
                                lesson_id,
                                action.get("action"),
                                action.get("status")
                            )
                        )
                
                # Добавляем регионы
                for region in incident_data.get("regions", []):
                    cursor.execute(
                        """
                        INSERT INTO incident_regions (incident_id, region, is_source)
                        VALUES (?, ?, ?)
                        """,
                        (
                            incident_id,
                            region.get("region"),
                            region.get("is_source", False)
                        )
                    )
                
                # Обновляем индекс поиска
                content = (
                    incident_data.get("title", "") + " " + 
                    incident_data.get("description", "") + " " + 
                    " ".join(incident_data.get("tags", []))
                )
                
                cursor.execute("DELETE FROM incident_search_index WHERE incident_id = ?", (incident_id,))
                cursor.execute(
                    """
                    INSERT INTO incident_search_index (content, title, description, incident_id, date_occurred)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        content,
                        incident_data.get("title"),
                        incident_data.get("description"),
                        incident_id,
                        incident_data.get("date_occurred")
                    )
                )
                
                # Завершаем транзакцию
                self.db.commit()
                return True
            except sqlite3.Error as e:
                self.db.rollback()
                print(f"Ошибка при обновлении инцидента: {e}")
                return False
    
    def remove_incident(self, incident_id: int) -> bool:
        """
        Удаление инцидента
        
        Args:
            incident_id: ID инцидента
            
        Returns:
            True, если инцидент успешно удален, иначе False
        """
        if self.storage_type == "json":
            incidents = self.data.get("incidents", [])
            for i, incident in enumerate(incidents):
                if incident.get("id") == incident_id:
                    incidents.pop(i)
                    self.data["incidents"] = incidents
                    self._save_json()
                    return True
            return False
        else:
            cursor = self.db.cursor()
            try:
                cursor.execute("DELETE FROM security_incidents WHERE id = ?", (incident_id,))
                self.db.commit()
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                self.db.rollback()
                print(f"Ошибка при удалении инцидента: {e}")
                return False
