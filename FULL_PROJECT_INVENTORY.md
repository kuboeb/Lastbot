# Полная инвентаризация проекта LASTBOT

## Статистика:
- **Файлов Python**: 116
- **Файлов HTML**: 55
- **Таблиц в БД**: 30
- **Размер БД**: 11 MB
- **Дата бэкапа**: 16 июня 2025

## Структура проекта:

### Основные компоненты:
- `bot.py` - главный файл Telegram бота
- `database.py` - модели SQLAlchemy
- `config.py` - конфигурация
- `requirements.txt` - зависимости

### Модули бота:
- `handlers/` - обработчики команд и состояний
- `keyboards/` - клавиатуры
- `states/` - FSM состояния
- `middlewares/` - промежуточные обработчики
- `utils/` - вспомогательные функции

### Админ-панель:
- `admin_panel/` - основная версия
- `admin_panel.backup/` - резервная копия
- `admin_panel/templates/` - HTML шаблоны
- `admin_panel/static/` - CSS/JS файлы
- `admin_panel/routes/` - маршруты Flask

### Facebook интеграция:
- `utils/fb_conversion_sender.py` - отправка конверсий
- `handlers/facebook_utils.py` - сохранение fbclid
- `admin_panel/routes/facebook.py` - админка для FB

### База данных:
- 30 таблиц
- Основные: applications, bot_users, traffic_sources
- Facebook: facebook_conversions, user_clicks
- Дамп: database_backup_20250616_143319.sql

### Systemd сервисы:
- `crypto-bot.service` - Telegram бот
- `crypto-admin.service` - админ-панель

## Доступы:
- Админка: http://145.223.80.72:8000
- Facebook конверсии: http://145.223.80.72:8000/facebook/
- БД: PostgreSQL на localhost:5432

## GitHub:
- Репозиторий: https://github.com/kuboeb/Lastbot.git
- Ветка: almost-main-v2
- Теги: ALMOST_MAIN_BACKUP_V2_FINAL
