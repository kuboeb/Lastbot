#!/bin/bash
echo "
🔧 КОМАНДЫ АДМИНИСТРАТОРА:

1. Статус системы:
   sudo systemctl status crypto-bot
   sudo systemctl status crypto-admin

2. Перезапуск:
   sudo systemctl restart crypto-bot
   sudo systemctl restart crypto-admin

3. Логи:
   sudo journalctl -u crypto-bot -f
   sudo journalctl -u crypto-admin -f

4. База данных:
   sudo -u postgres psql crypto_course_db

5. Админка:
   http://145.223.80.72:8000/admin

6. Откат к стабильной версии:
   ./restore_stable.sh
"
