#!/bin/bash

# Скрипт инициализации базы данных

echo "🗄️ Инициализация базы данных..."

# Ждем запуска PostgreSQL
until docker-compose exec -T postgres pg_isready -U cryptobot; do
  echo "Ожидание запуска PostgreSQL..."
  sleep 2
done

# Создаем базу данных если не существует
docker-compose exec -T postgres psql -U cryptobot -tc "SELECT 1 FROM pg_database WHERE datname = 'crypto_course_db'" | grep -q 1 || \
docker-compose exec -T postgres psql -U cryptobot -c "CREATE DATABASE crypto_course_db"

# Применяем миграции Alembic
echo "📝 Применение миграций..."
docker-compose exec -T bot alembic upgrade head

# Создаем начальные данные
echo "📊 Создание начальных данных..."
docker-compose exec -T postgres psql -U cryptobot -d crypto_course_db < migrations/init.sql

echo "✅ База данных инициализирована!"
