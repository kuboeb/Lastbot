# Инструкция по использованию Crypto Course Bot

## Установка завершена успешно! ✅

### Доступы к системе

#### Telegram бот
- Токен: 7556919860:AAFm1AmvLajbNoXjY5Llf1DFks_7kO7lT-4
- Найдите бота в Telegram и напишите /start

#### Админ панель
- URL: http://145.223.80.72:8000
- Логин: admin
- Пароль: kuboeb1A

#### Операторская панель
- URL: http://145.223.80.72:8001
- Логин: admin
- Пароль: oper1A

## Управление сервисами

### Проверка статуса
```bash
sudo systemctl status crypto-bot
sudo systemctl status crypto-admin
sudo systemctl status crypto-operator
```

### Перезапуск сервисов
```bash
sudo systemctl restart crypto-bot
sudo systemctl restart crypto-admin
sudo systemctl restart crypto-operator
```

### Просмотр логов
```bash
sudo journalctl -u crypto-bot -f
sudo journalctl -u crypto-admin -f
sudo journalctl -u crypto-operator -f
```

## База данных
- Host: localhost
- Port: 5432
- Database: crypto_course_db
- User: cryptobot
- Password: kuboeb1A
