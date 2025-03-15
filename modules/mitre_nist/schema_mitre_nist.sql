-- Схема для хранения данных MITRE ATT&CK и NIST

-- Тактики MITRE ATT&CK
CREATE TABLE mitre_tactics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT
);

-- Техники MITRE ATT&CK
CREATE TABLE mitre_techniques (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    detection TEXT,
    mitigation TEXT
);

-- Связь между тактиками и техниками MITRE ATT&CK (многие ко многим)
CREATE TABLE mitre_tactic_technique_mappings (
    tactic_id TEXT,
    technique_id TEXT,
    PRIMARY KEY (tactic_id, technique_id),
    FOREIGN KEY (tactic_id) REFERENCES mitre_tactics(id) ON DELETE CASCADE,
    FOREIGN KEY (technique_id) REFERENCES mitre_techniques(id) ON DELETE CASCADE
);

-- Подтехники MITRE ATT&CK
CREATE TABLE mitre_subtechniques (
    id TEXT PRIMARY KEY,
    parent_technique_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    detection TEXT,
    mitigation TEXT,
    FOREIGN KEY (parent_technique_id) REFERENCES mitre_techniques(id) ON DELETE CASCADE
);

-- Категории NIST (CSF, 800-53, etc.)
CREATE TABLE nist_categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    framework TEXT NOT NULL,
    description TEXT
);

-- Контролы NIST
CREATE TABLE nist_controls (
    id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    implementation_guidance TEXT,
    FOREIGN KEY (category_id) REFERENCES nist_categories(id) ON DELETE CASCADE
);

-- Связь между MITRE ATT&CK и NIST
CREATE TABLE mitre_nist_mappings (
    mitre_id TEXT NOT NULL,
    nist_id TEXT NOT NULL,
    mapping_type TEXT CHECK (mapping_type IN ('tactic', 'technique', 'subtechnique')),
    description TEXT,
    PRIMARY KEY (mitre_id, nist_id, mapping_type)
);

-- Связь между термином и MITRE ATT&CK
CREATE TABLE term_mitre_mappings (
    term_id INTEGER,
    mitre_id TEXT,
    mapping_type TEXT CHECK (mapping_type IN ('tactic', 'technique', 'subtechnique')),
    PRIMARY KEY (term_id, mitre_id, mapping_type),
    FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
);

-- Связь между типом угрозы и MITRE ATT&CK
CREATE TABLE threat_mitre_mappings (
    threat_id INTEGER,
    mitre_id TEXT,
    mapping_type TEXT CHECK (mapping_type IN ('tactic', 'technique', 'subtechnique')),
    PRIMARY KEY (threat_id, mitre_id, mapping_type),
    FOREIGN KEY (threat_id) REFERENCES threat_types(id) ON DELETE CASCADE
);

-- Связь между продуктом и MITRE ATT&CK (какие техники блокирует)
CREATE TABLE product_mitre_mappings (
    product_id TEXT,
    mitre_id TEXT,
    mapping_type TEXT CHECK (mapping_type IN ('tactic', 'technique', 'subtechnique')),
    effectiveness TEXT CHECK (effectiveness IN ('High', 'Medium', 'Low')),
    description TEXT,
    PRIMARY KEY (product_id, mitre_id, mapping_type),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Связь между продуктом и NIST
CREATE TABLE product_nist_mappings (
    product_id TEXT,
    nist_id TEXT,
    compliance_level TEXT CHECK (compliance_level IN ('Full', 'Partial', 'None')),
    description TEXT,
    PRIMARY KEY (product_id, nist_id),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
