import logging
import requests
import hashlib
import json
import psycopg2
from datetime import datetime
import os

logger = logging.getLogger(__name__)

def send_fb_conversion_simple(application_id: int):
    """Простая отправка конверсии в Facebook"""
    try:
        # Подключаемся к БД
        conn = psycopg2.connect(
            host='localhost',
            database='crypto_course_db',
            user='cryptobot',
            password='kuboeb1A'
        )
        cur = conn.cursor()
        
        # Получаем данные заявки
        cur.execute("""
            SELECT 
                a.user_id,
                a.phone,
                a.country,
                ts.settings,
                uc.click_id
            FROM applications a
            JOIN bot_users bu ON a.user_id = bu.user_id
            LEFT JOIN traffic_sources ts ON bu.source_id = ts.id
            LEFT JOIN user_clicks uc ON a.user_id = uc.user_id AND uc.click_type = 'fbclid'
            WHERE a.id = %s AND ts.platform = 'facebook'
        """, (application_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            return False
            
        user_id, phone, country, settings, fbclid = result
        settings = json.loads(settings) if isinstance(settings, str) else settings
        
        # Подготавливаем данные для Facebook
        event_data = {
            "data": [{
                "event_name": "Lead",
                "event_time": int(datetime.now().timestamp()),
                "event_id": f"lead_{application_id}_{int(datetime.now().timestamp())}",
                "action_source": "app",
                "user_data": {
                    "ph": [hashlib.sha256(phone.lower().strip().encode()).hexdigest()],
                    "country": [hashlib.sha256(country[:2].lower().encode()).hexdigest()]
                }
            }],
            "access_token": settings.get('access_token')
        }
        
        # Добавляем fbclid если есть
        if fbclid:
            event_data["data"][0]["user_data"]["fbc"] = f"fb.1.{int(datetime.now().timestamp())}.{fbclid}"
        
        # Отправляем в Facebook
        url = f"https://graph.facebook.com/v18.0/{settings.get('pixel_id')}/events"
        response = requests.post(url, json=event_data, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ FB conversion sent for application {application_id}")
            return True
        else:
            logger.error(f"❌ FB conversion failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending FB conversion: {e}")
        return False
