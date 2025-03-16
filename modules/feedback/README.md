Модуль обратной связи для базы знаний КиберНексус

Модуль обратной связи позволяет пользователям оставлять комментарии, предложения по улучшению, сообщать об ошибках и запрашивать новые функциональности базы знаний КиберНексус.

Содержание

1. Функциональные возможности
2. Структура модуля
3. Типы обратной связи
4. Форматы хранения данных
5. Использование библиотеки
6. Интеграция с API
7. Примеры использования

Функциональные возможности

Модуль обратной связи предоставляет следующие возможности:

- Создание различных типов обратной связи (комментарии, предложения, сообщения об ошибках, запросы функциональности)
- Связывание обратной связи с существующими сущностями базы знаний (разделы, подразделы, термины, продукты)
- Отслеживание статусов обработки обратной связи
- Управление тегами для категоризации
- Поддержка многопользовательской среды с идентификацией пользователей
- Полнотекстовый поиск по содержимому обратной связи
- Комментирование и обсуждение обратной связи
- Голосование за предложения и запросы
- Отслеживание истории изменений статуса
- Экспорт и импорт данных между различными форматами

Структура модуля

Модуль состоит из следующих компонентов:

- feedback_models.py - Модели данных для различных типов обратной связи
- feedback_accessor.py - Класс для работы с данными обратной связи (JSON и SQLite)
- schema_feedback.sql - Схема базы данных SQLite
- feedback_api.py - API-эндпоинты для работы с обратной связью
- feedback_examples.py - Примеры использования модуля

Типы обратной связи

Модуль поддерживает следующие типы обратной связи:

1. Комментарии (Comment) - Общие комментарии пользователей о базе знаний
2. Предложения (Suggestion) - Предложения по улучшению контента или функциональности
3. Сообщения об ошибках (ErrorReport) - Информация об обнаруженных ошибках или неточностях
4. Запросы на новую функциональность (FeatureRequest) - Запросы на добавление новых функций или контента

Каждый тип обратной связи имеет свои специфические атрибуты и методы обработки.

Форматы хранения данных

Модуль поддерживает два формата хранения данных:

JSON формат

Данные хранятся в структурированном JSON-файле, что удобно для:
- Простого просмотра и редактирования
- Хранения небольших объемов данных
- Версионирования через системы контроля версий
- Быстрого переноса между системами

SQLite формат

Данные хранятся в базе данных SQLite, что удобно для:
- Эффективного поиска и фильтрации
- Хранения больших объемов данных
- Обеспечения целостности данных
- Полнотекстового поиска

Использование библиотеки

Инициализация

from modules.feedback.feedback_accessor import FeedbackAccessor
from modules.feedback.feedback_models import Comment, Suggestion, ErrorReport, FeatureRequest

# Для работы с JSON
feedback = FeedbackAccessor(storage_type="json", path="data/feedback.json")

# Для работы с SQLite
feedback = FeedbackAccessor(storage_type="sqlite", path="data/feedback.db")

Создание обратной связи

# Создание комментария
comment = Comment(
    user_name="Иван Петров",
    user_email="ivan@example.com",
    content="Очень полезная информация о кибербезопасности. Спасибо!",
    entity_type="section",
    entity_id="concepts_basics"
)
comment_id = feedback.add_feedback(comment)

# Создание сообщения об ошибке
error_report = ErrorReport(
    user_name="Мария Сидорова",
    user_email="maria@example.com",
    content="В разделе о шифровании найдена ошибка в описании алгоритма AES.",
    entity_type="subsection",
    entity_id="encryption_basics",
    error_type="Фактическая ошибка",
    expected_behavior="AES использует ключи длиной 128, 192 или 256 бит, а не 64 бит, как указано."
)
error_id = feedback.add_feedback(error_report)

Получение и фильтрация обратной связи

# Получение обратной связи по ID
item = feedback.get_feedback(feedback_id)

# Получение списка всей обратной связи
all_items = feedback.get_feedback_list()

# Фильтрация по типу и статусу
suggestions = feedback.get_feedback_list(
    feedback_type=FeedbackType.SUGGESTION.value,
    status=FeedbackStatus.NEW.value
)

# Поиск по содержимому
search_results = feedback.search_feedback("шифрование")

Обновление статуса и добавление комментариев

# Обновление статуса
feedback.update_feedback(
    feedback_id,
    {
        "status": FeedbackStatus.IN_REVIEW.value,
        "assigned_to": "admin@cybernexus.com"
    },
    changed_by="admin@cybernexus.com"
)

# Добавление комментария
feedback.add_comment(
    feedback_id,
    "admin@cybernexus.com",
    "Администратор",
    "Спасибо за сообщение! Мы рассмотрим ваше предложение."
)

# Получение комментариев
comments = feedback.get_comments(feedback_id)

Управление тегами

# Добавление тега
feedback.add_tag(feedback_id, "важное")

# Удаление тега
feedback.remove_tag(feedback_id, "важное")

Голосование

# Увеличение счетчика голосов
feedback.upvote_feedback(feedback_id)

Экспорт и импорт

# Экспорт в JSON
feedback.export_to_json("exports/feedback_export.json")

# Импорт из JSON
feedback.import_from_json("exports/feedback_export.json")

Интеграция с API

Модуль обратной связи предоставляет готовые API-эндпоинты, которые можно интегрировать с существующим API-сервером:

from fastapi import FastAPI
from modules.feedback.feedback_api import router as feedback_router

app = FastAPI()

# Добавляем маршруты для работы с обратной связью
app.include_router(feedback_router)

Основные эндпоинты API

- GET /api/feedback/ - Получение списка обратной связи с фильтрацией
- POST /api/feedback/ - Создание новой обратной связи
- GET /api/feedback/{id} - Получение обратной связи по ID
- PUT /api/feedback/{id} - Обновление обратной связи
- DELETE /api/feedback/{id} - Удаление обратной связи
- GET /api/feedback/search?query={text} - Полнотекстовый поиск
- POST /api/feedback/{id}/comments - Добавление комментария
- GET /api/feedback/{id}/comments - Получение комментариев
- GET /api/feedback/{id}/history - История изменений статуса
- POST /api/feedback/{id}/upvote - Голосование за обратную связь
- GET /api/feedback/statistics - Статистика по обратной связи

Примеры использования

Более подробные примеры использования модуля обратной связи можно найти в файле feedback_examples.py:

- Пример работы с обратной связью в формате JSON
- Пример работы с обратной связью в формате SQLite
- Пример интеграции с API
