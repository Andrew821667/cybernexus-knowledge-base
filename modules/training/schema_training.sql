-- Схема БД для модуля обучения персонала по кибербезопасности

-- Категории обучающих материалов
CREATE TABLE training_categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    parent_id INTEGER,
    order_index INTEGER,
    FOREIGN KEY (parent_id) REFERENCES training_categories(id) ON DELETE SET NULL
);

-- Уровни сложности обучающих материалов
CREATE TABLE training_difficulty_levels (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Роли сотрудников (для таргетированных материалов)
CREATE TABLE employee_roles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Обучающие курсы
CREATE TABLE training_courses (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    category_id INTEGER,
    difficulty_level_id INTEGER,
    duration_minutes INTEGER,
    is_required BOOLEAN DEFAULT 0,
    is_certification BOOLEAN DEFAULT 0,
    certification_validity_days INTEGER,
    creation_date DATE NOT NULL,
    last_updated DATE,
    version TEXT,
    author TEXT,
    FOREIGN KEY (category_id) REFERENCES training_categories(id) ON DELETE SET NULL,
    FOREIGN KEY (difficulty_level_id) REFERENCES training_difficulty_levels(id) ON DELETE SET NULL
);

-- Целевые роли для курсов (многие ко многим)
CREATE TABLE course_target_roles (
    course_id INTEGER,
    role_id INTEGER,
    PRIMARY KEY (course_id, role_id),
    FOREIGN KEY (course_id) REFERENCES training_courses(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES employee_roles(id) ON DELETE CASCADE
);

-- Связь курсов с продуктами компании
CREATE TABLE course_products (
    course_id INTEGER,
    product_id TEXT,
    PRIMARY KEY (course_id, product_id),
    FOREIGN KEY (course_id) REFERENCES training_courses(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Обучающие модули (части курса)
CREATE TABLE training_modules (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    order_index INTEGER,
    duration_minutes INTEGER,
    FOREIGN KEY (course_id) REFERENCES training_courses(id) ON DELETE CASCADE
);

-- Типы обучающих материалов
CREATE TABLE material_types (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Обучающие материалы
CREATE TABLE training_materials (
    id INTEGER PRIMARY KEY,
    module_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    content_text TEXT,
    content_url TEXT,
    material_type_id INTEGER,
    order_index INTEGER,
    duration_minutes INTEGER,
    is_interactive BOOLEAN DEFAULT 0,
    FOREIGN KEY (module_id) REFERENCES training_modules(id) ON DELETE CASCADE,
    FOREIGN KEY (material_type_id) REFERENCES material_types(id) ON DELETE SET NULL
);

-- Теги для материалов
CREATE TABLE material_tags (
    material_id INTEGER,
    tag TEXT,
    PRIMARY KEY (material_id, tag),
    FOREIGN KEY (material_id) REFERENCES training_materials(id) ON DELETE CASCADE
);

-- Тесты
CREATE TABLE training_tests (
    id INTEGER PRIMARY KEY,
    module_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    passing_score INTEGER NOT NULL, -- Процент правильных ответов для прохождения
    time_limit_minutes INTEGER,     -- Ограничение по времени
    max_attempts INTEGER,           -- Максимальное количество попыток
    FOREIGN KEY (module_id) REFERENCES training_modules(id) ON DELETE CASCADE
);

-- Вопросы тестов
CREATE TABLE test_questions (
    id INTEGER PRIMARY KEY,
    test_id INTEGER NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT NOT NULL, -- 'single_choice', 'multiple_choice', 'text_answer'
    difficulty INTEGER,          -- 1-5, где 5 - самый сложный
    points INTEGER DEFAULT 1,    -- Количество баллов за правильный ответ
    order_index INTEGER,
    explanation TEXT,            -- Объяснение правильного ответа
    FOREIGN KEY (test_id) REFERENCES training_tests(id) ON DELETE CASCADE
);

-- Варианты ответов на вопросы
CREATE TABLE test_answers (
    id INTEGER PRIMARY KEY,
    question_id INTEGER NOT NULL,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    order_index INTEGER,
    FOREIGN KEY (question_id) REFERENCES test_questions(id) ON DELETE CASCADE
);

-- Сотрудники (для отслеживания прогресса обучения)
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    department TEXT,
    role_id INTEGER,
    manager_id INTEGER,
    hire_date DATE,
    FOREIGN KEY (role_id) REFERENCES employee_roles(id) ON DELETE SET NULL,
    FOREIGN KEY (manager_id) REFERENCES employees(id) ON DELETE SET NULL
);

-- Прогресс обучения сотрудников по курсам
CREATE TABLE employee_course_progress (
    employee_id INTEGER,
    course_id INTEGER,
    start_date DATE,
    completion_date DATE,
    is_completed BOOLEAN DEFAULT 0,
    completion_percent INTEGER DEFAULT 0,
    last_activity_date DATE,
    certificate_id TEXT,
    expiration_date DATE,      -- Дата истечения срока действия сертификата
    PRIMARY KEY (employee_id, course_id),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES training_courses(id) ON DELETE CASCADE
);

-- Прогресс по модулям курса
CREATE TABLE employee_module_progress (
    employee_id INTEGER,
    module_id INTEGER,
    is_completed BOOLEAN DEFAULT 0,
    completion_date DATE,
    time_spent_minutes INTEGER DEFAULT 0,
    PRIMARY KEY (employee_id, module_id),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES training_modules(id) ON DELETE CASCADE
);

-- Результаты прохождения тестов
CREATE TABLE test_attempts (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    test_id INTEGER NOT NULL,
    attempt_number INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    score INTEGER,              -- Процент правильных ответов
    passed BOOLEAN,             -- Успешно пройден или нет
    time_spent_minutes INTEGER,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES training_tests(id) ON DELETE CASCADE,
    UNIQUE (employee_id, test_id, attempt_number)
);

-- Ответы сотрудников на вопросы тестов
CREATE TABLE employee_test_answers (
    attempt_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_answers TEXT,     -- JSON массив ID выбранных ответов или текстовый ответ
    is_correct BOOLEAN,
    points_earned INTEGER,
    PRIMARY KEY (attempt_id, question_id),
    FOREIGN KEY (attempt_id) REFERENCES test_attempts(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES test_questions(id) ON DELETE CASCADE
);

-- Комментарии и отзывы о материалах
CREATE TABLE material_feedback (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    rating INTEGER,            -- Оценка от 1 до 5
    comment TEXT,
    submission_date DATETIME NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES training_materials(id) ON DELETE CASCADE
);

-- Расписание обязательных тренингов
CREATE TABLE training_schedule (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL,
    target_role_id INTEGER,    -- NULL если для всех сотрудников
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reminder_days INTEGER,     -- За сколько дней высылать напоминание
    description TEXT,
    FOREIGN KEY (course_id) REFERENCES training_courses(id) ON DELETE CASCADE,
    FOREIGN KEY (target_role_id) REFERENCES employee_roles(id) ON DELETE SET NULL
);

-- Интеграция с инцидентами безопасности
CREATE TABLE security_incident_trainings (
    incident_id INTEGER,
    course_id INTEGER,
    recommendation_type TEXT, -- 'preventive', 'response'
    priority INTEGER,         -- 1-5, где 5 - высший приоритет
    PRIMARY KEY (incident_id, course_id),
    FOREIGN KEY (course_id) REFERENCES training_courses(id) ON DELETE CASCADE
);

-- Полнотекстовый поиск для обучающих материалов
CREATE VIRTUAL TABLE training_search_index USING fts5(
    content,
    category,
    title,
    entity_type,  -- 'course', 'module', 'material', 'test'
    entity_id
);
