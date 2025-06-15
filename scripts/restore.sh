#!/bin/bash

# Скрипт восстановления из резервной копии

if [ $# -eq 0 ]; then
    echo "Использование: ./restore.sh <путь_к_архиву>"
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR="/tmp/restore_$$"

echo "🔄 Восстановление из резервной копии: ${BACKUP_FILE}"

# Проверяем существование файла
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Файл не найден: ${BACKUP_FILE}"
    exit 1
fi

# Останавливаем сервисы
echo "🛑 Останавливаем сервисы..."
docker-compose down

# Распаковываем архив
echo "📦 Распаковка архива..."
mkdir -p ${RESTORE_DIR}
tar -xzf ${BACKUP_FILE} -C ${RESTORE_DIR}

# Находим директорию с бэкапом
BACKUP_DIR=$(ls ${RESTORE_DIR})

# Восстанавливаем .env
echo "🔐 Восстановление конфигурации..."
cp ${RESTORE_DIR}/${BACKUP_DIR}/.env .

# Запускаем только БД
echo "🗄️ Запуск базы данных..."
docker-compose up -d postgres
sleep 10

# Восстанавливаем БД
echo "📊 Восстановление базы данных..."
docker-compose exec -T postgres psql -U cryptobot -c "DROP DATABASE IF EXISTS crypto_course_db;"
docker-compose exec -T postgres psql -U cryptobot -c "CREATE DATABASE crypto_course_db;"
docker-compose exec -T postgres psql -U cryptobot crypto_course_db < ${RESTORE_DIR}/${BACKUP_DIR}/database.sql

# Восстанавливаем логи
echo "📝 Восстановление логов..."
cp -r ${RESTORE_DIR}/${BACKUP_DIR}/logs .

# Запускаем все сервисы
echo "🚀 Запуск всех сервисов..."
docker-compose up -d

# Очистка
rm -rf ${RESTORE_DIR}

echo "✅ Восстановление завершено!"
