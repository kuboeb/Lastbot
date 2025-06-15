import os
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Config:
    """Основная конфигурация приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://cryptobot:password@localhost:5432/crypto_course_db")
    
    # Админ панель
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    
    # Операторская панель
    OPERATOR_USERNAME: str = os.getenv("OPERATOR_USERNAME", "operator")
    OPERATOR_PASSWORD: str = os.getenv("OPERATOR_PASSWORD", "operator")
    
    # API ключи
    OPERATOR_API_KEY: str = os.getenv("OPERATOR_API_KEY", "")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")
    
    # Webhook подписи
    WEBHOOK_SIGNATURE_KEY: str = os.getenv("WEBHOOK_SIGNATURE_KEY", "")
    
    # Порты
    ADMIN_PANEL_PORT: int = int(os.getenv("ADMIN_PANEL_PORT", "8000"))
    OPERATOR_PANEL_PORT: int = int(os.getenv("OPERATOR_PANEL_PORT", "8001"))
    BOT_API_PORT: int = int(os.getenv("BOT_API_PORT", "8002"))
    BOT_WEBHOOK_PORT: int = int(os.getenv("BOT_WEBHOOK_PORT", "3000"))
    
    # Сервер
    SERVER_IP: str = os.getenv("SERVER_IP", "145.223.80.72")
    SERVER_DOMAIN: Optional[str] = os.getenv("SERVER_DOMAIN")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Временная зона
    TZ: str = os.getenv("TZ", "Europe/Moscow")
    
    # Безопасность
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")
    SECRET_KEY_ROTATION_DAYS: int = int(os.getenv("SECRET_KEY_ROTATION_DAYS", "30"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    SESSION_COOKIE_SECURE: bool = os.getenv("SESSION_COOKIE_SECURE", "True").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = os.getenv("SESSION_COOKIE_HTTPONLY", "True").lower() == "true"
    WTF_CSRF_ENABLED: bool = os.getenv("WTF_CSRF_ENABLED", "True").lower() == "true"

# Создаем экземпляр конфигурации
config = Config()
