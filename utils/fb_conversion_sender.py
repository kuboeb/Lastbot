import logging
import requests
import hashlib
import json
import psycopg2
from datetime import datetime
import threading
import os

logger = logging.getLogger(__name__)

def send_fb_conversion_async(application_id: int):
    """Отправка конверсии в Facebook в отдельном потоке"""
    thread = threading.Thread(
        target=_send_fb_conversion,
        args=(application_id,),
        daemon=True
    )
    thread.start()
    logger.info(f"Started Facebook conversion thread for application {application_id}")

def _send_fb_conversion(application_id: int):
    """Внутренняя функция отправки конверсии"""
    try:
        # Подключаемся к БД
        conn = psycopg2.connect(
            host='localhost',
            database='crypto_course_db',
            user='cryptobot',
            password='kuboeb1A'
        )
        cur = conn.cursor()
        
        # Получаем данные для отправки
        cur.execute("""
            SELECT 
                a.id,
                a.user_id,
                a.phone,
                a.country,
                ts.settings,
                ts.name,
                uc.click_id
            FROM applications a
            JOIN bot_users bu ON a.user_id = bu.user_id
            LEFT JOIN traffic_sources ts ON bu.source_id = ts.id
            LEFT JOIN user_clicks uc ON a.user_id = uc.user_id AND uc.click_type = 'fbclid'
            WHERE a.id = %s 
            AND ts.platform = 'facebook'
            AND ts.is_active = true
        """, (application_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            logger.info(f"No active Facebook source for application {application_id}")
            return
        
        app_id, user_id, phone, country, settings, source_name, fbclid = result
        
        # Парсим настройки
        settings = json.loads(settings) if isinstance(settings, str) else settings
        pixel_id = settings.get('pixel_id')
        access_token = settings.get('access_token')
        
        if not pixel_id or not access_token:
            logger.error(f"Missing pixel_id or access_token for source {source_name}")
            return
        
        # Генерируем event_id
        event_id = f"lead_{application_id}_{int(datetime.now().timestamp())}"
        
        # Хешируем данные
        phone_hash = hashlib.sha256(phone.lower().strip().encode()).hexdigest()
        
        # Определяем код страны
        country_codes = {
            'россия': 'ru', 'германия': 'de', 'испания': 'es',
            'италия': 'it', 'франция': 'fr', 'польша': 'pl',
            'чехия': 'cz', 'австрия': 'at', 'швейцария': 'ch',
            'нидерланды': 'nl', 'бельгия': 'be', 'португалия': 'pt',
            'греция': 'gr', 'великобритания': 'gb', 'швеция': 'se'
        }
        country_code = country_codes.get(country.lower(), 'xx')
        country_hash = hashlib.sha256(country_code.encode()).hexdigest()
        
        # Формируем данные для отправки
        event_data = {
            "data": [{
                "event_name": "Lead",
                "event_time": int(datetime.now().timestamp()),
                "event_id": event_id,
                "action_source": "app",
                "user_data": {
                    "ph": [phone_hash],
                    "country": [country_hash]
                }
            }],
            "access_token": access_token
        }
        
        # Добавляем fbclid если есть
        if fbclid:
            event_data["data"][0]["user_data"]["fbc"] = f"fb.1.{int(datetime.now().timestamp())}.{fbclid}"
            logger.info(f"Including fbclid for better matching: {fbclid[:20]}...")
        
        # Отправляем в Facebook
        url = f"https://graph.facebook.com/v18.0/{pixel_id}/events"
        response = requests.post(url, json=event_data, timeout=10)
        
        # Сохраняем результат в БД
        conn = psycopg2.connect(
            host='localhost',
            database='crypto_course_db',
            user='cryptobot',
            password='kuboeb1A'
        )
        cur = conn.cursor()
        
        if response.status_code == 200:
            logger.info(f"✅ Facebook conversion sent successfully for application {application_id}")
            cur.execute("""
                INSERT INTO facebook_conversions 
                (application_id, event_id, pixel_id, status, request_data, response_data)
                VALUES (%s, %s, %s, 'success', %s, %s)
            """, (
                application_id, event_id, pixel_id,
                json.dumps(event_data),
                json.dumps(response.json())
            ))
        else:
            logger.error(f"❌ Facebook conversion failed: {response.text}")
            cur.execute("""
                INSERT INTO facebook_conversions 
                (application_id, event_id, pixel_id, status, request_data, response_data, error_message)
                VALUES (%s, %s, %s, 'failed', %s, %s, %s)
            """, (
                application_id, event_id, pixel_id,
                json.dumps(event_data),
                json.dumps(response.json()) if response.text else None,
                f"HTTP {response.status_code}: {response.text}"
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error sending Facebook conversion: {e}")
