Модуль автоматического обогащения базы знаний

Модуль предназначен для автоматического сбора и обработки информации об угрозах кибербезопасности из различных источников и её интеграции в базу знаний компании.

Функциональность

1. Сбор данных из различных источников:
   - API (например, NVD для CVE)
   - RSS-ленты (новости о безопасности, бюллетени уязвимостей)
   - Веб-страницы (парсинг информации с сайтов)

2. Обработка и классификация данных:
   - Классификация по категориям угроз
   - Классификация по векторам атак
   - Извлечение индикаторов компрометации (IoC)
   - Оценка серьезности угроз

3. Интеграция в базу знаний:
   - Структурированное хранение в базе знаний
   - Категоризация по типам угроз
   - Связывание с существующими данными

4. Мониторинг и отчетность:
   - Статистика по обнаруженным угрозам
   - Отслеживание новых угроз
   - Журналирование процесса обогащения

Структура модуля

- auto_enrichment_module.py - основной файл модуля
- config/ - директория с файлами конфигурации
  - auto_enrichment_config.json - основная конфигурация
  - test_config.json - конфигурация для тестирования
- data/ - директория с данными
  - category_keywords.json - ключевые слова для категорий угроз
  - vector_keywords.json - ключевые слова для векторов атак
- test_auto_enrichment.py - тестовый скрипт
- auto_enrichment_example.py - пример использования

Требования

- Python 3.7+
- Библиотеки: requests, feedparser, beautifulsoup4
- Доступ к основной библиотеке базы знаний (knowledge_base_accessor.py)

Установка зависимостей

pip install requests feedparser beautifulsoup4

Использование

Базовый пример

from auto_enrichment_module import AutoEnrichmentModule

# Инициализация модуля
enrichment = AutoEnrichmentModule()

# Запуск процесса обогащения
result = enrichment.run_enrichment()
print(f"Результат обогащения: {result}")

# Получение последних угроз
threats = enrichment.get_latest_threats(limit=5)
for threat in threats:
    print(f"{threat['title']} (Серьезность: {threat['severity']}/10)")

# Получение статистики
stats = enrichment.get_enrichment_stats()
print(f"Всего записей: {stats['total_count']}")
print(f"Добавлено в базу знаний: {stats['added_to_kb_count']}")

# Закрытие соединений
enrichment.close()

Использование с собственной конфигурацией

from auto_enrichment_module import AutoEnrichmentModule
from knowledge_base_accessor import KnowledgeBaseAccessor

# Инициализация аксессора базы знаний
kb = KnowledgeBaseAccessor(storage_type="json", path="./my_knowledge_base.json")

# Инициализация модуля с собственной конфигурацией и аксессором
enrichment = AutoEnrichmentModule(
    config_path="./my_config.json",
    kb_accessor=kb
)

# Запуск процесса обогащения
enrichment.run_enrichment()

# Закрытие соединений
enrichment.close()

Настройка

Основные настройки модуля находятся в файле auto_enrichment_config.json. Вы можете изменить следующие параметры:

- Источники данных (sources): настройка API, RSS-лент и веб-страниц
- Хранилище данных (storage): тип и путь к хранилищу
- Процессор данных (processor): настройки классификации и извлечения
- Расписание (schedule): частота и время запуска обогащения

Тестирование

Для запуска тестов используйте скрипт test_auto_enrichment.py:

python test_auto_enrichment.py

Расширение модуля

Вы можете расширить модуль, добавив:

1. Новые источники данных:
   - Создать класс-наследник ThreatIntelSource
   - Реализовать метод fetch_data()
   - Добавить новый источник в конфигурацию

2. Новые алгоритмы классификации:
   - Расширить класс ThreatDataProcessor
   - Добавить новые методы классификации
   - Обновить метод process_entry()

3. Интеграцию с другими системами:
   - Добавить экспорт в другие форматы
   - Реализовать API для других сервисов
   - Настроить оповещения о новых угрозах
