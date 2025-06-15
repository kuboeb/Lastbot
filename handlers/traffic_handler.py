"""
Обработчик источников трафика для бота
"""
import re
import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_traffic_params(start_param: str) -> Dict[str, Optional[str]]:
    """
    Парсинг параметров из команды /start
    
    Примеры:
    - src_fb_12345 -> {'source_code': 'fb_12345', 'click_id': None}
    - src_fb_12345-fbclid_IwAR123 -> {'source_code': 'fb_12345', 'click_id': 'IwAR123', 'click_type': 'fbclid'}
    """
    result = {
        'source_code': None,
        'click_id': None,
        'click_type': None
    }
    
    if not start_param or not start_param.startswith('src_'):
        return result
    
    # Убираем префикс src_
    param = start_param[4:]
    
    # Разбираем на код источника и click_id
    parts = param.split('-', 1)
    result['source_code'] = parts[0]
    
    # Если есть вторая часть, парсим click_id
    if len(parts) > 1:
        click_part = parts[1]
        
        # Паттерны для разных типов click_id
        patterns = {
            'fbclid': r'fbclid_(.+?)(?:-|$)',
            'gclid': r'gclid_(.+?)(?:-|$)',
            'ttclid': r'ttclid_(.+?)(?:-|$)',
            'clickid': r'clickid_(.+?)(?:-|$)',
            'subid': r'subid_(.+?)(?:-|$)'
        }
        
        for click_type, pattern in patterns.items():
            match = re.search(pattern, click_part)
            if match:
                result['click_id'] = match.group(1)
                result['click_type'] = click_type
                break
                
        # Если не нашли по паттернам, но есть данные - сохраняем как есть
        if not result['click_id'] and click_part:
            # Пытаемся определить тип по префиксу
            if click_part.startswith('fbclid_'):
                result['click_id'] = click_part[7:]
                result['click_type'] = 'fbclid'
            elif click_part.startswith('gclid_'):
                result['click_id'] = click_part[6:]
                result['click_type'] = 'gclid'
            else:
                # Сохраняем как generic clickid
                result['click_id'] = click_part
                result['click_type'] = 'clickid'
    
    return result

async def save_traffic_source(user_id: int, params: Dict, db_pool) -> Optional[int]:
    """Сохранение источника трафика для пользователя"""
    if not params['source_code']:
        return None
        
    try:
        async with db_pool.acquire() as conn:
            # Ищем источник по коду
            source = await conn.fetchrow(
                "SELECT id FROM traffic_sources WHERE source_code = $1 AND is_active = TRUE",
                params['source_code']
            )
            
            if not source:
                logger.warning(f"Unknown source code: {params['source_code']}")
                return None
                
            source_id = source['id']
            
            # Сохраняем источник для пользователя
            await conn.execute(
                "UPDATE bot_users SET source_id = $1 WHERE user_id = $2",
                source_id, user_id
            )
            
            # Записываем событие клика
            await conn.execute("""
                INSERT INTO tracking_events (source_id, user_id, event_type, click_id)
                VALUES ($1, $2, 'click', $3)
            """, source_id, user_id, params.get('click_id'))
            
            # Если есть click_id, сохраняем отдельно
            if params['click_id'] and params['click_type']:
                await conn.execute("""
                    INSERT INTO user_click_ids (user_id, source_id, click_id, click_type)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, click_type) 
                    DO UPDATE SET click_id = EXCLUDED.click_id, source_id = EXCLUDED.source_id
                """, user_id, source_id, params['click_id'], params['click_type'])
                
            logger.info(f"Saved traffic source {source_id} for user {user_id}")
            return source_id
            
    except Exception as e:
        logger.error(f"Error saving traffic source: {e}")
        return None

async def track_event(user_id: int, event_type: str, db_pool, application_id: Optional[int] = None):
    """Отслеживание событий для источников трафика"""
    try:
        async with db_pool.acquire() as conn:
            # Получаем source_id пользователя
            user = await conn.fetchrow(
                "SELECT source_id FROM bot_users WHERE user_id = $1",
                user_id
            )
            
            if not user or not user['source_id']:
                return
                
            source_id = user['source_id']
            
            # Записываем событие
            await conn.execute("""
                INSERT INTO tracking_events (source_id, user_id, event_type)
                VALUES ($1, $2, $3)
            """, source_id, user_id, event_type)
            
            # Если это лид, создаем запись для конверсии
            if event_type == 'lead' and application_id:
                # Получаем данные источника
                source = await conn.fetchrow(
                    "SELECT platform, settings FROM traffic_sources WHERE id = $1",
                    source_id
                )
                
                if source:
                    # Создаем запись о конверсии
                    await conn.execute("""
                        INSERT INTO conversion_logs 
                        (source_id, user_id, application_id, platform, status)
                        VALUES ($1, $2, $3, $4, 'pending')
                    """, source_id, user_id, application_id, source['platform'])
                    
                    # Обновляем заявку
                    await conn.execute(
                        "UPDATE applications SET source_id = $1 WHERE id = $2",
                        source_id, application_id
                    )
                    
            logger.info(f"Tracked {event_type} event for user {user_id}, source {source_id}")
            
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
