# Состояние проекта - ПОЧТИ ГЛАВНЫЙ V2

## Дата: 16 июня 2025

### ✅ Работающие компоненты:

1. **Telegram Bot**
   - Полная воронка регистрации
   - Реферальная система
   - Отслеживание источников трафика
   - Автоматическая отправка Facebook конверсий

2. **Админ-панель (http://145.223.80.72:8000)**
   - Управление заявками
   - Управление пользователями
   - Редактор текстов
   - Источники трафика
   - Facebook конверсии (/facebook/)
   - Базовый функционал рассылок

3. **Facebook Integration**
   - Автоматическая отправка конверсий
   - Отслеживание fbclid
   - Статистика конверсий

### ❌ Требует доработки:
   - Полный функционал рассылок
   - Экспорт данных
   - Google Ads интеграция

### 🔧 Конфигурация:
   - PostgreSQL база: crypto_course_db
   - Порты: 8000 (админка), 3000 (webhook бота)
   - Systemd сервисы: crypto-bot, crypto-admin

### �� Структура проекта:
   - bot.py - основной файл бота
   - admin_panel/ - админ-панель
   - handlers/ - обработчики бота
   - utils/ - вспомогательные модули
   - database.py - модели БД
