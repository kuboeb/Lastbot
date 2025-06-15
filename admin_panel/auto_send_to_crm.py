#!/usr/bin/env python3
"""
Автоматическая отправка новых заявок в CRM
Запускать через cron каждую минуту
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os
sys.path.append('/home/Lastbot/admin_panel')
from send_to_crm_helper import send_application_to_active_crms

def get_unsent_applications():
    """Получить заявки, которые еще не отправлены в CRM"""
    conn = psycopg2.connect(
        host='localhost',
        database='crypto_course_db',
        user='cryptobot',
        password='kuboeb1A',
        cursor_factory=RealDictCursor
    )
    cur = conn.cursor()
    
    # Находим заявки без записей в integration_logs
    cur.execute("""
        SELECT DISTINCT a.id
        FROM applications a
        LEFT JOIN integration_logs il ON a.id = il.application_id
        WHERE il.id IS NULL
           OR NOT EXISTS (
               SELECT 1 FROM integration_logs il2 
               WHERE il2.application_id = a.id 
               AND il2.status = 'success'
           )
        ORDER BY a.id DESC
        LIMIT 10
    """)
    
    unsent_ids = [row['id'] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return unsent_ids

def main():
    print("Проверка неотправленных заявок...")
    
    unsent_ids = get_unsent_applications()
    
    if unsent_ids:
        print(f"Найдено {len(unsent_ids)} неотправленных заявок: {unsent_ids}")
        
        for app_id in unsent_ids:
            print(f"Отправка заявки {app_id}...")
            try:
                send_application_to_active_crms(app_id)
                print(f"Заявка {app_id} отправлена успешно")
            except Exception as e:
                print(f"Ошибка отправки заявки {app_id}: {e}")
    else:
        print("Все заявки отправлены")

if __name__ == "__main__":
    main()
