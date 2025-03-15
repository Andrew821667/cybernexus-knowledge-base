-- Схема расширения для модуля сценариев атак (threat scenarios)

-- Таблица сценариев атак
CREATE TABLE attack_scenarios (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    difficulty_level TEXT CHECK(difficulty_level IN ('Low', 'Medium', 'High', 'Critical')),
    impact_level TEXT CHECK(impact_level IN ('Low', 'Medium', 'High', 'Critical')),
    typical_duration TEXT,
    detection_complexity TEXT CHECK(detection_complexity IN ('Low', 'Medium', 'High')),
    mitigation_complexity TEXT CHECK(mitigation_complexity IN ('Low', 'Medium', 'High')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT,
    mitre_attack_ids TEXT,
    threat_actors TEXT
);

-- Таблица для связи сценариев атак с подразделами
CREATE TABLE scenario_subsections (
    scenario_id INTEGER,
    subsection_id TEXT,
    PRIMARY KEY (scenario_id, subsection_id),
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (subsection_id) REFERENCES subsections(id) ON DELETE CASCADE
);

-- Таблица для связи сценариев атак с этапами атак
CREATE TABLE scenario_attack_stages (
    scenario_id INTEGER,
    stage_id INTEGER,
    order_index INTEGER,
    description TEXT,
    PRIMARY KEY (scenario_id, stage_id),
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES attack_stages(id) ON DELETE CASCADE
);

-- Таблица для целевых активов (на что направлена атака)
CREATE TABLE scenario_target_assets (
    scenario_id INTEGER,
    asset_type TEXT,
    asset_description TEXT,
    PRIMARY KEY (scenario_id, asset_type),
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE
);

-- Таблица для техник, используемых в сценарии атаки
CREATE TABLE scenario_techniques (
    id INTEGER PRIMARY KEY,
    scenario_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    mitre_technique_id TEXT,
    stage_id INTEGER,
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES attack_stages(id) ON DELETE SET NULL
);

-- Таблица для средств защиты от сценария атаки
CREATE TABLE scenario_mitigations (
    id INTEGER PRIMARY KEY,
    scenario_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    effectiveness TEXT CHECK(effectiveness IN ('Low', 'Medium', 'High')),
    implementation_complexity TEXT CHECK(implementation_complexity IN ('Low', 'Medium', 'High')),
    stage_id INTEGER,
    product_id TEXT,
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE,
    FOREIGN KEY (stage_id) REFERENCES attack_stages(id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- Таблица для индикаторов компрометации (IOC) для конкретного сценария
CREATE TABLE scenario_iocs (
    id INTEGER PRIMARY KEY,
    scenario_id INTEGER,
    ioc_type TEXT CHECK(ioc_type IN ('IP', 'Domain', 'URL', 'File Hash', 'Registry', 'Email', 'Process', 'Network', 'Other')),
    ioc_value TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE
);

-- Таблица для примеров реальных инцидентов, связанных со сценарием
CREATE TABLE scenario_real_world_examples (
    id INTEGER PRIMARY KEY,
    scenario_id INTEGER,
    incident_name TEXT NOT NULL,
    incident_date DATE,
    affected_organizations TEXT,
    description TEXT,
    outcome TEXT,
    lessons_learned TEXT,
    references TEXT,
    FOREIGN KEY (scenario_id) REFERENCES attack_scenarios(id) ON DELETE CASCADE
);

-- Обновление индекса полнотекстового поиска
-- Добавление триггеров для автоматического обновления поискового индекса

-- Триггер для добавления сценария атаки в поисковый индекс
CREATE TRIGGER tr_attack_scenario_insert AFTER INSERT ON attack_scenarios
BEGIN
    INSERT INTO search_index (content, section, subsection, entity_type, entity_id)
    VALUES (
        NEW.name || ' ' || NEW.description || ' ' || NEW.tags || ' ' || NEW.threat_actors,
        'attack_scenarios',
        'scenario',
        'attack_scenario',
        NEW.id
    );
END;

-- Триггер для обновления сценария атаки в поисковом индексе
CREATE TRIGGER tr_attack_scenario_update AFTER UPDATE ON attack_scenarios
BEGIN
    UPDATE search_index
    SET content = NEW.name || ' ' || NEW.description || ' ' || NEW.tags || ' ' || NEW.threat_actors
    WHERE entity_type = 'attack_scenario' AND entity_id = NEW.id;
END;

-- Триггер для удаления сценария атаки из поискового индекса
CREATE TRIGGER tr_attack_scenario_delete AFTER DELETE ON attack_scenarios
BEGIN
    DELETE FROM search_index
    WHERE entity_type = 'attack_scenario' AND entity_id = OLD.id;
END;

-- Триггер для автоматического обновления даты изменения сценария
CREATE TRIGGER tr_attack_scenario_update_timestamp AFTER UPDATE ON attack_scenarios
BEGIN
    UPDATE attack_scenarios
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;
