#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Примеры использования модуля обратной связи для базы знаний КиберНексус
"""

from feedback_models import (
    FeedbackItem, Comment, Suggestion, ErrorReport, FeatureRequest,
    FeedbackType, FeedbackStatus, FeedbackPriority, create_feedback_item
)
from feedback_accessor import FeedbackAccessor
import json
import os
import datetime


def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("\n" + "=" * 80 + "\n")


def example_json_storage():
    """Пример работы с обратной связью в формате JSON"""
    print("Пример работы с обратной связью в формате JSON")
    print_separator()
    
    # Создаем экземпляр для работы с JSON
    fb = FeedbackAccessor(storage_type="json", path="feedback.json")
    
    # Пример создания различных типов обратной связи
    
    # 1. Комментарий
    print("Добавление комментария...")
    comment = Comment(
        user_name="Иван Петров",
        user_email="ivan@example.com",
        content="Очень полезная информация о кибербезопасности. Спасибо!",
        entity_type="section",
        entity_id="concepts_basics"
    )
    comment_id = fb.add_feedback(comment)
    print(f"Добавлен комментарий с ID: {comment_id}")
    
    # 2. Сообщение об ошибке
    print("\nДобавление сообщения об ошибке...")
    error_report = ErrorReport(
        user_name="Мария Сидорова",
        user_email="maria@example.com",
        content="В разделе о шифровании найдена ошибка в описании алгоритма AES.",
        entity_type="subsection",
        entity_id="encryption_basics",
        error_type="Фактическая ошибка",
        expected_behavior="AES использует ключи длиной 128, 192 или 256 бит, а не 64 бит, как указано."
    )
    error_id = fb.add_feedback(error_report)
    print(f"Добавлено сообщение об ошибке с ID: {error_id}")
    
    # 3. Предложение по улучшению
    print("\nДобавление предложения по улучшению...")
    suggestion = Suggestion(
        user_name="Алексей Иванов",
        user_email="alex@example.com",
        content="Предлагаю добавить раздел о безопасности мобильных приложений.",
        benefits="Это поможет разработчикам создавать более защищенные приложения и пользователям понимать риски."
    )
    suggestion.tags = ["мобильные приложения", "разработка", "безопасность"]
    suggestion_id = fb.add_feedback(suggestion)
    print(f"Добавлено предложение с ID: {suggestion_id}")
    
    # 4. Запрос на новую функциональность
    print("\nДобавление запроса на новую функциональность...")
    feature_request = FeatureRequest(
        user_name="Екатерина Смирнова",
        user_email="kate@example.com",
        content="Хотелось бы видеть интерактивные примеры атак для обучения.",
        use_case="Обучение сотрудников распознаванию фишинговых атак на практических примерах.",
        business_value="Повышение осведомленности сотрудников и снижение вероятности успешных атак."
    )
    feature_request.priority = FeedbackPriority.HIGH
    feature_id = fb.add_feedback(feature_request)
    print(f"Добавлен запрос на функциональность с ID: {feature_id}")
    
    # Получение списка всех элементов обратной связи
    print("\nСписок всей обратной связи:")
    all_feedback = fb.get_feedback_list()
    for item in all_feedback:
        print(f"- [{item.type.value}] {item.content[:50]}...")
    
    # Получение списка только предложений с высоким приоритетом
    print("\nСписок предложений с высоким приоритетом:")
    suggestions = fb.get_feedback_list(
        feedback_type=FeedbackType.SUGGESTION.value,
        priority=FeedbackPriority.HIGH.value
    )
    for item in suggestions:
        print(f"- [{item.priority.value}] {item.content[:50]}...")
    
    # Поиск по содержимому
    print("\nПоиск по запросу 'мобильн':")
    search_results = fb.search_feedback("мобильн")
    for item in search_results:
        print(f"- [{item.type.value}] {item.content[:50]}...")
    
    # Обновление статуса предложения
    print(f"\nОбновление статуса предложения {suggestion_id}...")
    fb.update_feedback(
        suggestion_id,
        {
            "status": FeedbackStatus.IN_REVIEW.value,
            "assigned_to": "admin@cybernexus.com",
            "status_comment": "Взято в работу для анализа"
        },
        changed_by="admin@cybernexus.com"
    )
    
    # Добавление тега к предложению
    print(f"Добавление тега к предложению {suggestion_id}...")
    fb.add_tag(suggestion_id, "приоритетно")
    
    # Добавление комментария к сообщению об ошибке
    print(f"\nДобавление комментария к сообщению об ошибке {error_id}...")
    fb.add_comment(
        error_id,
        "admin@cybernexus.com",
        "Администратор",
        "Спасибо за сообщение! Мы исправим ошибку в ближайшее время."
    )
    
    # Получение комментариев
    print(f"\nКомментарии к сообщению об ошибке {error_id}:")
    comments = fb.get_comments(error_id)
    for comment in comments:
        print(f"- {comment['user_name']}: {comment['content']}")
    
    # Получение истории изменений статуса
    print(f"\nИстория изменений статуса предложения {suggestion_id}:")
    history = fb.get_status_history(suggestion_id)
    for record in history:
        print(f"- {record['changed_at']}: {record.get('old_status', 'None')} -> {record['new_status']}")
    
    # Увеличение счетчика голосов
    print(f"\nГолосование за запрос функциональности {feature_id}...")
    fb.upvote_feedback(feature_id)
    
    # Получение обновленной информации о запросе
    feature = fb.get_feedback(feature_id)
    print(f"Количество голосов: {feature.upvotes}")
    
    # Получение статистики
    print("\nСтатистика по обратной связи:")
    stats = fb.get_statistics()
    print(f"Всего элементов: {stats['total_items']}")
    print("По типам:")
    for type_name, count in stats['type_counts'].items():
        print(f"  - {type_name}: {count}")
    print("По статусам:")
    for status_name, count in stats['status_counts'].items():
        print(f"  - {status_name}: {count}")
    print("Популярные теги:")
    for tag, count in stats['popular_tags'].items():
        print(f"  - {tag}: {count}")
    
    # Экспорт данных
    print("\nЭкспорт данных обратной связи...")
    os.makedirs('exports', exist_ok=True)
    fb.export_to_json("exports/feedback_export.json")
    
    # Закрываем соединение
    fb.close()
    
    print_separator()
    print("Пример работы с JSON-хранилищем обратной связи завершен")


def example_sqlite_storage():
    """Пример работы с обратной связью в формате SQLite"""
    print("Пример работы с обратной связью в формате SQLite")
    print_separator()
    
    # Удаляем существующую базу данных для демонстрации
    if os.path.exists("feedback.db"):
        os.remove("feedback.db")
    
    # Создаем экземпляр для работы с SQLite
    fb = FeedbackAccessor(storage_type="sqlite", path="feedback.db")
    
    # Добавляем несколько элементов обратной связи
    print("Добавление элементов обратной связи...")
    
    # Комментарий
    comment = Comment(
        user_name="Дмитрий Кузнецов",
        user_email="dmitry@example.com",
        content="Очень понравился раздел о защите от социальной инженерии.",
        entity_type="subsection",
        entity_id="social_engineering"
    )
    fb.add_feedback(comment)
    
    # Сообщение об ошибке
    error_report = ErrorReport(
        user_name="Ольга Смирнова",
        user_email="olga@example.com",
        content="Обнаружена неточность в описании типов шифрования.",
        entity_type="subsection",
        entity_id="encryption_types",
        error_type="Терминологическая ошибка",
        expected_behavior="Симметричное шифрование использует один ключ, а не два, как указано."
    )
    error_id = fb.add_feedback(error_report)
    
    # Предложение по улучшению
    suggestion = Suggestion(
        user_name="Сергей Попов",
        user_email="sergey@example.com",
        content="Добавить интерактивную визуализацию процесса атаки.",
        benefits="Поможет лучше понять механизмы атак и защиты."
    )
    suggestion.tags = ["визуализация", "обучение", "интерактив"]
    suggestion_id = fb.add_feedback(suggestion)
    
    # Получение списка всех элементов обратной связи с тегами
    print("\nСписок всей обратной связи с тегом 'обучение':")
    feedback_with_tag = fb.get_feedback_list(tags=["обучение"])
    for item in feedback_with_tag:
        print(f"- [{item.type.value}] {item.content}")
        print(f"  Теги: {', '.join(item.tags)}")
    
    # Добавление нескольких комментариев
    print(f"\nДобавление комментариев к сообщению об ошибке {error_id}...")
    fb.add_comment(
        error_id,
        "admin@cybernexus.com",
        "Администратор",
        "Спасибо за сообщение. Мы проверим информацию."
    )
    fb.add_comment(
        error_id,
        "expert@cybernexus.com",
        "Эксперт по шифрованию",
        "Ошибка подтверждена. Будет исправлено в ближайшем обновлении."
    )
    
    # Получение комментариев
    print(f"\nКомментарии к сообщению об ошибке {error_id}:")
    comments = fb.get_comments(error_id)
    for comment in comments:
        print(f"- {comment['user_name']}: {comment['content']}")
    
    # Изменение статуса сообщения об ошибке
    print(f"\nИзменение статуса сообщения об ошибке {error_id}...")
    fb.update_feedback(
        error_id,
        {
            "status": FeedbackStatus.ACCEPTED.value,
            "status_comment": "Ошибка подтверждена и будет исправлена"
        },
        changed_by="admin@cybernexus.com"
    )
    
    # Изменение приоритета предложения
    print(f"\nИзменение приоритета предложения {suggestion_id}...")
    fb.update_feedback(
        suggestion_id,
        {"priority": FeedbackPriority.HIGH.value},
        changed_by="admin@cybernexus.com"
    )
    
    # Полнотекстовый поиск
    print("\nПоиск по запросу 'шифрование':")
    search_results = fb.search_feedback("шифрование")
    for item in search_results:
        print(f"- [{item.type.value}] {item.content}")
    
    # Получение статистики
    print("\nСтатистика по обратной связи:")
    stats = fb.get_statistics()
    print(f"Всего элементов: {stats['total_items']}")
    print("По типам:")
    for type_name, count in stats['type_counts'].items():
        print(f"  - {type_name}: {count}")
    
    # Экспорт данных в JSON
    print("\nЭкспорт данных обратной связи в JSON...")
    os.makedirs('exports', exist_ok=True)
    fb.export_to_json("exports/feedback_sqlite_export.json")
    
    # Закрываем соединение
    fb.close()
    
    print_separator()
    print("Пример работы с SQLite-хранилищем обратной связи завершен")


def example_integration_with_api():
    """Пример интеграции с API"""
    print("Пример интеграции модуля обратной связи с API")
    print_separator()
    
    print("""
