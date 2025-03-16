"""
Модуль обратной связи для базы знаний КиберНексус.
Позволяет пользователям оставлять комментарии, предложения и сообщать об ошибках.

Основные компоненты:
- feedback_models.py - Модели данных для различных типов обратной связи
- feedback_accessor.py - Класс для работы с данными обратной связи
- feedback_api.py - API-эндпоинты для работы с обратной связью
"""

from .feedback_models import (
    FeedbackItem, Comment, Suggestion, ErrorReport, FeatureRequest,
    FeedbackType, FeedbackStatus, FeedbackPriority, create_feedback_item
)
from .feedback_accessor import FeedbackAccessor
