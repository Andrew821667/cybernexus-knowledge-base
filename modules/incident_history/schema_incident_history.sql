-- Схема для хранения данных о хронологии инцидентов кибербезопасности

-- Категории инцидентов
CREATE TABLE incident_categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Основная таблица инцидентов
CREATE TABLE security_incidents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    date_occurred DATE NOT NULL,  -- Дата инцидента
    date_discovered DATE,         -- Дата обнаружения (может отличаться от даты инцидента)
    date_resolved DATE,           -- Дата разрешения инцидента
    severity TEXT NOT NULL,       -- Критичность: Critical, High, Medium, Low
    category_id INTEGER,          -- Ссылка на категорию инцидента
    affected_systems TEXT,        -- Затронутые системы
    impact_description TEXT,      -- Описание воздействия
    estimated_financial_impact REAL,  -- Оценка финансового ущерба
    organizations_affected INTEGER,   -- Примерное количество затронутых организаций
    source_url TEXT,              -- Ссылка на источник информации
    FOREIGN KEY (category_id) REFERENCES incident_categories(id) ON DELETE SET NULL
);

-- Теги для инцидентов
CREATE TABLE incident_tags (
    incident_id INTEGER,
    tag TEXT,
    PRIMARY KEY (incident_id, tag),
    FOREIGN KEY (incident_id) REFERENCES security_incidents(id) ON DELETE CASCADE
);

-- Связь с MITRE ATT&CK техниками
CREATE TABLE incident_techniques (
    incident_id INTEGER,
    technique_id TEXT,  -- ID техники из MITRE ATT&CK (например, T1566)
    description TEXT,   -- Описание использования конкретной техники
    PRIMARY KEY (incident_id, technique_id),
    FOREIGN KEY (incident_id) REFERENCES security_incidents(id) ON DELETE CASCADE
);

-- Фазы инцидента
CREATE TABLE incident_phases (
    id INTEGER PRIMARY KEY,
    incident_id INTEGER NOT NULL,
    phase_name TEXT NOT NULL,  -- Например: Initial Access, Execution, Persistence, ...
    description TEXT,
    order_index INTEGER,       -- Порядок фаз
    FOREIGN KEY (incident_id) REFERENCES security_incidents(id) ON DELETE CASCADE
);

-- Извлеченные уроки
CREATE TABLE lessons_learned (
    id INTEGER PRIMARY KEY,
    incident_id INTEGER NOT NULL,
    lesson TEXT NOT NULL,       -- Извлеченный урок
    recommendation TEXT,        -- Рекомендация на будущее
    priority TEXT,              -- High, Medium, Low
    FOREIGN KEY (incident_id) REFERENCES security_incidents(id) ON DELETE CASCADE
);

-- Корректирующие действия
CREATE TABLE corrective_actions (
    id INTEGER PRIMARY KEY,
    lesson_id INTEGER NOT NULL,
    action TEXT NOT NULL,        -- Описание корректирующего действия
    status TEXT,                 -- Planned, In Progress, Completed
    FOREIGN KEY (lesson_id) REFERENCES lessons_learned(id) ON DELETE CASCADE
);

-- Связанные страны и регионы
CREATE TABLE incident_regions (
    incident_id INTEGER,
    region TEXT,                 -- Страна или регион
    is_source BOOLEAN,           -- True - источник атаки, False - цель атаки
    PRIMARY KEY (incident_id, region, is_source),
    FOREIGN KEY (incident_id) REFERENCES security_incidents(id) ON DELETE CASCADE
);

-- Обновление индекса полнотекстового поиска
CREATE VIRTUAL TABLE incident_search_index USING fts5(
    content,
    title,
    description,
    incident_id,
    date_occurred
);

-- Предзаполненные категории инцидентов
INSERT INTO incident_categories (name, description) VALUES
('Malware', 'Инциденты, связанные с вредоносным ПО, включая вирусы, трояны, шпионское ПО и программы-вымогатели'),
('Data Breach', 'Утечка или кража конфиденциальных данных'),
('DDoS', 'Распределенные атаки типа "отказ в обслуживании"'),
('Phishing', 'Социальная инженерия, направленная на получение конфиденциальной информации'),
('Zero-day Exploitation', 'Эксплуатация ранее неизвестных уязвимостей'),
('Insider Threat', 'Угрозы, исходящие от сотрудников организации'),
('Supply Chain Attack', 'Атаки через компрометацию цепочки поставок программного обеспечения'),
('APT', 'Целенаправленные продвинутые постоянные угрозы');