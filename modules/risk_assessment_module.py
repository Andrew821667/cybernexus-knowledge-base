#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль оценки рисков для базы знаний по кибербезопасности
Позволяет добавлять, получать и анализировать оценки рисков для угроз
"""

import json
import sqlite3
import os
import math
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Tuple, Set


class RiskLevel(Enum):
    """Уровни риска для классификации угроз"""
    LOW = "Низкий"
    MEDIUM = "Средний"
    HIGH = "Высокий"
    CRITICAL = "Критический"


class RiskAssessmentModule:
    """Модуль для оценки рисков угроз в базе знаний"""
    
    def __init__(self, kb_accessor):
        """
        Инициализация модуля оценки рисков
        
        Args:
            kb_accessor: Экземпляр KnowledgeBaseAccessor для доступа к базе знаний
        """
        self.kb_accessor = kb_accessor
        self.storage_type = kb_accessor.storage_type
        
        # Создаем необходимые таблицы, если используется SQLite
        if self.storage_type == "sqlite":
            self._create_risk_tables()
    
    def _create_risk_tables(self):
        """Создание таблиц для оценки рисков в SQLite"""
        cursor = self.kb_accessor.db.cursor()
        
        # Проверка наличия таблицы risk_assessments
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_assessments'")
        if not cursor.fetchone():
            # Создаем таблицу оценки рисков
            cursor.execute("""
                CREATE TABLE risk_assessments (
                    id INTEGER PRIMARY KEY,
                    threat_id INTEGER NOT NULL,
                    probability REAL NOT NULL,                -- Вероятность реализации угрозы (0-1)
                    impact REAL NOT NULL,                     -- Влияние/ущерб от угрозы (0-1)
                    exploitation_complexity REAL NOT NULL,    -- Сложность эксплуатации (0-1, где 0 - очень сложно)
                    base_score REAL NOT NULL,                 -- Базовая оценка риска
                    last_updated DATE NOT NULL,               -- Дата последнего обновления
                    assessor TEXT,                            -- Кто проводил оценку
                    notes TEXT,                               -- Примечания к оценке
                    FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
                )
            """)
            
            # Создаем таблицу для факторов влияния на риск
            cursor.execute("""
                CREATE TABLE risk_factors (
                    id INTEGER PRIMARY KEY,
                    assessment_id INTEGER NOT NULL,
                    factor_name TEXT NOT NULL,                -- Название фактора
                    factor_value REAL NOT NULL,               -- Значение фактора (коэффициент)
                    factor_description TEXT,                  -- Описание фактора
                    FOREIGN KEY (assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE
                )
            """)
            
            # Создаем таблицу для мер снижения риска
            cursor.execute("""
                CREATE TABLE risk_mitigations (
                    id INTEGER PRIMARY KEY,
                    assessment_id INTEGER NOT NULL,
                    mitigation_name TEXT NOT NULL,            -- Название меры
                    effectiveness REAL NOT NULL,              -- Эффективность меры (0-1)
                    implementation_status TEXT,               -- Статус внедрения
                    implementation_cost TEXT,                 -- Стоимость внедрения
                    mitigation_description TEXT,              -- Описание меры
                    FOREIGN KEY (assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE
                )
            """)
            
            # Индексы для оптимизации запросов
            cursor.execute("CREATE INDEX idx_risk_assessments_threat_id ON risk_assessments(threat_id)")
            cursor.execute("CREATE INDEX idx_risk_factors_assessment_id ON risk_factors(assessment_id)")
            cursor.execute("CREATE INDEX idx_risk_mitigations_assessment_id ON risk_mitigations(assessment_id)")
            
            self.kb_accessor.db.commit()
            print("Таблицы для оценки рисков успешно созданы")
    
    def add_risk_assessment(self, threat_id: int, assessment_data: Dict[str, Any]) -> int:
        """
        Добавление оценки риска для угрозы
        
        Args:
            threat_id: ID угрозы
            assessment_data: Данные оценки риска, включающие:
                - probability: Вероятность реализации угрозы (0-1)
                - impact: Влияние/ущерб от угрозы (0-1)
                - exploitation_complexity: Сложность эксплуатации (0-1, где 0 - очень сложно)
                - last_updated: Дата последнего обновления (строка в формате YYYY-MM-DD)
                - assessor: Кто проводил оценку
                - notes: Примечания к оценке
                - factors: Список факторов влияния на риск (опционально)
                - mitigations: Список мер снижения риска (опционально)
        
        Returns:
            ID добавленной оценки риска
        """
        # Проверка существования угрозы
        if not self._threat_exists(threat_id):
            raise ValueError(f"Угроза с ID {threat_id} не найдена")
        
        # Проверка обязательных полей
        required_fields = ["probability", "impact", "exploitation_complexity", "last_updated"]
        for field in required_fields:
            if field not in assessment_data:
                raise ValueError(f"Отсутствует обязательное поле: {field}")
        
        # Валидация значений
        if not 0 <= assessment_data["probability"] <= 1:
            raise ValueError("Вероятность должна быть в диапазоне [0, 1]")
        if not 0 <= assessment_data["impact"] <= 1:
            raise ValueError("Влияние должно быть в диапазоне [0, 1]")
        if not 0 <= assessment_data["exploitation_complexity"] <= 1:
            raise ValueError("Сложность эксплуатации должна быть в диапазоне [0, 1]")
        
        # Расчет базовой оценки риска
        base_score = self._calculate_base_score(
            assessment_data["probability"],
            assessment_data["impact"],
            assessment_data["exploitation_complexity"]
        )
        
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            try:
                # Добавляем основную оценку риска
                cursor.execute("""
                    INSERT INTO risk_assessments 
                    (threat_id, probability, impact, exploitation_complexity, base_score, last_updated, assessor, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    threat_id,
                    assessment_data["probability"],
                    assessment_data["impact"],
                    assessment_data["exploitation_complexity"],
                    base_score,
                    assessment_data["last_updated"],
                    assessment_data.get("assessor", ""),
                    assessment_data.get("notes", "")
                ))
                
                # Получаем ID добавленной оценки
                assessment_id = cursor.lastrowid
                
                # Добавляем факторы влияния на риск
                for factor in assessment_data.get("factors", []):
                    cursor.execute("""
                        INSERT INTO risk_factors
                        (assessment_id, factor_name, factor_value, factor_description)
                        VALUES (?, ?, ?, ?)
                    """, (
                        assessment_id,
                        factor["name"],
                        factor["value"],
                        factor.get("description", "")
                    ))
                
                # Добавляем меры снижения риска
                for mitigation in assessment_data.get("mitigations", []):
                    cursor.execute("""
                        INSERT INTO risk_mitigations
                        (assessment_id, mitigation_name, effectiveness, implementation_status, implementation_cost, mitigation_description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        assessment_id,
                        mitigation["name"],
                        mitigation["effectiveness"],
                        mitigation.get("implementation_status", ""),
                        mitigation.get("implementation_cost", ""),
                        mitigation.get("description", "")
                    ))
                
                self.kb_accessor.db.commit()
                return assessment_id
                
            except Exception as e:
                self.kb_accessor.db.rollback()
                raise e
                
        else:  # JSON storage
            # Находим и обновляем информацию об угрозе в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        # Ищем подраздел с угрозами
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Находим нужную угрозу по ID
                            if threat_data.get("id") == threat_id:
                                # Создаем структуру для оценки риска
                                assessment = {
                                    "probability": assessment_data["probability"],
                                    "impact": assessment_data["impact"],
                                    "exploitation_complexity": assessment_data["exploitation_complexity"],
                                    "base_score": base_score,
                                    "last_updated": assessment_data["last_updated"],
                                    "assessor": assessment_data.get("assessor", ""),
                                    "notes": assessment_data.get("notes", "")
                                }
                                
                                # Добавляем факторы и меры, если они есть
                                if "factors" in assessment_data:
                                    assessment["factors"] = assessment_data["factors"]
                                if "mitigations" in assessment_data:
                                    assessment["mitigations"] = assessment_data["mitigations"]
                                
                                # Добавляем оценку риска к угрозе
                                if "risk_assessment" not in threat_data:
                                    threat_data["risk_assessment"] = []
                                
                                # Генерируем ID для оценки
                                assessment_id = len(threat_data["risk_assessment"]) + 1
                                assessment["id"] = assessment_id
                                
                                threat_data["risk_assessment"].append(assessment)
                                
                                # Сохраняем изменения
                                self.kb_accessor._save_json()
                                return assessment_id
            
            raise ValueError(f"Не удалось найти угрозу с ID {threat_id} в базе знаний")
    
    def get_risk_assessment(self, assessment_id: int) -> Dict[str, Any]:
        """
        Получение данных оценки риска по ID
        
        Args:
            assessment_id: ID оценки риска
            
        Returns:
            Словарь с данными оценки риска
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            # Получаем основные данные оценки
            cursor.execute("""
                SELECT * FROM risk_assessments WHERE id = ?
            """, (assessment_id,))
            
            assessment = cursor.fetchone()
            if not assessment:
                raise ValueError(f"Оценка риска с ID {assessment_id} не найдена")
            
            result = dict(assessment)
            
            # Получаем факторы влияния
            cursor.execute("""
                SELECT * FROM risk_factors WHERE assessment_id = ?
            """, (assessment_id,))
            
            result["factors"] = [dict(row) for row in cursor.fetchall()]
            
            # Получаем меры снижения риска
            cursor.execute("""
                SELECT * FROM risk_mitigations WHERE assessment_id = ?
            """, (assessment_id,))
            
            result["mitigations"] = [dict(row) for row in cursor.fetchall()]
            
            # Получаем данные о связанной угрозе
            cursor.execute("""
                SELECT t.* FROM threat_types t
                JOIN risk_assessments r ON t.id = r.threat_id
                WHERE r.id = ?
            """, (assessment_id,))
            
            threat = cursor.fetchone()
            if threat:
                result["threat"] = dict(threat)
            
            return result
            
        else:  # JSON storage
            # Ищем оценку риска в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Проверяем наличие оценок риска для этой угрозы
                            if "risk_assessment" in threat_data:
                                for assessment in threat_data["risk_assessment"]:
                                    if assessment.get("id") == assessment_id:
                                        # Копируем данные оценки
                                        result = assessment.copy()
                                        # Добавляем информацию об угрозе
                                        result["threat"] = {
                                            "id": threat_data.get("id"),
                                            "name": threat_data.get("name", ""),
                                            "definition": threat_data.get("definition", "")
                                        }
                                        return result
            
            raise ValueError(f"Оценка риска с ID {assessment_id} не найдена")
    
    def update_risk_assessment(self, assessment_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Обновление данных оценки риска
        
        Args:
            assessment_id: ID оценки риска
            update_data: Данные для обновления
            
        Returns:
            True, если обновление выполнено успешно
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            # Проверяем существование оценки
            cursor.execute("SELECT id FROM risk_assessments WHERE id = ?", (assessment_id,))
            if not cursor.fetchone():
                raise ValueError(f"Оценка риска с ID {assessment_id} не найдена")
            
            try:
                # Формируем SQL для обновления основных полей
                update_fields = []
                update_values = []
                
                # Список полей, доступных для обновления
                updatable_fields = [
                    "probability", "impact", "exploitation_complexity", 
                    "last_updated", "assessor", "notes"
                ]
                
                # Добавляем поля, которые нужно обновить
                for field in updatable_fields:
                    if field in update_data:
                        update_fields.append(f"{field} = ?")
                        update_values.append(update_data[field])
                
                # Если есть поля для обновления оценки риска
                if update_fields:
                    # Если изменились параметры, влияющие на базовую оценку, пересчитываем её
                    recalculate_base_score = any(
                        field in update_data for field in ["probability", "impact", "exploitation_complexity"]
                    )
                    
                    if recalculate_base_score:
                        # Получаем текущие значения
                        cursor.execute(
                            """
                            SELECT probability, impact, exploitation_complexity 
                            FROM risk_assessments WHERE id = ?
                            """, 
                            (assessment_id,)
                        )
                        current_values = cursor.fetchone()
                        
                        # Обновляем значения из переданных данных
                        probability = update_data.get("probability", current_values["probability"])
                        impact = update_data.get("impact", current_values["impact"])
                        exploitation_complexity = update_data.get(
                            "exploitation_complexity", 
                            current_values["exploitation_complexity"]
                        )
                        
                        # Рассчитываем новую базовую оценку
                        base_score = self._calculate_base_score(probability, impact, exploitation_complexity)
                        
                        # Добавляем обновление базовой оценки
                        update_fields.append("base_score = ?")
                        update_values.append(base_score)
                    
                    # Выполняем обновление основных данных
                    query = f"""
                        UPDATE risk_assessments 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    """
                    update_values.append(assessment_id)
                    
                    cursor.execute(query, tuple(update_values))
                
                # Обновляем факторы влияния, если они предоставлены
                if "factors" in update_data:
                    # Удаляем существующие факторы
                    cursor.execute(
                        "DELETE FROM risk_factors WHERE assessment_id = ?", 
                        (assessment_id,)
                    )
                    
                    # Добавляем новые факторы
                    for factor in update_data["factors"]:
                        cursor.execute(
                            """
                            INSERT INTO risk_factors
                            (assessment_id, factor_name, factor_value, factor_description)
                            VALUES (?, ?, ?, ?)
                            """, 
                            (
                                assessment_id,
                                factor["name"],
                                factor["value"],
                                factor.get("description", "")
                            )
                        )
                
                # Обновляем меры снижения риска, если они предоставлены
                if "mitigations" in update_data:
                    # Удаляем существующие меры
                    cursor.execute(
                        "DELETE FROM risk_mitigations WHERE assessment_id = ?", 
                        (assessment_id,)
                    )
                    
                    # Добавляем новые меры
                    for mitigation in update_data["mitigations"]:
                        cursor.execute(
                            """
                            INSERT INTO risk_mitigations
                            (assessment_id, mitigation_name, effectiveness, implementation_status, implementation_cost, mitigation_description)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, 
                            (
                                assessment_id,
                                mitigation["name"],
                                mitigation["effectiveness"],
                                mitigation.get("implementation_status", ""),
                                mitigation.get("implementation_cost", ""),
                                mitigation.get("description", "")
                            )
                        )
                
                self.kb_accessor.db.commit()
                return True
                
            except Exception as e:
                self.kb_accessor.db.rollback()
                raise e
                
        else:  # JSON storage
            # Ищем оценку риска в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Проверяем наличие оценок риска для этой угрозы
                            if "risk_assessment" in threat_data:
                                for i, assessment in enumerate(threat_data["risk_assessment"]):
                                    if assessment.get("id") == assessment_id:
                                        # Обновляем данные оценки
                                        for key, value in update_data.items():
                                            if key != "id":  # ID не обновляем
                                                assessment[key] = value
                                        
                                        # Если изменились параметры, влияющие на базовую оценку, пересчитываем её
                                        if any(field in update_data for field in ["probability", "impact", "exploitation_complexity"]):
                                            assessment["base_score"] = self._calculate_base_score(
                                                assessment["probability"],
                                                assessment["impact"],
                                                assessment["exploitation_complexity"]
                                            )
                                        
                                        # Сохраняем изменения
                                        self.kb_accessor._save_json()
                                        return True
            
            raise ValueError(f"Оценка риска с ID {assessment_id} не найдена")
    
    def delete_risk_assessment(self, assessment_id: int) -> bool:
        """
        Удаление оценки риска
        
        Args:
            assessment_id: ID оценки риска
            
        Returns:
            True, если удаление выполнено успешно
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            try:
                # Проверяем существование оценки
                cursor.execute("SELECT id FROM risk_assessments WHERE id = ?", (assessment_id,))
                if not cursor.fetchone():
                    raise ValueError(f"Оценка риска с ID {assessment_id} не найдена")
                
                # Удаляем оценку (факторы и меры будут удалены каскадно благодаря внешним ключам)
                cursor.execute("DELETE FROM risk_assessments WHERE id = ?", (assessment_id,))
                self.kb_accessor.db.commit()
                
                return True
                
            except Exception as e:
                self.kb_accessor.db.rollback()
                raise e
                
        else:  # JSON storage
            # Ищем оценку риска в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Проверяем наличие оценок риска для этой угрозы
                            if "risk_assessment" in threat_data:
                                for i, assessment in enumerate(threat_data["risk_assessment"]):
                                    if assessment.get("id") == assessment_id:
                                        # Удаляем оценку
                                        threat_data["risk_assessment"].pop(i)
                                        
                                        # Сохраняем изменения
                                        self.kb_accessor._save_json()
                                        return True
            
            raise ValueError(f"Оценка риска с ID {assessment_id} не найдена")
    
    def get_threat_risk_assessments(self, threat_id: int) -> List[Dict[str, Any]]:
        """
        Получение всех оценок риска для конкретной угрозы
        
        Args:
            threat_id: ID угрозы
            
        Returns:
            Список словарей с данными оценок риска
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            # Проверяем существование угрозы
            if not self._threat_exists(threat_id):
                raise ValueError(f"Угроза с ID {threat_id} не найдена")
            
            # Получаем основные данные оценок
            cursor.execute("""
                SELECT * FROM risk_assessments WHERE threat_id = ? ORDER BY last_updated DESC
            """, (threat_id,))
            
            assessments = [dict(row) for row in cursor.fetchall()]
            
            # Для каждой оценки добавляем факторы и меры
            for assessment in assessments:
                assessment_id = assessment["id"]
                
                # Получаем факторы влияния
                cursor.execute("""
                    SELECT * FROM risk_factors WHERE assessment_id = ?
                """, (assessment_id,))
                
                assessment["factors"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем меры снижения риска
                cursor.execute("""
                    SELECT * FROM risk_mitigations WHERE assessment_id = ?
                """, (assessment_id,))
                
                assessment["mitigations"] = [dict(row) for row in cursor.fetchall()]
            
            return assessments
            
        else:  # JSON storage
            # Ищем угрозу в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Находим угрозу по ID
                            if threat_data.get("id") == threat_id:
                                # Возвращаем все оценки риска для этой угрозы
                                return threat_data.get("risk_assessment", [])
            
            raise ValueError(f"Угроза с ID {threat_id} не найдена")
    
    def get_high_risk_threats(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Получение списка угроз с высоким уровнем риска
        
        Args:
            risk_threshold: Порог риска (от 0 до 1), выше которого угроза считается высокорисковой
            
        Returns:
            Список словарей с данными угроз и их оценками риска
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            # Получаем угрозы с высоким уровнем риска
            cursor.execute("""
                SELECT t.*, r.* 
                FROM threat_types t
                JOIN risk_assessments r ON t.id = r.threat_id
                WHERE r.base_score >= ?
                ORDER BY r.base_score DESC
            """, (risk_threshold,))
            
            threats = []
            rows = cursor.fetchall()
            
            # Группируем данные по угрозам
            threat_ids = set()
            for row in rows:
                row_dict = dict(row)
                threat_id = row_dict["id"]
                
                if threat_id not in threat_ids:
                    threat_ids.add(threat_id)
                    
                    # Базовая информация об угрозе
                    threat = {
                        "id": threat_id,
                        "name": row_dict["name"],
                        "definition": row_dict["definition"],
                        "assessments": []
                    }
                    
                    # Добавляем все оценки для этой угрозы
                    threat_assessments = self.get_threat_risk_assessments(threat_id)
                    threat["assessments"] = threat_assessments
                    
                    threats.append(threat)
            
            return threats
            
        else:  # JSON storage
            high_risk_threats = []
            
            # Ищем угрозы с высоким уровнем риска в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Проверяем наличие оценок риска
                            if "risk_assessment" in threat_data:
                                # Ищем оценки с высоким уровнем риска
                                high_risk_assessments = [
                                    assessment for assessment in threat_data["risk_assessment"]
                                    if assessment.get("base_score", 0) >= risk_threshold
                                ]
                                
                                if high_risk_assessments:
                                    # Добавляем угрозу в результат
                                    threat = {
                                        "id": threat_data.get("id"),
                                        "name": threat_data.get("name", ""),
                                        "definition": threat_data.get("definition", ""),
                                        "assessments": high_risk_assessments
                                    }
                                    high_risk_threats.append(threat)
            
            # Сортируем по максимальной оценке риска (по убыванию)
            high_risk_threats.sort(
                key=lambda t: max(a.get("base_score", 0) for a in t["assessments"]),
                reverse=True
            )
            
            return high_risk_threats
    
    def calculate_risk_matrix(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Формирование матрицы рисков по вероятности и влиянию
        
        Returns:
            Словарь с категориями риска и списками угроз
        """
        # Получаем все оценки рисков
        all_assessments = self._get_all_risk_assessments()
        
        # Разбиваем по категориям риска
        risk_matrix = {
            "critical": [],  # Критический риск (высокая вероятность, высокое влияние)
            "high": [],      # Высокий риск
            "medium": [],    # Средний риск
            "low": []        # Низкий риск
        }
        
        # Пороговые значения для категорий
        prob_threshold = 0.5  # Порог вероятности
        impact_threshold = 0.5  # Порог влияния
        
        for assessment in all_assessments:
            probability = assessment.get("probability", 0)
            impact = assessment.get("impact", 0)
            
            # Определяем категорию риска
            if probability >= prob_threshold and impact >= impact_threshold:
                risk_matrix["critical"].append(assessment)
            elif probability >= prob_threshold:
                risk_matrix["high"].append(assessment)
            elif impact >= impact_threshold:
                risk_matrix["medium"].append(assessment)
            else:
                risk_matrix["low"].append(assessment)
        
        return risk_matrix
    
    def generate_risk_report(self, format: str = "text") -> str:
        """
        Генерация отчета по оценке рисков
        
        Args:
            format: Формат отчета ("text", "html" или "json")
            
        Returns:
            Строка с отчетом в указанном формате
        """
        # Получаем данные для отчета
        all_assessments = self._get_all_risk_assessments()
        risk_matrix = self.calculate_risk_matrix()
        
        if format == "json":
            # Формируем отчет в JSON формате
            report = {
                "generated_at": self._get_current_date(),
                "total_threats_assessed": len(set(a.get("threat_id") for a in all_assessments)),
                "total_assessments": len(all_assessments),
                "risk_distribution": {
                    "critical": len(risk_matrix["critical"]),
                    "high": len(risk_matrix["high"]),
                    "medium": len(risk_matrix["medium"]),
                    "low": len(risk_matrix["low"])
                },
                "risk_matrix": risk_matrix,
                "high_risk_threats": self.get_high_risk_threats(0.7)
            }
            
            return json.dumps(report, ensure_ascii=False, indent=2)
            
        elif format == "html":
            # Формируем отчет в HTML формате
            html = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                "    <meta charset='utf-8'>",
                "    <title>Отчет по оценке рисков</title>",
                "    <style>",
                "        body { font-family: Arial, sans-serif; margin: 20px; }",
                "        h1, h2 { color: #333366; }",
                "        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }",
                "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
                "        th { background-color: #f2f2f2; }",
                "        .critical { background-color: #ffdddd; }",
                "        .high { background-color: #ffffcc; }",
                "        .medium { background-color: #e6f3ff; }",
                "        .low { background-color: #eeffee; }",
                "    </style>",
                "</head>",
                "<body>",
                f"    <h1>Отчет по оценке рисков</h1>",
                f"    <p>Дата формирования: {self._get_current_date()}</p>",
                f"    <p>Всего оценено угроз: {len(set(a.get('threat_id') for a in all_assessments))}</p>",
                f"    <p>Всего оценок: {len(all_assessments)}</p>",
                "    <h2>Распределение рисков</h2>",
                "    <table>",
                "        <tr>",
                "            <th>Уровень риска</th>",
                "            <th>Количество</th>",
                "        </tr>",
                f"        <tr class='critical'><td>Критический</td><td>{len(risk_matrix['critical'])}</td></tr>",
                f"        <tr class='high'><td>Высокий</td><td>{len(risk_matrix['high'])}</td></tr>",
                f"        <tr class='medium'><td>Средний</td><td>{len(risk_matrix['medium'])}</td></tr>",
                f"        <tr class='low'><td>Низкий</td><td>{len(risk_matrix['low'])}</td></tr>",
                "    </table>"
            ]
            
            # Добавляем таблицу с высокорисковыми угрозами
            high_risk_threats = self.get_high_risk_threats(0.7)
            if high_risk_threats:
                html.extend([
                    "    <h2>Высокорисковые угрозы</h2>",
                    "    <table>",
                    "        <tr>",
                    "            <th>Название угрозы</th>",
                    "            <th>Оценка риска</th>",
                    "            <th>Вероятность</th>",
                    "            <th>Влияние</th>",
                    "            <th>Дата оценки</th>",
                    "        </tr>"
                ])
                
                for threat in high_risk_threats:
                    # Берем оценку с наивысшим риском для каждой угрозы
                    assessment = max(threat["assessments"], key=lambda a: a.get("base_score", 0))
                    html.append(f"        <tr class='critical'>")
                    html.append(f"            <td>{threat['name']}</td>")
                    html.append(f"            <td>{assessment.get('base_score', 0):.2f}</td>")
                    html.append(f"            <td>{assessment.get('probability', 0):.2f}</td>")
                    html.append(f"            <td>{assessment.get('impact', 0):.2f}</td>")
                    html.append(f"            <td>{assessment.get('last_updated', '')}</td>")
                    html.append(f"        </tr>")
                
                html.append("    </table>")
            
            html.extend([
                "</body>",
                "</html>"
            ])
            
            return "\n".join(html)
            
        else:  # Text format (default)
            # Формируем отчет в текстовом формате
            lines = [
                "ОТЧЕТ ПО ОЦЕНКЕ РИСКОВ",
                "=" * 50,
                f"Дата формирования: {self._get_current_date()}",
                f"Всего оценено угроз: {len(set(a.get('threat_id') for a in all_assessments))}",
                f"Всего оценок: {len(all_assessments)}",
                "",
                "РАСПРЕДЕЛЕНИЕ РИСКОВ",
                "-" * 50,
                f"Критический риск: {len(risk_matrix['critical'])}",
                f"Высокий риск: {len(risk_matrix['high'])}",
                f"Средний риск: {len(risk_matrix['medium'])}",
                f"Низкий риск: {len(risk_matrix['low'])}",
                ""
            ]
            
            # Добавляем информацию о высокорисковых угрозах
            high_risk_threats = self.get_high_risk_threats(0.7)
            if high_risk_threats:
                lines.extend([
                    "ВЫСОКОРИСКОВЫЕ УГРОЗЫ",
                    "-" * 50
                ])
                
                for threat in high_risk_threats:
                    # Берем оценку с наивысшим риском для каждой угрозы
                    assessment = max(threat["assessments"], key=lambda a: a.get("base_score", 0))
                    lines.extend([
                        f"Название: {threat['name']}",
                        f"Описание: {threat['definition'][:100]}...",
                        f"Оценка риска: {assessment.get('base_score', 0):.2f}",
                        f"Вероятность: {assessment.get('probability', 0):.2f}",
                        f"Влияние: {assessment.get('impact', 0):.2f}",
                        f"Дата оценки: {assessment.get('last_updated', '')}",
                        "-" * 30
                    ])
            
            return "\n".join(lines)
    
    def _calculate_base_score(self, probability: float, impact: float, exploitation_complexity: float) -> float:
        """
        Расчет базовой оценки риска
        
        Args:
            probability: Вероятность реализации угрозы (0-1)
            impact: Влияние/ущерб от угрозы (0-1)
            exploitation_complexity: Сложность эксплуатации (0-1, где 0 - очень сложно)
            
        Returns:
            Базовая оценка риска (0-1)
        """
        # Инвертируем сложность эксплуатации (чем сложнее, тем ниже риск)
        ease_of_exploitation = 1 - exploitation_complexity
        
        # Формула расчета базовой оценки риска
        # Вес вероятности - 0.4, веса влияния - 0.4, вес простоты эксплуатации - 0.2
        base_score = 0.4 * probability + 0.4 * impact + 0.2 * ease_of_exploitation
        
        return base_score
    
    def _get_all_risk_assessments(self) -> List[Dict[str, Any]]:
        """
        Получение всех оценок рисков из базы данных
        
        Returns:
            Список словарей с данными оценок риска
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            
            # Получаем все оценки рисков с данными об угрозах
            cursor.execute("""
                SELECT r.*, t.name as threat_name, t.definition as threat_definition
                FROM risk_assessments r
                JOIN threat_types t ON r.threat_id = t.id
                ORDER BY r.base_score DESC
            """)
            
            assessments = [dict(row) for row in cursor.fetchall()]
            
            # Для каждой оценки добавляем факторы и меры
            for assessment in assessments:
                assessment_id = assessment["id"]
                
                # Получаем факторы влияния
                cursor.execute("""
                    SELECT * FROM risk_factors WHERE assessment_id = ?
                """, (assessment_id,))
                
                assessment["factors"] = [dict(row) for row in cursor.fetchall()]
                
                # Получаем меры снижения риска
                cursor.execute("""
                    SELECT * FROM risk_mitigations WHERE assessment_id = ?
                """, (assessment_id,))
                
                assessment["mitigations"] = [dict(row) for row in cursor.fetchall()]
            
            return assessments
            
        else:  # JSON storage
            all_assessments = []
            
            # Собираем все оценки рисков из JSON структуры
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            # Проверяем наличие оценок риска
                            if "risk_assessment" in threat_data:
                                for assessment in threat_data["risk_assessment"]:
                                    # Добавляем данные об угрозе к оценке
                                    assessment_with_threat = assessment.copy()
                                    assessment_with_threat["threat_id"] = threat_data.get("id")
                                    assessment_with_threat["threat_name"] = threat_data.get("name", "")
                                    assessment_with_threat["threat_definition"] = threat_data.get("definition", "")
                                    
                                    all_assessments.append(assessment_with_threat)
            
            # Сортируем по оценке риска (по убыванию)
            all_assessments.sort(key=lambda a: a.get("base_score", 0), reverse=True)
            
            return all_assessments
    
    def _threat_exists(self, threat_id: int) -> bool:
        """
        Проверка существования угрозы в базе знаний
        
        Args:
            threat_id: ID угрозы
            
        Returns:
            True, если угроза существует
        """
        if self.storage_type == "sqlite":
            cursor = self.kb_accessor.db.cursor()
            cursor.execute("SELECT id FROM threat_types WHERE id = ?", (threat_id,))
            return cursor.fetchone() is not None
        else:
            # Ищем угрозу в JSON структуре
            for section in self.kb_accessor.data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    for subsection in section.get("subsections", []):
                        content = subsection.get("content", {})
                        for threat_key, threat_data in content.items():
                            if threat_data.get("id") == threat_id:
                                return True
            return False
    
    def _get_current_date(self) -> str:
        """
        Получение текущей даты в формате YYYY-MM-DD
        
        Returns:
            Строка с текущей датой
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")


class RiskAssessmentSchemaUpdater:
    """Класс для обновления схемы базы данных для поддержки оценки рисков"""
    
    @staticmethod
    def update_json_schema(json_path: str) -> bool:
        """
        Обновление схемы JSON для поддержки оценки рисков
        
        Args:
            json_path: Путь к JSON файлу базы знаний
            
        Returns:
            True, если обновление выполнено успешно
        """
        try:
            # Загружаем текущую базу знаний
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем наличие раздела cyber_threats
            cyber_threats_exists = False
            for section in data.get("sections", []):
                if section.get("id") == "cyber_threats":
                    cyber_threats_exists = True
                    break
            
            # Если раздела нет, создаем его
            if not cyber_threats_exists:
                data["sections"].append({
                    "id": "cyber_threats",
                    "name": "Категории киберугроз",
                    "description": "Классификация и описание основных типов киберугроз",
                    "subsections": [
                        {
                            "id": "malware",
                            "name": "Вредоносное ПО",
                            "content": {}
                        },
                        {
                            "id": "network_attacks",
                            "name": "Сетевые атаки",
                            "content": {}
                        },
                        {
                            "id": "social_engineering",
                            "name": "Социальная инженерия",
                            "content": {}
                        }
                    ]
                })
            
            # Сохраняем обновленную базу знаний
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при обновлении JSON схемы: {e}")
            return False
    
    @staticmethod
    def update_sqlite_schema(sqlite_path: str) -> bool:
        """
        Обновление схемы SQLite для поддержки оценки рисков
        
        Args:
            sqlite_path: Путь к SQLite файлу базы данных
            
        Returns:
            True, если обновление выполнено успешно
        """
        try:
            # Подключаемся к базе данных
            conn = sqlite3.connect(sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Проверяем наличие таблицы threat_types
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='threat_types'")
            if not cursor.fetchone():
                # Создаем таблицу угроз
                cursor.execute("""
                    CREATE TABLE threat_types (
                        id INTEGER PRIMARY KEY,
                        subsection_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        definition TEXT,
                        FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
                    )
                """)
                
                # Создаем таблицы для примеров и индикаторов угроз
                cursor.execute("""
                    CREATE TABLE threat_examples (
                        threat_id INTEGER,
                        example TEXT,
                        PRIMARY KEY (threat_id, example),
                        FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE threat_indicators (
                        threat_id INTEGER,
                        indicator TEXT,
                        PRIMARY KEY (threat_id, indicator),
                        FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE threat_protection (
                        threat_id INTEGER,
                        protection TEXT,
                        PRIMARY KEY (threat_id, protection),
                        FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
                    )
                """)
            
            # Проверяем наличие таблицы risk_assessments
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_assessments'")
            if not cursor.fetchone():
                # Создаем таблицу оценки рисков
                cursor.execute("""
                    CREATE TABLE risk_assessments (
                        id INTEGER PRIMARY KEY,
                        threat_id INTEGER NOT NULL,
                        probability REAL NOT NULL,
                        impact REAL NOT NULL,
                        exploitation_complexity REAL NOT NULL,
                        base_score REAL NOT NULL,
                        last_updated DATE NOT NULL,
                        assessor TEXT,
                        notes TEXT,
                        FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
                    )
                """)
                
                # Создаем таблицу для факторов влияния на риск
                cursor.execute("""
                    CREATE TABLE risk_factors (
                        id INTEGER PRIMARY KEY,
                        assessment_id INTEGER NOT NULL,
                        factor_name TEXT NOT NULL,
                        factor_value REAL NOT NULL,
                        factor_description TEXT,
                        FOREIGN KEY (assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE
                    )
                """)
                
                # Создаем таблицу для мер снижения риска
                cursor.execute("""
                    CREATE TABLE risk_mitigations (
                        id INTEGER PRIMARY KEY,
                        assessment_id INTEGER NOT NULL,
                        mitigation_name TEXT NOT NULL,
                        effectiveness REAL NOT NULL,
                        implementation_status TEXT,
                        implementation_cost TEXT,
                        mitigation_description TEXT,
                        FOREIGN KEY (assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE
                    )
                """)
                
                # Создаем индексы для оптимизации запросов
                cursor.execute("CREATE INDEX idx_risk_assessments_threat_id ON risk_assessments(threat_id)")
                cursor.execute("CREATE INDEX idx_risk_factors_assessment_id ON risk_factors(assessment_id)")
                cursor.execute("CREATE INDEX idx_risk_mitigations_assessment_id ON risk_mitigations(assessment_id)")
            
            # Проверяем наличие раздела cyber_threats
            cursor.execute("SELECT id FROM sections WHERE id = 'cyber_threats'")
            if not cursor.fetchone():
                # Добавляем раздел с киберугрозами
                cursor.execute("""
                    INSERT INTO sections (id, name, description, order_index)
                    VALUES ('cyber_threats', 'Категории киберугроз', 'Классификация и описание основных типов киберугроз', 
                    (SELECT MAX(order_index) + 1 FROM sections))
                """)
                
                # Добавляем подразделы
                cursor.execute("""
                    INSERT INTO subsections (id, section_id, name, order_index)
                    VALUES ('malware', 'cyber_threats', 'Вредоносное ПО', 0)
                """)
                
                cursor.execute("""
                    INSERT INTO subsections (id, section_id, name, order_index)
                    VALUES ('network_attacks', 'cyber_threats', 'Сетевые атаки', 1)
                """)
                
                cursor.execute("""
                    INSERT INTO subsections (id, section_id, name, order_index)
                    VALUES ('social_engineering', 'cyber_threats', 'Социальная инженерия', 2)
                """)
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Ошибка при обновлении SQLite схемы: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return False
