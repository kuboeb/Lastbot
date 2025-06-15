-- Создание таблиц для Telegram бота курса криптовалют

-- Таблица админов
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица операторов
CREATE TABLE IF NOT EXISTS operators (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица настроек бота
CREATE TABLE IF NOT EXISTS bot_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица пользователей бота
CREATE TABLE IF NOT EXISTS bot_users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE,
    username VARCHAR(100),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP,
    source_id INTEGER,
    has_application BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    registration_step VARCHAR(50)
);

-- Таблица источников трафика
CREATE TABLE IF NOT EXISTS traffic_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    platform VARCHAR(50),
    tracking_code VARCHAR(100) UNIQUE,
    link VARCHAR(500),
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица заявок
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE REFERENCES bot_users(user_id),
    full_name VARCHAR(255),
    country VARCHAR(100),
    phone VARCHAR(50),
    preferred_time VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referrer_id BIGINT,
    source_id INTEGER REFERENCES traffic_sources(id)
);

-- Таблица рефералов
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT,
    referred_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'registered'
);

-- Таблица комментариев к заявкам
CREATE TABLE IF NOT EXISTS application_comments (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id),
    admin_id INTEGER REFERENCES admins(id),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица действий пользователей
CREATE TABLE IF NOT EXISTS user_actions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица текстов бота
CREATE TABLE IF NOT EXISTS bot_texts (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE,
    category VARCHAR(50),
    text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES admins(id)
);

-- Таблица рассылок
CREATE TABLE IF NOT EXISTS broadcasts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    message TEXT,
    target_audience JSONB,
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    status VARCHAR(20),
    stats JSONB
);

-- Таблица отслеживания переходов
CREATE TABLE IF NOT EXISTS tracking_events (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES traffic_sources(id),
    user_id BIGINT,
    event_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица интеграций
CREATE TABLE IF NOT EXISTS integrations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    type VARCHAR(50),
    settings JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов интеграций
CREATE TABLE IF NOT EXISTS integration_logs (
    id SERIAL PRIMARY KEY,
    integration_id INTEGER REFERENCES integrations(id),
    application_id INTEGER REFERENCES applications(id),
    status VARCHAR(20),
    request_data JSONB,
    response_data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сообщений от операторов
CREATE TABLE IF NOT EXISTS operator_messages (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(50),
    user_id BIGINT,
    message TEXT,
    operator_id VARCHAR(50),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered BOOLEAN DEFAULT FALSE
);

-- Таблица неудачных конверсий
CREATE TABLE IF NOT EXISTS failed_conversions (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id),
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица системных метрик
CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица состояний inline кнопок
CREATE TABLE IF NOT EXISTS inline_states (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    message_id BIGINT,
    keyboard_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, message_id)
);

-- Таблица click_ids для отслеживания
CREATE TABLE IF NOT EXISTS user_clicks (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    click_id VARCHAR(255),
    platform VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time ON system_metrics(metric_name, recorded_at);
CREATE INDEX IF NOT EXISTS idx_inline_states_created ON inline_states(created_at);
CREATE INDEX IF NOT EXISTS idx_bot_users_user_id ON bot_users(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);
CREATE INDEX IF NOT EXISTS idx_traffic_sources_tracking_code ON traffic_sources(tracking_code);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id_created ON user_actions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tracking_events_source_id_created ON tracking_events(source_id, created_at);
