import sys
import asyncio
import logging
import os
import psycopg2
import json
from datetime import datetime

# Добавляем пути
sys.path.append('/home/Lastbot')
sys.path.append('/home/Lastbot/admin_panel')

logger = logging.getLogger(__name__)

def get_db_connection_sync():
    """Создаем подключение к БД для синхронного кода"""
    from dotenv import load_dotenv
    load_dotenv()
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'crypto_course_db'),
        user=os.getenv('DB_USER', 'cryptobot'),
        password=os.getenv('DB_PASSWORD', 'kuboeb1A')
    )

def send_facebook_conversion_sync(application_id: int, user_id: int):
    """Синхронная версия отправки конверсии"""
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from admin_panel.facebook_module.services import send_facebook_conversion
        
        conn = get_db_connection_sync()
        cur = conn.cursor()
        
        # Получаем данные заявки и источника
        cur.execute("""
            SELECT 
                a.id,
                a.user_id,
                a.full_name,
                a.phone,
                a.country,
                bu.source_id,
                ts.platform,
                ts.settings
            FROM applications a
            JOIN bot_users bu ON a.user_id = bu.user_id
            LEFT JOIN traffic_sources ts ON bu.source_id = ts.id
            WHERE a.id = %s AND ts.platform = 'facebook'
        """, (application_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            logger.info(f"No Facebook source for application {application_id}")
            return
        
        # Подготавливаем данные
        application_data = {
            'id': result[0],
            'user_id': result[1],
            'full_name': result[2],
            'phone': result[3],
            'country': result[4]
        }
        
        settings = json.loads(result[7]) if isinstance(result[7], str) else result[7]
        
        # Отправляем конверсию
        success, response = send_facebook_conversion(application_data, settings)
        
        if success:
            logger.info(f"✅ Facebook conversion sent for application {application_id}")
        else:
            logger.error(f"❌ Failed to send Facebook conversion: {response}")
            
    except Exception as e:
        logger.error(f"Error in send_facebook_conversion_sync: {e}")

# Пустая async версия для совместимости
async def send_conversion_to_facebook(application_id: int, user_id: int):
    """Асинхронная обертка"""
    send_facebook_conversion_sync(application_id, user_id)
