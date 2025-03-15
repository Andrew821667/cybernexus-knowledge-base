#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Примеры использования модуля обучения персонала
"""

from modules.training.training_accessor import TrainingAccessor
import json
import os


def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("\n" + "=" * 80 + "\n")


def example_json_storage():
    """Пример работы с данными обучения в формате JSON"""
    print("Пример работы с данными обучения в формате JSON")
    print_separator()
    
    # Создаем экземпляр для работы с JSON
    training = TrainingAccessor(storage_type="json", path="training_data.json")
    
    # Добавляем категории обучения
    print("Добавление категорий обучения...")
    security_basics_id = training.add_category({
        "name": "Основы безопасности",
        "description": "Базовые знания о кибербезопасности",
        "order_index": 1
    })
    
    security_advanced_id = training.add_category({
        "name": "Продвинутая безопасность",
        "description": "Углубленные знания о кибербезопасности",
        "order_index": 2
    })
    
    product_training_id = training.add_category({
        "name": "Обучение по продуктам",
        "description": "Обучение по продуктам компании",
        "order_index": 3
    })
    
    # Добавляем курс по основам информационной безопасности
    print("\nДобавление курса по основам ИБ...")
    course_data = {
        "title": "Основы информационной безопасности",
        "description": "Базовый курс по основам информационной безопасности для всех сотрудников",
        "category_id": security_basics_id,
        "difficulty_level_id": 1,  # Начальный уровень
        "duration_minutes": 120,
        "is_required": True,
        "author": "Отдел информационной безопасности"
    }
    course_id = training.add_course(course_data)
    
    # Получаем список категорий
    print("\nСписок категорий:")
    categories = training.get_categories()
    for category in categories:
        print(f"- {category['name']} ({category['id']})")
    
    # Получаем список курсов
    print("\nСписок курсов в категории 'Основы безопасности':")
    courses = training.get_courses(category_id=security_basics_id)
    for course in courses:
        print(f"- {course['title']} (ID: {course['id']}, Длительность: {course['duration_minutes']} мин.)")
    
    # Поиск курсов
    print("\nПоиск курсов по запросу 'основы':")
    search_results = training.search_training("основы")
    for result in search_results:
        print(f"- {result['title']} ({result['type']})")
    
    # Закрываем соединение
    training.close()
    
    print_separator()
    print("Пример работы с JSON-хранилищем завершен")


def example_sqlite_storage():
    """Пример работы с данными обучения в формате SQLite"""
    print("Пример работы с данными обучения в формате SQLite")
    print_separator()
    
    # Удаляем существующую базу данных для демонстрации
    if os.path.exists("training_data.db"):
        os.remove("training_data.db")
    
    # Создаем экземпляр для работы с SQLite
    training = TrainingAccessor(storage_type="sqlite", path="training_data.db")
    
    # Добавляем категории обучения
    print("Добавление категорий обучения...")
    security_basics_id = training.add_category({
        "name": "Основы безопасности",
        "description": "Базовые знания о кибербезопасности",
        "order_index": 1
    })
    
    security_advanced_id = training.add_category({
        "name": "Продвинутая безопасность",
        "description": "Углубленные знания о кибербезопасности",
        "order_index": 2
    })
    
    product_training_id = training.add_category({
        "name": "Обучение по продуктам",
        "description": "Обучение по продуктам компании",
        "order_index": 3
    })
    
    # Добавляем курс по основам безопасности
    print("\nДобавление курса по основам безопасности...")
    course_data = {
        "title": "Основы информационной безопасности",
        "description": "Базовый курс по основам информационной безопасности для всех сотрудников",
        "category_id": security_basics_id,
        "difficulty_level_id": 1,  # Начальный уровень
        "duration_minutes": 120,
        "is_required": True,
        "author": "Отдел информационной безопасности"
    }
    course_id = training.add_course(course_data)
    
    # Добавляем сотрудника
    print("\nДобавление сотрудника...")
    employee_data = {
        "username": "ivanov",
        "full_name": "Иванов Иван Иванович",
        "email": "ivanov@example.com",
        "department": "ИТ",
        "hire_date": "2023-01-15"
    }
    employee_id = training.add_employee(employee_data)
    
    # Обновляем прогресс обучения
    print("\nОбновление прогресса обучения...")
    training.update_course_progress(
        employee_id=employee_id,
        course_id=course_id,
        progress_data={
            "is_completed": False,
            "completion_percent": 50,
            "start_date": "2023-05-10"
        }
    )
    
    # Получаем список категорий
    print("\nСписок категорий:")
    categories = training.get_categories()
    for category in categories:
        print(f"- {category['name']} (ID: {category['id']})")
    
    # Получаем список курсов
    print("\nСписок курсов:")
    courses = training.get_courses()
    for course in courses:
        print(f"- {course['title']} (ID: {course['id']})")
    
    # Получаем прогресс обучения
    print("\nПрогресс обучения сотрудника:")
    progress = training.get_course_progress(employee_id=employee_id)
    if progress:
        for p in progress:
            print(f"- Курс ID: {p['course_id']}, Прогресс: {p['completion_percent']}%, Завершен: {p['is_completed']}")
    else:
        print("Прогресс не найден")
    
    # Поиск в базе данных
    print("\nПоиск курсов по запросу 'основы':")
    search_results = training.search_training("основы")
    for result in search_results:
        print(f"- {result['title']} ({result['type']})")
    
    # Закрываем соединение
    training.close()
    
    print_separator()
    print("Пример работы с SQLite-хранилищем завершен")


def main():
    """Основная функция для запуска примеров"""
    choice = None
    while choice != '0':
        print("\nПРИМЕРЫ ИСПОЛЬЗОВАНИЯ МОДУЛЯ ОБУЧЕНИЯ ПЕРСОНАЛА")
        print("1. Пример работы с данными обучения в формате JSON")
        print("2. Пример работы с данными обучения в формате SQLite")
        print("0. Выход")
        
        choice = input("\nВыберите пример для запуска: ")
        
        if choice == '1':
            example_json_storage()
        elif choice == '2':
            example_sqlite_storage()
        elif choice == '0':
            print("Выход из программы...")
        else:
            print("Неверный выбор. Пожалуйста, попробуйте снова.")


if __name__ == "__main__":
    main()
