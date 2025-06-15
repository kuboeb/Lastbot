#!/bin/bash

# Скрипт создания резервной копии

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="crypto_bot_backup_${TIMESTAMP}"

echo "🔄 Создание резервной копии..."

# Создаем директорию для бэкапа
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}

# Бэкап базы данных
echo "📊 Создание дампа базы данных..."
docker-compose exec -T postgres pg_dump -U cryptobot crypto_course_db > ${BACKUP_DIR}/${BACKUP_NAME}/database.sql

# Бэкап файлов .env
echo "🔐 Копирование конфигурации..."
cp .env ${BACKUP_DIR}/${BACKUP_NAME}/

# Бэкап логов
echo "📝 Копирование логов..."
cp -r logs ${BACKUP_DIR}/${BACKUP_NAME}/

# Архивируем
echo "📦 Создание архива..."
cd ${BACKUP_DIR}
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}
rm -rf ${BACKUP_NAME}

echo "✅ Резервная копия создана: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"

# Удаляем старые бэкапы (оставляем последние 7)
echo "🗑️ Очистка старых бэкапов..."
ls -t ${BACKUP_DIR}/*.tar.gz | tail -n +8 | xargs -r rm

echo "✅ Готово!"
