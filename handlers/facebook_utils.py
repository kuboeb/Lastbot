import logging
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def save_user_fbclid(user_id: int, fbclid: str, raw_params: str = None):
    """Простое сохранение fbclid в существующую БД"""
    try:
        # Используем ту же БД что и админка
        conn = psycopg2.connect(
            host='localhost',
            database='crypto_course_db',
            user='cryptobot',
            password='kuboeb1A'
        )
        cur = conn.cursor()
        
        # Сохраняем в таблицу user_clicks которая уже есть
        cur.execute("""
            INSERT INTO user_clicks (user_id, click_id, click_type, raw_params)
            VALUES (%s, %s, 'fbclid', %s)
            ON CONFLICT (user_id, click_type) 
            DO UPDATE SET 
                click_id = EXCLUDED.click_id,
                raw_params = EXCLUDED.raw_params,
                created_at = CURRENT_TIMESTAMP
        """, (user_id, fbclid, raw_params))
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Saved fbclid for user {user_id}: {fbclid[:20]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error saving fbclid: {e}")
        return False
