-- Схема БД для хранения данных о соответствии нормативным требованиям

-- Нормативные документы (законы, стандарты, регламенты)
CREATE TABLE compliance_documents (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL,              -- Короткий код/номер документа (например, GDPR, 152-ФЗ)
    name TEXT NOT NULL,              -- Полное название документа
    description TEXT,                -- Описание документа
    issuer TEXT,                     -- Орган, выпустивший документ
    issue_date DATE,                 -- Дата выпуска
    effective_date DATE,             -- Дата вступления в силу
    scope TEXT,                      -- Область применения
    region TEXT,                     -- Регион действия (страна, международный и т.д.)
    url TEXT,                        -- Ссылка на официальный документ
    document_type TEXT               -- Тип документа (закон, стандарт, руководство)
);

-- Требования нормативных документов
CREATE TABLE compliance_requirements (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    code TEXT NOT NULL,              -- Код требования (например, статья, пункт)
    name TEXT NOT NULL,              -- Название требования
    description TEXT,                -- Описание требования
    priority TEXT,                   -- Приоритет (критический, высокий, средний, низкий)
    FOREIGN KEY (document_id) REFERENCES compliance_documents(id) ON DELETE CASCADE
);

-- Контрольные меры для обеспечения соответствия
CREATE TABLE compliance_controls (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    implementation_status TEXT,      -- Статус внедрения (внедрено, в процессе, запланировано, не применимо)
    responsible_role TEXT,           -- Ответственная роль/должность
    verification_method TEXT,        -- Метод проверки соответствия
    last_assessment_date DATE,       -- Дата последней оценки
    assessment_result TEXT,          -- Результат оценки (соответствует, частично соответствует, не соответствует)
    next_assessment_date DATE        -- Дата следующей запланированной оценки
);

-- Связь между требованиями и контрольными мерами (многие ко многим)
CREATE TABLE requirement_control_mapping (
    requirement_id INTEGER,
    control_id INTEGER,
    PRIMARY KEY (requirement_id, control_id),
    FOREIGN KEY (requirement_id) REFERENCES compliance_requirements(id) ON DELETE CASCADE,
    FOREIGN KEY (control_id) REFERENCES compliance_controls(id) ON DELETE CASCADE
);

-- Связь продуктов компании с контрольными мерами
CREATE TABLE product_compliance_mapping (
    product_id TEXT,                 -- ID продукта из основной БД
    control_id INTEGER,              -- ID контрольной меры
    compliance_level TEXT,           -- Уровень соответствия (полный, частичный, отсутствует)
    notes TEXT,                      -- Примечания по реализации
    PRIMARY KEY (product_id, control_id),
    FOREIGN KEY (control_id) REFERENCES compliance_controls(id) ON DELETE CASCADE
);

-- Отчеты о соответствии
CREATE TABLE compliance_reports (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    document_id INTEGER,             -- Нормативный документ, для которого создан отчет
    creation_date DATE NOT NULL,
    author TEXT,
    summary TEXT,
    overall_compliance_level TEXT,   -- Общий уровень соответствия
    recommendations TEXT,            -- Рекомендации
    file_path TEXT,                  -- Путь к файлу отчета (если есть)
    FOREIGN KEY (document_id) REFERENCES compliance_documents(id) ON DELETE SET NULL
);

-- Несоответствия (gaps) и план действий
CREATE TABLE compliance_gaps (
    id INTEGER PRIMARY KEY,
    requirement_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    impact TEXT,                     -- Влияние несоответствия
    risk_level TEXT,                 -- Уровень риска
    remediation_plan TEXT,           -- План устранения
    due_date DATE,                   -- Срок устранения
    status TEXT,                     -- Статус (открыто, в работе, закрыто)
    responsible_person TEXT,         -- Ответственный
    FOREIGN KEY (requirement_id) REFERENCES compliance_requirements(id) ON DELETE CASCADE
);

-- Полнотекстовый поиск
CREATE VIRTUAL TABLE compliance_search_index USING fts5(
    content,
    document_code,
    document_name,
    requirement_code,
    entity_type,
    entity_id
);
