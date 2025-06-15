-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Добавление начальных данных для админа
INSERT INTO admins (username, password_hash, created_at) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGMuRgQrGK.', NOW())
ON CONFLICT (username) DO NOTHING;

-- Добавление начальных данных для оператора
INSERT INTO operators (username, password_hash, created_at) 
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGMuRgQrGK.', NOW())
ON CONFLICT (username) DO NOTHING;

-- Добавление начальных настроек бота
INSERT INTO bot_settings (key, value) VALUES 
('bot_enabled', 'true'),
('bot_start_time', NOW()::text)
ON CONFLICT (key) DO NOTHING;

-- Добавление начальных текстов бота
INSERT INTO bot_texts (key, category, text) VALUES
('welcome_message', 'main', '🚀 Добро пожаловать!'),
('registration_complete', 'registration', '✅ Регистрация завершена!')
ON CONFLICT (key) DO NOTHING;

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_bot_users_user_id ON bot_users(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);
CREATE INDEX IF NOT EXISTS idx_traffic_sources_tracking_code ON traffic_sources(tracking_code);
CREATE INDEX IF NOT EXISTS idx_user_actions_user_id_created ON user_actions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_tracking_events_source_id_created ON tracking_events(source_id, created_at);
