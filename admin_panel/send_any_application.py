#!/usr/bin/env python3
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.append('/home/Lastbot/admin_panel')
from send_to_crm_helper import send_application_to_active_crms

# Подключаемся к БД
conn = psycopg2.connect(
    host="localhost",
    database="crypto_course_db", 
    user="cryptobot",
    password="kuboeb1A",
    cursor_factory=RealDictCursor
)

# Получаем username из аргументов
username = sys.argv[1] if len(sys.argv) > 1 else 'al857bert'

# Находим заявку
cur = conn.cursor()
cur.execute("""
    SELECT a.id, a.full_name, bu.username
    FROM applications a
    JOIN bot_users bu ON a.user_id = bu.user_id  
    WHERE bu.username = %s
    ORDER BY a.created_at DESC
    LIMIT 1
""", (username,))

app = cur.fetchone()

if app:
    print(f"✅ Найдена заявка: ID={app['id']}, Имя={app['full_name']}, Username=@{app['username']}")
    print(f"Отправляем в CRM...")
    
    try:
        result = send_application_to_active_crms(app['id'])
        print(f"Результат: {result}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
else:
    print(f"❌ Заявка для @{username} не найдена")

cur.close()
conn.close()
