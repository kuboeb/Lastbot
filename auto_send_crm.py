#!/usr/bin/env python3
import sys
import time
sys.path.append('/home/Lastbot/admin_panel')
from send_to_crm_helper import send_application_to_active_crms
import psycopg2
from psycopg2.extras import RealDictCursor

print("🤖 Автоматическая отправка заявок в CRM запущена...")

while True:
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="crypto_course_db",
            user="cryptobot", 
            password="kuboeb1A",
            cursor_factory=RealDictCursor
        )
        cur = conn.cursor()
        
        # Находим неотправленные заявки
        cur.execute("""
            SELECT a.id, a.full_name, bu.username
            FROM applications a
            JOIN bot_users bu ON a.user_id = bu.user_id
            LEFT JOIN integration_logs il ON a.id = il.application_id AND il.status = 'success'
            WHERE il.id IS NULL
            ORDER BY a.created_at
            LIMIT 5
        """)
        
        apps = cur.fetchall()
        
        if apps:
            print(f"\n📤 Найдено {len(apps)} неотправленных заявок")
            for app in apps:
                print(f"  Отправляем: {app['full_name']} (@{app['username'] or 'no_username'})")
                try:
                    send_application_to_active_crms(app['id'])
                    print(f"  ✅ Успешно отправлено")
                except Exception as e:
                    print(f"  ❌ Ошибка: {e}")
                time.sleep(2)  # Пауза между отправками
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка в цикле: {e}")
    
    time.sleep(30)  # Проверяем каждые 30 секунд
