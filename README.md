# База знаний КиберНексус по кибербезопасности

Репозиторий содержит базу знаний компании КиберНексус - ведущего разработчика AI-решений в области кибербезопасности. База знаний включает в себя структурированную информацию о концепциях кибербезопасности, продуктах компании, типах угроз и методах защиты.

## Содержание

1. [Структура репозитория](#структура-репозитория)
2. [Форматы хранения данных](#форматы-хранения-данных)
3. [Начало работы](#начало-работы)
4. [Использование библиотеки](#использование-библиотеки)
5. [Преобразование между форматами](#преобразование-между-форматами)
6. [Примеры](#примеры)
7. [Развитие базы знаний](#развитие-базы-знаний)

## Структура репозитория

- `knowledge_base.json` - База знаний в формате JSON
- `knowledge_base_accessor.py` - Библиотека для работы с базой знаний
- `schema.sql` - Схема базы данных SQLite
- `data_converter.py` - Скрипт для преобразования между форматами JSON и SQLite
- `usage_examples.py` - Примеры использования библиотеки
- `README.md` - Документация по проекту

## Форматы хранения данных

База знаний поддерживает два формата хранения данных:

### JSON-формат

JSON-формат представляет собой один файл с иерархической структурой:
- `database_info` - Информация о базе данных
- `company` - Информация о компании
- `sections` - Разделы базы знаний
  - `subsections` - Подразделы
    - `content` - Содержимое подразделов (термины, продукты и т.д.)

Преимущества:
- Простой просмотр и редактирование
- Храниние всей информации в одном файле
- Удобное версионирование через Git

### SQLite-формат

SQLite-формат представляет собой реляционную базу данных со следующими основными таблицами:
- `sections` - Разделы базы знаний
- `subsections` - Подразделы
- `terms` - Термины кибербезопасности
- `products` - Продукты компании
- `search_index` - Индекс полнотекстового поиска

Преимущества:
- Эффективные запросы и поиск
- Поддержка сложных выборок данных
- Полнотекстовый поиск
- Целостность данных через ограничения

## Начало работы

### Требования

- Python 3.7+
- Стандартные библиотеки Python: sqlite3, json, os, re

### Установка

```bash
# Клонирование репозитория
git clone https://github.com/your-username/cybernexus-knowledge-base.git
cd cybernexus-knowledge-base

# Создание директорий для экспорта и резервных копий
mkdir -p exports backups
```

## Использование библиотеки

Библиотека `KnowledgeBaseAccessor` предоставляет унифицированный интерфейс для работы с базой знаний независимо от формата хранения.

### Инициализация

```python
from knowledge_base_accessor import KnowledgeBaseAccessor

# Для работы с JSON
kb_json = KnowledgeBaseAccessor(storage_type="json", path="knowledge_base.json")

# Для работы с SQLite
kb_sqlite = KnowledgeBaseAccessor(storage_type="sqlite", path="knowledge_base.db")
```

### Основные методы

```python
# Получение информации о компании
company_info = kb.get_company_info()

# Получение списка разделов
sections = kb.get_sections()

# Получение конкретного раздела
section = kb.get_section("concepts_basics")

# Получение подраздела
subsection = kb.get_subsection("concepts_basics", "basic_terms")

# Получение информации о продукте
product = kb.get_product("intellectshield")

# Поиск по базе знаний
results = kb.search("аномалии")

# Добавление термина
kb.add_term({
    "term": "Zero-day уязвимость",
    "definition": "Уязвимость, о которой не знает разработчик ПО или оборудования...",
    "related_terms": ["exploit", "patch", "vulnerability"]
})

# Добавление раздела
kb.add_section({
    "id": "new_section",
    "name": "Новый раздел",
    "description": "Описание раздела",
    "subsections": [...]
})

# Экспорт в JSON
kb.export_to_json("exports/exported_kb.json")

# Закрытие соединения
kb.close()
```

## Преобразование между форматами

Для преобразования между форматами используйте скрипт `data_converter.py`:

```bash
# Преобразование из JSON в SQLite
python data_converter.py --to-sqlite --input knowledge_base.json --output knowledge_base.db --backup

# Преобразование из SQLite в JSON
python data_converter.py --to-json --input knowledge_base.db --output knowledge_base_new.json --backup
```

## Примеры

Запустите файл с примерами использования:

```bash
python usage_examples.py
```

## Развитие базы знаний

### Структура базы знаний

База знаний имеет следующую иерархическую структуру:

1. **Концепции и базовые знания**
   - Основные термины кибербезопасности
   - Модели безопасности
   - Жизненный цикл кибератак

2. **Продукты КиберНексус**
   - ИнтеллектЩит (платформа обнаружения аномалий)
   - Другие продукты

3. **Категории киберугроз** (может быть добавлено)
   - Вредоносное ПО
   - Сетевые атаки
   - Социальная инженерия

### Добавление нового контента

1. Определите тип контента (термин, продукт, угроза)
2. Выберите подходящий раздел или создайте новый
3. Используйте соответствующие методы библиотеки для добавления
4. Сохраните изменения в репозитории

### Будущие улучшения

- Интерфейс пользователя для редактирования базы знаний
- Система версионирования для отслеживания изменений в базе знаний
- Расширенные возможности поиска и визуализации
- Интеграция с внешними источниками данных об угрозах

## Лицензия

© 2025, КиберНексус. Все права защищены.

## Модуль сценариев атак

Модуль сценариев атак (threat scenarios) расширяет базу знаний функциональностью для структурированного хранения, поиска и анализа типовых сценариев кибератак.

### Возможности модуля

- Детальное описание сценариев атак с указанием уровня сложности, воздействия и других характеристик
- Структурированное хранение этапов атаки, используемых техник и мер защиты
- Интеграция с фреймворком MITRE ATT&CK для стандартизации описания тактик и техник
- Привязка мер защиты к продуктам компании КиберНексус
- Хранение индикаторов компрометации (IOC) для каждого сценария
- Документирование реальных примеров атак с извлеченными уроками
- Поиск сценариев по различным критериям (теги, техники, продукты)
