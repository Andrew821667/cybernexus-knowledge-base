#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модели данных для механизма обратной связи системы базы знаний КиберНексус
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import datetime
import json


class FeedbackType(Enum):
    """Типы обратной связи"""
    COMMENT = "comment"            # Общий комментарий
    SUGGESTION = "suggestion"      # Предложение по улучшению
    ERROR_REPORT = "error_report"  # Сообщение об ошибке
    FEATURE_REQUEST = "feature_request"  # Запрос на новую функциональность


class FeedbackStatus(Enum):
    """Статусы обработки обратной связи"""
    NEW = "new"                # Новый, еще не рассмотрен
    IN_REVIEW = "in_review"    # В процессе рассмотрения
    ACCEPTED = "accepted"      # Принят к реализации
    REJECTED = "rejected"      # Отклонен
    IMPLEMENTED = "implemented"  # Реализован
    CLOSED = "closed"          # Закрыт без реализации


class FeedbackPriority(Enum):
    """Приоритеты для обратной связи"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeedbackItem:
    """Базовый класс для элемента обратной связи"""
    id: Optional[int] = None
    type: FeedbackType = FeedbackType.COMMENT
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    content: str = ""
    entity_type: Optional[str] = None  # Тип сущности (раздел, подраздел, термин, продукт)
    entity_id: Optional[str] = None    # ID сущности, к которой относится обратная связь
    status: FeedbackStatus = FeedbackStatus.NEW
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    upvotes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование объекта в словарь"""
        result = {
            "id": self.id,
            "type": self.type.value,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_email": self.user_email,
            "content": self.content,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "assigned_to": self.assigned_to,
            "tags": self.tags,
            "attachments": self.attachments,
            "upvotes": self.upvotes
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackItem':
        """Создание объекта из словаря"""
        # Преобразование строковых значений в enum
        feedback_type = FeedbackType(data.get("type", "comment"))
        status = FeedbackStatus(data.get("status", "new"))
        priority = FeedbackPriority(data.get("priority", "medium"))
        
        return cls(
            id=data.get("id"),
            type=feedback_type,
            user_id=data.get("user_id"),
            user_name=data.get("user_name"),
            user_email=data.get("user_email"),
            content=data.get("content", ""),
            entity_type=data.get("entity_type"),
            entity_id=data.get("entity_id"),
            status=status,
            priority=priority,
            created_at=data.get("created_at", datetime.datetime.now().isoformat()),
            updated_at=data.get("updated_at"),
            assigned_to=data.get("assigned_to"),
            tags=data.get("tags", []),
            attachments=data.get("attachments", []),
            upvotes=data.get("upvotes", 0)
        )
    
    def to_json(self) -> str:
        """Преобразование объекта в JSON-строку"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class Comment(FeedbackItem):
    """Класс для комментариев"""
    type: FeedbackType = FeedbackType.COMMENT
    

@dataclass
class Suggestion(FeedbackItem):
    """Класс для предложений по улучшению"""
    type: FeedbackType = FeedbackType.SUGGESTION
    benefits: str = ""  # Описание преимуществ предложения
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование объекта в словарь"""
        result = super().to_dict()
        result["benefits"] = self.benefits
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Suggestion':
        """Создание объекта из словаря"""
        instance = super().from_dict.__func__(cls, data)
        instance.benefits = data.get("benefits", "")
        return instance


@dataclass
class ErrorReport(FeedbackItem):
    """Класс для сообщений об ошибках"""
    type: FeedbackType = FeedbackType.ERROR_REPORT
    error_type: str = ""  # Тип ошибки (фактическая, техническая, грамматическая)
    expected_behavior: str = ""  # Ожидаемое поведение или корректная информация
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование объекта в словарь"""
        result = super().to_dict()
        result["error_type"] = self.error_type
        result["expected_behavior"] = self.expected_behavior
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorReport':
        """Создание объекта из словаря"""
        instance = super().from_dict.__func__(cls, data)
        instance.error_type = data.get("error_type", "")
        instance.expected_behavior = data.get("expected_behavior", "")
        return instance


@dataclass
class FeatureRequest(FeedbackItem):
    """Класс для запросов на новые функции"""
    type: FeedbackType = FeedbackType.FEATURE_REQUEST
    use_case: str = ""  # Описание сценария использования
    business_value: str = ""  # Бизнес-ценность функциональности
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование объекта в словарь"""
        result = super().to_dict()
        result["use_case"] = self.use_case
        result["business_value"] = self.business_value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureRequest':
        """Создание объекта из словаря"""
        instance = super().from_dict.__func__(cls, data)
        instance.use_case = data.get("use_case", "")
        instance.business_value = data.get("business_value", "")
        return instance


def create_feedback_item(data: Dict[str, Any]) -> FeedbackItem:
    """
    Фабричный метод для создания соответствующего объекта обратной связи
    на основе типа из данных
    
    Args:
        data: Словарь с данными обратной связи
        
    Returns:
        Объект соответствующего класса обратной связи
    """
    feedback_type = data.get("type", "comment")
    
    if feedback_type == FeedbackType.COMMENT.value:
        return Comment.from_dict(data)
    elif feedback_type == FeedbackType.SUGGESTION.value:
        return Suggestion.from_dict(data)
    elif feedback_type == FeedbackType.ERROR_REPORT.value:
        return ErrorReport.from_dict(data)
    elif feedback_type == FeedbackType.FEATURE_REQUEST.value:
        return FeatureRequest.from_dict(data)
    else:
        # По умолчанию возвращаем базовый класс
        return FeedbackItem.from_dict(data)
