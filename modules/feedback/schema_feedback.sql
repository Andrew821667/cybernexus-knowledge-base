-- Схема БД для хранения обратной связи о базе знаний по кибербезопасности

-- Таблица обратной связи
CREATE TABLE feedback_items (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL,  -- Тип обратной связи (comment, suggestion, error_report, feature_request)
    user_id TEXT,        -- ID пользователя (если авторизован)
    user_name TEXT,      -- Имя пользователя
    user_email TEXT,     -- Email пользователя
    content TEXT NOT NULL, -- Содержание обратной связи
    entity_type TEXT,    -- Тип сущности, к которой относится (section, subsection, term, product)
    entity_id TEXT,      -- ID сущности
    status TEXT NOT NULL DEFAULT 'new', -- Статус обработки
    priority TEXT NOT NULL DEFAULT 'medium', -- Приоритет
    created_at TEXT NOT NULL, -- Дата создания
    updated_at TEXT,     -- Дата обновления
    assigned_to TEXT,    -- Кому назначено
    upvotes INTEGER DEFAULT 0 -- Количество голосов за
);

-- Таблица для дополнительной информации о предложениях
CREATE TABLE suggestions (
    feedback_id INTEGER PRIMARY KEY,
    benefits TEXT, -- Описание преимуществ предложения
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица для дополнительной информации о сообщениях об ошибках
CREATE TABLE error_reports (
    feedback_id INTEGER PRIMARY KEY,
    error_type TEXT, -- Тип ошибки
    expected_behavior TEXT, -- Ожидаемое поведение
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица для дополнительной информации о запросах функциональности
CREATE TABLE feature_requests (
    feedback_id INTEGER PRIMARY KEY,
    use_case TEXT, -- Сценарий использования
    business_value TEXT, -- Бизнес-ценность
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица тегов для обратной связи
CREATE TABLE feedback_tags (
    feedback_id INTEGER,
    tag TEXT,
    PRIMARY KEY (feedback_id, tag),
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица вложений для обратной связи
CREATE TABLE feedback_attachments (
    id INTEGER PRIMARY KEY,
    feedback_id INTEGER,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица комментариев к обратной связи (для диалогов)
CREATE TABLE feedback_comments (
    id INTEGER PRIMARY KEY,
    feedback_id INTEGER,
    user_id TEXT,
    user_name TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица для связи обратной связи с существующими разделами и подразделами
CREATE TABLE feedback_entity_relations (
    feedback_id INTEGER,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    PRIMARY KEY (feedback_id, entity_type, entity_id),
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Таблица истории изменений статусов обратной связи
CREATE TABLE feedback_status_history (
    id INTEGER PRIMARY KEY,
    feedback_id INTEGER,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT,
    changed_at TEXT NOT NULL,
    comment TEXT,
    FOREIGN KEY (feedback_id) REFERENCES feedback_items(id) ON DELETE CASCADE
);

-- Полнотекстовый поиск
CREATE VIRTUAL TABLE feedback_search USING fts5(
    content,
    type,
    entity_type,
    entity_id,
    user_name,
    tags
);

-- Триггер для обновления поля updated_at при изменении обратной связи
CREATE TRIGGER update_feedback_timestamp 
AFTER UPDATE ON feedback_items
BEGIN
    UPDATE feedback_items 
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Триггер для обновления поискового индекса при добавлении обратной связи
CREATE TRIGGER feedback_insert_search
AFTER INSERT ON feedback_items
BEGIN
    INSERT INTO feedback_search (
        rowid,
        content,
        type,
        entity_type,
        entity_id,
        user_name,
        tags
    )
    SELECT
        NEW.id,
        NEW.content,
        NEW.type,
        NEW.entity_type,
        NEW.entity_id,
        NEW.user_name,
        (SELECT group_concat(tag, ' ') FROM feedback_tags WHERE feedback_id = NEW.id)
    ;
END;

-- Триггер для обновления поискового индекса при обновлении обратной связи
CREATE TRIGGER feedback_update_search
AFTER UPDATE ON feedback_items
BEGIN
    UPDATE feedback_search
    SET
        content = NEW.content,
        type = NEW.type,
        entity_type = NEW.entity_type,
        entity_id = NEW.entity_id,
        user_name = NEW.user_name,
        tags = (SELECT group_concat(tag, ' ') FROM feedback_tags WHERE feedback_id = NEW.id)
    WHERE rowid = NEW.id;
END;

-- Триггер для удаления из поискового индекса при удалении обратной связи
CREATE TRIGGER feedback_delete_search
AFTER DELETE ON feedback_items
BEGIN
    DELETE FROM feedback_search WHERE rowid = OLD.id;
END;
