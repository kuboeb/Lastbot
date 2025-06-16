import sys
import asyncio
import logging
import os

# Добавляем пути
sys.path.append('/home/Lastbot')
sys.path.append('/home/Lastbot/admin_panel')

logger = logging.getLogger(__name__)

def send_facebook_conversion_sync(application_id: int, user_id: int):
    """Синхронная версия отправки конверсии"""
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from admin_panel.facebook_module.services import send_facebook_conversion
        from database import get_db_connection
        
        conn = get_db_connection()
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
        import json
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
