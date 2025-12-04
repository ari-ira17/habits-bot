CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    timezone_offset INTEGER 
);

CREATE TABLE habits (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    reminder_config JSONB NOT NULL
    last_reminded_at TIMESTAMP WITH TIME ZONE,
    next_reminder_datetime_utc TIMESTAMP WITH TIME ZONE,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE habit_completions (
    id SERIAL PRIMARY KEY,
    habit_id INTEGER NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,

    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);
