"""
Отправка конверсий в RichAds
Полностью независимый модуль
"""
import requests
import logging
import psycopg2
from datetime import datetime
from typing import Optional, Dict
import threading
import json
from .config import RICHADS_CONFIG

logger = logging.getLogger(__name__)

def send_richads_conversion_async(application_id: int):
    """Асинхронная отправка в отдельном потоке"""
    thread = threading.Thread(
        target=_send_richads_conversion,
        args=(application_id,),
        daemon=True
    )
    thread.start()
    logger.info(f"Started RichAds conversion thread for application {application_id}")

def _send_richads_conversion(application_id: int):
    """Внутренняя функция отправки"""
    try:
        from config import DATABASE_URL
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Получаем данные только для RichAds
        cur.execute("""
            SELECT 
                a.id,
                a.user_id,
                uc.click_id,
                uc.raw_params,
                ts.settings
            FROM applications a
            JOIN bot_users bu ON a.user_id = bu.user_id
            JOIN traffic_sources ts ON bu.source_id = ts.id
            LEFT JOIN user_clicks uc ON a.user_id = uc.user_id 
                AND uc.click_type = 'richads_click'
            WHERE a.id = %s 
                AND ts.platform = 'richads'
                AND ts.is_active = true
        """, (application_id,))
        
        result = cur.fetchone()
        
        if not result:
            logger.info(f"No RichAds data for application {application_id}")
            cur.close()
            conn.close()
            return
            
        app_id, user_id, click_id, raw_params, settings = result
        
        if not click_id:
            logger.error(f"No RichAds click_id for user {user_id}")
            cur.close()
            conn.close()
            return
            
        # Парсим настройки источника
        settings = json.loads(settings) if isinstance(settings, str) else settings
        payout = settings.get('payout', '0')
        
        # Парсим campaign из raw_params если есть
        campaign = None
        if raw_params:
            raw = json.loads(raw_params) if isinstance(raw_params, str) else raw_params
            campaign = raw.get('campaign')
            
        # Сохраняем запись о конверсии
        cur.execute("""
            INSERT INTO richads_conversions 
            (application_id, click_id, campaign, payout, postback_url, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            ON CONFLICT (application_id) DO UPDATE
            SET updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            application_id, 
            click_id, 
            campaign,
            payout,
            RICHADS_CONFIG['postback_url']
        ))
        
        conversion_id = cur.fetchone()[0]
        conn.commit()
        
        # Отправляем postback
        params = {
            'action': 'conversion',
            'key': click_id,
            'price': payout
        }
        
        logger.info(f"Sending RichAds postback: {params}")
        
        response = requests.get(
            RICHADS_CONFIG['postback_url'],
            params=params,
            timeout=RICHADS_CONFIG['timeout']
        )
        
        # Обновляем статус
        if response.status_code in RICHADS_CONFIG['success_statuses']:
            cur.execute("""
                UPDATE richads_conversions 
                SET status = 'sent',
                    response_status = %s,
                    response_body = %s,
                    request_sent_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (response.status_code, response.text[:1000], conversion_id))
            
            logger.info(f"✅ RichAds conversion sent for application {application_id}")
        else:
            cur.execute("""
                UPDATE richads_conversions 
                SET status = 'failed',
                    response_status = %s,
                    response_body = %s,
                    error_message = %s,
                    retry_count = retry_count + 1
                WHERE id = %s
            """, (
                response.status_code, 
                response.text[:1000],
                f"HTTP {response.status_code}",
                conversion_id
            ))
            
            logger.error(f"❌ RichAds conversion failed: {response.status_code}")
            
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error sending RichAds conversion: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
