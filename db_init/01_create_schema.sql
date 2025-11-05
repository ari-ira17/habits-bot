-- Создание таблицы пользователей
CREATE TABLE users (
    id BIGINT PRIMARY KEY, -- Telegram user ID
    timezone_offset INTEGER -- Смещение пользователя от UTC в секундах
);

-- Создание таблицы привычек
CREATE TABLE habits (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    reminder_config JSONB NOT NULL, -- Хранит конфигурацию напоминаний
    last_reminded_at TIMESTAMP WITH TIME ZONE,
    next_reminder_datetime_utc TIMESTAMP WITH TIME ZONE,

    -- Внешний ключ на таблицу users
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Создание таблицы выполнений привычек
CREATE TABLE habit_completions (
    id SERIAL PRIMARY KEY,
    habit_id INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Внешний ключ на таблицу habits
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);
