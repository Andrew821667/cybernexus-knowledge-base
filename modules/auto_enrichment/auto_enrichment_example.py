#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования модуля автоматического обогащения базы знаний по кибербезопасности
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Импортируем модуль автоматического обогащения
from auto_enrichment_module import AutoEnrichmentModule
from knowledge_base_accessor import KnowledgeBaseAccessor


def setup_logger():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("auto_enrichment_example.log")
        ]
    )
    return logging.getLogger(__name__)


def create_directories():
    """Создание необходимых директорий"""
    # Создаем директории для данных и конфигураций
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'config'), exist_ok=True)


def main():
    """Основная функция для запуска примера"""
    global logger
    logger = setup_logger()
    logger.info("Запуск примера использования модуля автоматического обогащения")
    
    # Создание парсера аргументов командной строки
    parser = argparse.ArgumentParser(description="Пример использования модуля автоматического обогащения базы знаний")
    parser.add_argument("--kb-path", help="Путь к базе знаний (JSON или SQLite)")
    parser.add_argument("--config", help="Путь к файлу конфигурации")
    parser.add_argument("--run", action="store_true", help="Запустить процесс обогащения")
    parser.add_argument("--dry-run", action="store_true", help="Запустить в режиме без внесения изменений")
    parser.add_argument("--init", action="store_true", help="Инициализировать директории и конфигурацию")
    
    args = parser.parse_args()
    
    # Инициализация директорий и файлов
    if args.init:
        logger.info("Инициализация директорий и файлов конфигурации")
        create_directories()
        logger.info("Инициализация завершена")
    
    logger.info("Пример использования модуля автоматического обогащения завершен")


if __name__ == "__main__":
    main()
