"""
Планировщик для автоматической отправки рассылок
"""
import schedule
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def check_scheduled_broadcasts():
    """Проверка и отправка запланированных рассылок"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Получаем рассылки, которые пора отправить
        cur.execute("""
            SELECT * FROM broadcasts 
            WHERE status = 'scheduled' 
            AND next_run_at <= CURRENT_TIMESTAMP
            AND is_active = TRUE
        """)
        
        broadcasts = cur.fetchall()
        
        for broadcast in broadcasts:
            print(f"Отправка рассылки: {broadcast['name']}")
            
            # Если это сценарий, проверяем какой шаг
            if broadcast['scenario_type']:
                send_scenario_step(broadcast, conn)
            else:
                # Обычная рассылка
                send_regular_broadcast(broadcast['id'])
            
            # Обновляем next_run_at если нужно повторить
            if broadcast['schedule_type'] == 'daily':
                next_run = datetime.now() + timedelta(days=1)
                cur.execute("""
                    UPDATE broadcasts 
                    SET next_run_at = %s
                    WHERE id = %s
                """, (next_run, broadcast['id']))
            else:
                # Одноразовая рассылка - меняем статус
                cur.execute("""
                    UPDATE broadcasts 
                    SET status = 'pending'
                    WHERE id = %s
                """, (broadcast['id'],))
            
            conn.commit()
            
    except Exception as e:
        print(f"Ошибка в планировщике: {e}")
    finally:
        cur.close()
        conn.close()

def send_scenario_step(broadcast, conn):
    """Отправка шага сценария"""
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Получаем сценарий
    cur.execute("""
        SELECT steps FROM warming_scenarios 
        WHERE name = %s
    """, (broadcast['scenario_type'],))
    
    scenario = cur.fetchone()
    if not scenario:
        return
    
    steps = scenario['steps']
    current_step = broadcast.get('scenario_step', 1)
    
    if current_step <= len(steps):
        # Отправляем текущий шаг
        step_data = steps[current_step - 1]
        
        # Обновляем сообщение в рассылке
        cur.execute("""
            UPDATE broadcasts 
            SET message = %s, scenario_step = %s
            WHERE id = %s
        """, (step_data['message'], current_step + 1, broadcast['id']))
        
        # Запускаем отправку
        send_regular_broadcast(broadcast['id'])
        
        # Планируем следующий шаг
        if current_step < len(steps):
            next_step = steps[current_step]
            days_diff = next_step['day'] - step_data['day']
            next_run = datetime.now() + timedelta(days=days_diff)
            
            cur.execute("""
                UPDATE broadcasts 
                SET next_run_at = %s
                WHERE id = %s
            """, (next_run, broadcast['id']))
    else:
        # Сценарий завершен
        cur.execute("""
            UPDATE broadcasts 
            SET status = 'completed', is_active = FALSE
            WHERE id = %s
        """, (broadcast['id'],))
    
    conn.commit()

def send_regular_broadcast(broadcast_id):
    """Запуск обычной рассылки через API админки"""
    try:
        # Вызываем endpoint админки
        response = requests.post(
            f"http://localhost:8000/broadcast/{broadcast_id}/send",
            headers={'X-Internal-Request': 'true'}
        )
        print(f"Результат отправки: {response.status_code}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

if __name__ == "__main__":
    print("Планировщик рассылок запущен...")
    
    # Проверяем каждые 5 минут
    schedule.every(5).minutes.do(check_scheduled_broadcasts)
    
    # Первая проверка сразу
    check_scheduled_broadcasts()
    
    while True:
        schedule.run_pending()
        time.sleep(60)
