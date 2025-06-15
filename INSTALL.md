# Инструкция по установке Crypto Course Bot

## Требования
- Ubuntu 22.04 или выше
- Docker и Docker Compose
- Минимум 2GB RAM
- 10GB свободного места на диске

## Быстрая установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/kuboeb/Lastbot.git
cd Lastbot
```

2. Создайте .env файл:
```bash
cp .env.example .env
# Отредактируйте .env и установите свои значения
```

3. Запустите развертывание:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```
