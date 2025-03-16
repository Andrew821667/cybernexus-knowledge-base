#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки модуля автоматического обогащения
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импортируем модуль автоматического обогащения
from auto_enrichment_module import AutoEnrichmentModule, logger

def test_data_collection():
    """Тестирование сбора данных из источников"""
    print("Тестирование сбора данных из источников...")
    
    # Инициализация модуля
    enrichment = AutoEnrichmentModule()
    
    # Тестирование каждого источника
    for name, source in enrichment.sources.items():
        print(f"Получение данных из источника: {name}")
        entries = source.fetch_data()
        print(f"Получено {len(entries)} записей")
        
        if entries:
            # Выводим первую запись для проверки
            first_entry = entries[0]
            print("Пример записи:")
            print(f"- Заголовок: {first_entry.get('title', '')}")
            print(f"- Описание: {first_entry.get('description', '')[:100]}...")
            print(f"- Опубликовано: {first_entry.get('published', '')}")
            print(f"- Ссылка: {first_entry.get('link', '')}")
    
    # Закрываем соединения
    enrichment.close()
    
    print("Тестирование сбора данных завершено
    print("Тестирование сбора данных завершено")


def test_data_processing():
    """Тестирование обработки данных"""
    print("Тестирование обработки данных...")
    
    # Инициализация модуля
    enrichment = AutoEnrichmentModule()
    
    # Получаем данные из первого доступного источника
    source_data = []
    for name, source in enrichment.sources.items():
        print(f"Получение тестовых данных из источника: {name}")
        entries = source.fetch_data()
        if entries:
            source_data = entries[:3]  # Берем не более 3 записей для теста
            print(f"Получено {len(source_data)} записей для тестирования")
            break
    
    if not source_data:
        print("Не удалось получить тестовые данные ни из одного источника")
        return
    
    # Обработка данных
    print("Обработка тестовых данных...")
    processed_data = enrichment.processor.process_entries(source_data)
    
    # Вывод результатов обработки
    for i, entry in enumerate(processed_data):
        print(f"\nЗапись #{i+1}:")
        print(f"- Заголовок: {entry['title']}")
        print(f"- Категории угроз: {entry['threat_categories']}")
        print(f"- Векторы атак: {entry['attack_vectors']}")
        print(f"- Серьезность: {entry['severity']}/10")
        
        # Вывод индикаторов компрометации
        for ioc_type, values in entry['ioc'].items():
            if values:
                print(f"- {ioc_type.upper()}: {values}")
    
    # Закрываем соединения
    enrichment.close()
    
    print("Тестирование обработки данных завершено")


def test_integration():
    """Тестирование интеграции данных в базу знаний"""
    print("Тестирование интеграции данных в базу знаний...")
    
    # Проверяем, существует ли файл базы знаний
    kb_path = os.path.join(os.path.dirname(__file__), "../../knowledge_base.json")
    if not os.path.exists(kb_path):
        print(f"Файл базы знаний не найден: {kb_path}")
        print("Создаем базовый файл для тестирования...")
        
        # Создаем базовую структуру базы знаний
        from knowledge_base_accessor import KnowledgeBaseAccessor
        kb = KnowledgeBaseAccessor(storage_type="json", path=kb_path)
        kb.update_company_info({
            "name": "КиберНексус",
            "description": "Тестовая компания для демонстрации возможностей модуля автоматического обогащения"
        })
        kb.close()
    
    # Инициализация модуля с тестовой конфигурацией
    config_path = os.path.join(os.path.dirname(__file__), "config/test_config.json")
    
    # Проверяем, существует ли файл тестовой конфигурации
    if not os.path.exists(config_path):
        print(f"Файл тестовой конфигурации не найден: {config_path}")
        print("Используем стандартную конфигурацию")
        config_path = None
    
    # Инициализация модуля
    enrichment = AutoEnrichmentModule(config_path=config_path)
    
    # Запускаем процесс обогащения с тестовыми данными
    print("Запуск тестового процесса обогащения...")
    result = enrichment.run_enrichment()
    
    # Вывод результатов
    print(f"Результат обогащения: {result}")
    
    # Проверяем последние добавленные угрозы
    print("\nПоследние добавленные угрозы:")
    threats = enrichment.get_latest_threats(limit=3)
    for i, threat in enumerate(threats):
        print(f"{i+1}. {threat['title']} (Серьезность: {threat['severity']}/10)")
        print(f"   Категории: {', '.join(threat['threat_categories'])}")
        print(f"   Добавлено в базу знаний: {'Да' if threat['added_to_kb'] else 'Нет'}")
    
    # Получаем статистику
    print("\nСтатистика обогащения:")
    stats = enrichment.get_enrichment_stats()
    print(f"Всего записей: {stats['total_count']}")
    print(f"Добавлено в базу знаний: {stats['added_to_kb_count']}")
    
    # Закрываем соединения
    enrichment.close()
    
    print("Тестирование интеграции завершено")


def main():
    """Основная функция для запуска тестов"""
    # Настраиваем уровень логирования для тестов
    logger.setLevel(logging.INFO)
    
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ МОДУЛЯ АВТОМАТИЧЕСКОГО ОБОГАЩЕНИЯ")
    print("=" * 50)
    
    # Тестирование сбора данных
    test_data_collection()
    print("\n" + "=" * 50 + "\n")
    
    # Тестирование обработки данных
    test_data_processing()
    print("\n" + "=" * 50 + "\n")
    
    # Тестирование интеграции данных в базу знаний
    test_integration()
    print("\n" + "=" * 50 + "\n")
    
    print("Все тесты завершены")


if __name__ == "__main__":
    main()
