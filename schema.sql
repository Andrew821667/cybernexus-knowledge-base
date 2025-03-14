-- Схема БД для хранения базы знаний по кибербезопасности

-- Информация о базе данных
CREATE TABLE database_info (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    version TEXT NOT NULL,
    last_updated DATE NOT NULL,
    description TEXT
);

-- Информация о компании
CREATE TABLE company (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    mission TEXT,
    unique_value TEXT,
    foundation_year INTEGER
);

-- Основные разделы
CREATE TABLE sections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER
);

-- Подразделы
CREATE TABLE subsections (
    id TEXT PRIMARY KEY,
    section_id TEXT NOT NULL,
    name TEXT NOT NULL,
    order_index INTEGER,
    FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
);

-- Термины кибербезопасности
CREATE TABLE terms (
    id INTEGER PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    term TEXT NOT NULL,
    definition TEXT NOT NULL,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
);

-- Связанные термины
CREATE TABLE related_terms (
    term_id INTEGER,
    related_term TEXT,
    PRIMARY KEY (term_id, related_term),
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
);

-- Модели безопасности
CREATE TABLE security_models (
    id INTEGER PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
);

-- Компоненты моделей безопасности
CREATE TABLE model_components (
    id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (model_id) REFERENCES security_models(id) ON DELETE CASCADE
);

-- Меры защиты для компонентов
CREATE TABLE component_measures (
    component_id INTEGER,
    measure TEXT,
    PRIMARY KEY (component_id, measure),
    FOREIGN KEY (component_id) REFERENCES model_components(id) ON DELETE CASCADE
);

-- Продукты компании
CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    subsection_id TEXT,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE SET NULL
);

-- Целевая аудитория продуктов
CREATE TABLE product_audience (
    product_id TEXT,
    audience TEXT,
    PRIMARY KEY (product_id, audience),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Ключевые особенности продуктов
CREATE TABLE product_features (
    product_id TEXT,
    feature TEXT,
    PRIMARY KEY (product_id, feature),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Технические характеристики продуктов
CREATE TABLE product_technology (
    id INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL,
    core TEXT,
    architecture TEXT,
    visualization TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Источники данных для продуктов
CREATE TABLE product_data_sources (
    technology_id INTEGER,
    data_source TEXT,
    PRIMARY KEY (technology_id, data_source),
    FOREIGN KEY (technology_id) REFERENCES product_technology(id) ON DELETE CASCADE
);

-- Примеры внедрения продуктов (кейсы)
CREATE TABLE case_studies (
    id INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL,
    customer TEXT NOT NULL,
    challenge TEXT,
    solution TEXT,
    results TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Типы киберугроз
CREATE TABLE threat_types (
    id INTEGER PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    name TEXT NOT NULL,
    definition TEXT,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
);

-- Примеры для типов угроз
CREATE TABLE threat_examples (
    threat_id INTEGER,
    example TEXT,
    PRIMARY KEY (threat_id, example),
    FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
);

-- Индикаторы угроз
CREATE TABLE threat_indicators (
    threat_id INTEGER,
    indicator TEXT,
    PRIMARY KEY (threat_id, indicator),
    FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
);

-- Методы защиты от угроз
CREATE TABLE threat_protection (
    threat_id INTEGER,
    protection TEXT,
    PRIMARY KEY (threat_id, protection),
    FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
);

-- Жизненный цикл кибератак
CREATE TABLE attack_stages (
    id INTEGER PRIMARY KEY,
    subsection_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    order_index INTEGER,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
);

-- Примеры для этапов атак
CREATE TABLE attack_stage_examples (
    stage_id INTEGER,
    example TEXT,
    PRIMARY KEY (stage_id, example),
    FOREIGN KEY (stage_id) REFERENCES attack_stages(id) ON DELETE CASCADE
);

-- Контрмеры для этапов атак
CREATE TABLE attack_stage_countermeasures (
    stage_id INTEGER,
    countermeasure TEXT,
    PRIMARY KEY (stage_id, countermeasure),
    FOREIGN KEY (stage_id) REFERENCES attack_stages(id) ON DELETE CASCADE
);

-- Полнотекстовый поиск
CREATE VIRTUAL TABLE search_index USING fts5(
    content,
    section,
    subsection,
    entity_type,
    entity_id
);
