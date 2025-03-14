#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Примеры использования библиотеки для работы с базой знаний по кибербезопасности
"""

from knowledge_base_accessor import KnowledgeBaseAccessor
import json
import os


def print_separator():
    """Печать разделителя для наглядности вывода"""
    print("\n" + "=" * 80 + "\n")


def example_json_storage():
    """Пример работы с базой знаний в формате JSON"""
    print("Пример работы с базой знаний в формате JSON")
    print_separator()
    
    # Создаем экземпляр для работы с JSON
    kb = KnowledgeBaseAccessor(storage_type="json", path="knowledge_base.json")
    
    # Добавляем новый термин
    print("Добавление нового термина...")
    kb.add_term({
        "term": "Vulnerability",
        "definition": "Уязвимость - слабость в информационной системе, процедурах безопасности, внутреннем контроле или реализации, которая может быть использована угрозой.",
        "related_terms": ["эксплойт", "патч", "риск", "угроза"]
    })
    
    # Получаем информацию о компании
    print("\nИнформация о компании:")
    company_info = kb.get_company_info()
    print(json.dumps(company_info, ensure_ascii=False, indent=2))
    
    # Получаем список разделов
    print("\nСписок разделов:")
    sections = kb.get_sections()
    for section in sections:
        print(f"- {section['name']} ({section['id']})")
    
    # Получаем информацию о продукте
    print("\nИнформация о продукте 'ИнтеллектЩит':")
    product = kb.get_product("intellectshield")
    if product:
        print(f"Название: {product['name']}")
        print(f"Описание: {product['content']['description']}")
        print("Ключевые особенности:")
        for feature in product['content'].get('key_features', []):
            print(f"  - {feature}")
        print("Технологии:")
        tech = product['content'].get('technology', {})
        print(f"  - Ядро: {tech.get('core', '')}")
        print(f"  - Архитектура: {tech.get('architecture', '')}")
    else:
        print("Продукт не найден")
    
    # Ищем информацию по запросу
    print("\nПоиск по запросу 'уязвимость':")
    search_results = kb.search("уязвимость")
    for result in search_results:
        print(f"- {result.get('title', 'Без названия')}: {result.get('content', '')[:100]}...")
    
    # Экспорт базы знаний
    print("\nЭкспорт базы знаний в export.json")
    os.makedirs('exports', exist_ok=True)
    kb.export_to_json("exports/export.json")
    
    # Закрываем соединение
    kb.close()
    
    print_separator()
    print("Пример работы с JSON-хранилищем завершен")


def example_sqlite_storage():
    """Пример работы с базой знаний в формате SQLite"""
    print("Пример работы с базой знаний в формате SQLite")
    print_separator()
    
    # Проверяем наличие файла базы данных
    if not os.path.exists("knowledge_base.db"):
        print("Создание SQLite базы данных из JSON...")
        # Импортируем функцию преобразования из модуля data_converter
        from data_converter import json_to_sqlite
        json_to_sqlite("knowledge_base.json", "knowledge_base.db")
    
    # Создаем экземпляр для работы с SQLite
    kb = KnowledgeBaseAccessor(storage_type="sqlite", path="knowledge_base.db")
    
    # Добавляем новый раздел с киберугрозами
    print("Добавление раздела с киберугрозами...")
    kb.add_section({
        "id": "cyber_threats",
        "name": "Категории киберугроз",
        "description": "Классификация и описание основных типов киберугроз",
        "subsections": [
            {
                "id": "malware",
                "name": "Вредоносное ПО"
            },
            {
                "id": "network_attacks",
                "name": "Сетевые атаки"
            },
            {
                "id": "social_engineering",
                "name": "Социальная инженерия"
            }
        ]
    })
    
    # Получаем информацию о компании
    print("\nИнформация о компании:")
    company_info = kb.get_company_info()
    print(json.dumps(company_info, ensure_ascii=False, indent=2))
    
    # Получаем список разделов
    print("\nСписок разделов:")
    sections = kb.get_sections()
    for section in sections:
        print(f"- {section['name']} ({section['id']})")
        # Выводим подразделы
        if "subsections" in section:
            for subsection in section["subsections"]:
                print(f"  - {subsection['name']} ({subsection['id']})")
    
    # Поиск по базе данных
    print("\nПоиск по запросу 'безопасность':")
    search_results = kb.search("безопасность")
    for result in search_results:
        print(f"- {result.get('title', 'Без названия')}: {result.get('content', '')[:100]}...")
    
    # Экспорт базы знаний обратно в JSON
    print("\nЭкспорт базы знаний в SQLite_export.json")
    os.makedirs('exports', exist_ok=True)
    kb.export_to_json("exports/SQLite_export.json")
    
    # Закрываем соединение
    kb.close()
    
    print_separator()
    print("Пример работы с SQLite-хранилищем завершен")


def main():
    """Основная функция для запуска примеров"""
    # Создаем директории
    os.makedirs('exports', exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    choice = None
    while choice != '0':
        print("\nПРИМЕРЫ ИСПОЛЬЗОВАНИЯ БАЗЫ ЗНАНИЙ ПО КИБЕРБЕЗОПАСНОСТИ")
        print("1. Пример работы с базой знаний в формате JSON")
        print("2. Пример работы с базой знаний в формате SQLite")
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
