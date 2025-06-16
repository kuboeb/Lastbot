import sys
import asyncio
import logging
sys.path.append('/home/Lastbot/admin_panel')

from facebook_module.services import send_facebook_conversion
from database import get_db_connection

logger = logging.getLogger(__name__)

async def send_conversion_to_facebook(application_id: int, user_id: int):
    """Отправка конверсии в Facebook если пользователь пришел оттуда"""
    try:
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
        application_data = {
            'id': result[0],
            'user_id': result[1],
            'full_name': result[2],
            'phone': result[3],
            'country': result[4]
        }
        
        settings = result[7]
        
        # Отправляем конверсию
        success, response = send_facebook_conversion(application_data, settings)
        
        if success:
            logger.info(f"✅ Facebook conversion sent for application {application_id}")
        else:
            logger.error(f"❌ Failed to send Facebook conversion: {response}")
            
    except Exception as e:
        logger.error(f"Error in send_conversion_to_facebook: {e}")

# Синхронная обертка для использования в обычном коде
def send_facebook_conversion_sync(application_id: int, user_id: int):
    """Синхронная версия отправки конверсии"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_conversion_to_facebook(application_id, user_id))
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
