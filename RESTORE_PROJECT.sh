#!/bin/bash
# Скрипт восстановления проекта LASTBOT

echo "=== Восстановление проекта LASTBOT ==="

# 1. Клонирование репозитория
git clone https://github.com/kuboeb/Lastbot.git
cd Lastbot
git checkout almost-main-v2

# 2. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Восстановление БД
echo "Восстановите БД командой:"
echo "sudo -u postgres psql < database_backup_20250616_143319.sql"

# 5. Настройка systemd сервисов
echo "Настройте systemd сервисы согласно документации"

echo "=== Готово! ==="
