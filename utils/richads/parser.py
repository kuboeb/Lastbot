"""
Парсер для RichAds параметров
Изолирован от других парсеров
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def parse_richads_params(start_param: str) -> Optional[Dict[str, str]]:
    """
    Парсит параметры из start ссылки RichAds
    
    Форматы:
    - src_rich_001__CLICK_ID
    - src_rich_001__CLICK_ID__CAMPAIGN_ID
    
    Returns:
        Dict с параметрами или None если не RichAds
    """
    try:
        if not start_param or '__' not in start_param:
            return None
            
        parts = start_param.split('__')
        
        # Проверяем, что это RichAds источник
        if not (parts[0].startswith('src_rich') or parts[0] == 'src'):
            return None
            
        # Извлекаем код источника
        source_code = parts[0]
        if source_code.startswith('src_'):
            source_code = source_code[4:]  # Убираем src_ префикс
            
        result = {
            'source_code': source_code,
            'platform': 'richads'
        }
        
        # Обязательный click_id
        if len(parts) >= 2:
            result['click_id'] = parts[1]
        else:
            logger.error("RichAds link without click_id")
            return None
            
        # Опциональная кампания
        if len(parts) >= 3:
            result['campaign'] = parts[2]
            
        logger.info(f"Parsed RichAds params: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing RichAds params: {e}")
        return None

def should_save_richads_click(params: Dict) -> bool:
    """Проверяет, нужно ли сохранять RichAds клик"""
    return (
        params.get('platform') == 'richads' 
        and params.get('click_id')
    )
