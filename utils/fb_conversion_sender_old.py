import logging
import traceback

import requests
import hashlib
import json
import psycopg2
from datetime import datetime
import threading
import os

logger = logging.getLogger(__name__)

def normalize_and_hash(value: str) -> str:
    """Нормализация и хеширование по правилам Facebook"""
    if not value:
        return None
    # Приводим к нижнему регистру, убираем пробелы
    normalized = value.lower().strip()
    # Хешируем SHA256
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

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
    logger.info(f"DEBUG: _send_fb_conversion called from: {traceback.extract_stack()[-2]}")
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
        
        app_id, user_id, phone, settings, source_name, fbclid = result
        
        # Парсим настройки
        settings = json.loads(settings) if isinstance(settings, str) else settings
        pixel_id = settings.get('pixel_id')
        access_token = settings.get('access_token')
        
        if not pixel_id or not access_token:
            logger.error(f"Missing pixel_id or access_token for source {source_name}")
            return
        
        # Генерируем event_id
        event_id = f"lead_{application_id}_{int(datetime.now().timestamp())}"
        
        # Подготавливаем данные пользователя (только телефон!)
        user_data = {
            "ph": [normalize_and_hash(phone)]
        }
        
        # Добавляем fbclid если есть (НЕ хешируется!)
        if fbclid:
            user_data["fbc"] = f"fb.1.{int(datetime.now().timestamp())}.{fbclid}"
            logger.info(f"Including fbclid for better matching: {fbclid[:20]}...")
        
        # Формируем данные для отправки
        event_data = {
            "data": [{
                "event_name": "Lead",
                "event_time": int(datetime.now().timestamp()),
                "event_id": event_id,
                "action_source": "app",
                "user_data": user_data,
                "advertiser_tracking_enabled": 1,  # Обязательно для app
                "data_processing_options": []
            }],
            "access_token": access_token
        }
        
        # Логируем что отправляем
        logger.info(f"Sending to Facebook - phone_hash: {user_data['ph'][0][:10]}..., fbclid: {'yes' if fbclid else 'no'}")
        
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
            response_json = response.json()
            logger.info(f"Facebook response: events_received={response_json.get('events_received', 0)}")
            
            cur.execute("""
                INSERT INTO facebook_conversions 
                (application_id, event_id, pixel_id, status, request_data, response_data)
                VALUES (%s, %s, %s, 'success', %s, %s)
                ON CONFLICT (event_id) DO UPDATE SET
                    status = 'success',
                    response_data = EXCLUDED.response_data
            """, (
                application_id, event_id, pixel_id,
                json.dumps(event_data),
                json.dumps(response_json)
            ))
        else:
            error_detail = response.json() if response.text else {"error": response.text}
            logger.error(f"❌ Facebook conversion failed: {json.dumps(error_detail, indent=2)}")
            
            cur.execute("""
                INSERT INTO facebook_conversions 
                (application_id, event_id, pixel_id, status, request_data, response_data, error_message)
                VALUES (%s, %s, %s, 'failed', %s, %s, %s)
                ON CONFLICT (event_id) DO UPDATE SET
                    status = 'failed',
                    response_data = EXCLUDED.response_data,
                    error_message = EXCLUDED.error_message
            """, (
                application_id, event_id, pixel_id,
                json.dumps(event_data),
                json.dumps(error_detail),
                f"HTTP {response.status_code}: {error_detail.get('error', {}).get('message', 'Unknown error')}"
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error sending Facebook conversion: {e}")
