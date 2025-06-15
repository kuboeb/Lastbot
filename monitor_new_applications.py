#!/usr/bin/env python3
import psycopg2
import time
from datetime import datetime

print("Мониторинг новых заявок (Ctrl+C для выхода)...")
print("-" * 60)

conn = psycopg2.connect(
    host='localhost',
    database='crypto_course_db',
    user='cryptobot', 
    password='kuboeb1A'
)

last_id = 0

while True:
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT a.id, a.full_name, a.created_at, bu.username
            FROM applications a
            LEFT JOIN bot_users bu ON a.user_id = bu.user_id
            WHERE a.id > %s
            ORDER BY a.id
        """, (last_id,))
        
        new_apps = cur.fetchall()
        
        for app in new_apps:
            print(f"\n🆕 Новая заявка #{app[0]}")
            print(f"   Имя: {app[1]}")
            print(f"   Username: @{app[3] or 'нет'}")
            print(f"   Время: {app[2]}")
            
            # Проверяем отправку в CRM
            cur.execute("""
                SELECT status, created_at 
                FROM integration_logs 
                WHERE application_id = %s
                ORDER BY id DESC LIMIT 1
            """, (app[0],))
            
            crm_result = cur.fetchone()
            if crm_result:
                status_icon = "✅" if crm_result[0] == 'success' else "❌"
                print(f"   CRM: {status_icon} {crm_result[0]} ({crm_result[1]})")
            else:
                print(f"   CRM: ⏳ ожидает отправки")
            
            last_id = app[0]
        
        cur.close()
        time.sleep(5)
        
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(5)

conn.close()
print("\nМониторинг завершен")
