# Добавим в начало файла start.py после импортов
import sys
sys.path.append('/home/Lastbot/admin_panel')
from facebook_module.models import save_user_click
import logging

logger = logging.getLogger(__name__)

# Функция для парсинга параметров start
def parse_start_params(args: str):
    """Парсинг параметров команды start"""
    if not args:
        return None, None, None
    
    # Разбираем параметры
    source_code = None
    click_id = None
    click_type = None
    
    # Проверяем реферальную ссылку
    if args.startswith('ref_'):
        return 'referral', args.replace('ref_', ''), None
    
    # Проверяем источник трафика
    if args.startswith('src_'):
        parts = args.split('__')
        source_code = parts[0].replace('src_', '')
        
        # Ищем click_id в остальных частях
        for part in parts[1:]:
            if part.startswith('fbclid_'):
                click_id = part.replace('fbclid_', '')
                click_type = 'fbclid'
                break
            elif part.startswith('gclid_'):
                click_id = part.replace('gclid_', '')
                click_type = 'gclid'
                break
            elif part.startswith('ttclid_'):
                click_id = part.replace('ttclid_', '')
                click_type = 'ttclid'
                break
    
    return source_code, click_id, click_type