from fastapi import FastAPI, Depends
from modules.feedback.feedback_api import router as feedback_router
from modules.api.api_auth import get_current_user, get_admin_user

app = FastAPI(title="КиберНексус API", description="API для базы знаний по кибербезопасности")

# Добавляем маршруты для работы с обратной связью
app.include_router(feedback_router)

# Пример использования:
# GET /api/feedback/ - получение списка обратной связи
# POST /api/feedback/ - создание новой обратной связи
# GET /api/feedback/{id} - получение обратной связи по ID
# PUT /api/feedback/{id} - обновление обратной связи
# GET /api/feedback/search?query=текст - поиск по обратной связи
# и т.д.
    """)
    
    print_separator()
    print("Пример интеграции с API завершен")


def main():
    """Основная функция для запуска примеров"""
    # Создаем директории
    os.makedirs('exports', exist_ok=True)
    
    choice = None
    while choice != '0':
        print("\nПРИМЕРЫ ИСПОЛЬЗОВАНИЯ МОДУЛЯ ОБРАТНОЙ СВЯЗИ")
        print("1. Пример работы с обратной связью в формате JSON")
        print("2. Пример работы с обратной связью в формате SQLite")
        print("3. Пример интеграции с API")
        print("0. Выход")
        
        choice = input("\nВыберите пример для запуска: ")
        
        if choice == '1':
            example_json_storage()
        elif choice == '2':
            example_sqlite_storage()
        elif choice == '3':
            example_integration_with_api()
        elif choice == '0':
            print("Выход из программы...")
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main()
