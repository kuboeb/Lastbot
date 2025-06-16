from .models import get_db_connection
import requests
import hashlib
import json
from datetime import datetime
from .models import get_user_click_id, save_conversion_log

# Словарь соответствия стран
COUNTRY_CODES = {
    'россия': 'ru',
    'германия': 'de', 
    'испания': 'es',
    'италия': 'it',
    'франция': 'fr',
    'польша': 'pl',
    'чехия': 'cz',
    'австрия': 'at',
    'швейцария': 'ch',
    'нидерланды': 'nl',
    'бельгия': 'be',
    'португалия': 'pt',
    'греция': 'gr',
    'великобритания': 'gb',
    'швеция': 'se',
    'норвегия': 'no',
    'финляндия': 'fi',
    'дания': 'dk',
    'венгрия': 'hu',
    'румыния': 'ro',
    'болгария': 'bg',
    'хорватия': 'hr',
    'словения': 'si',
    'словакия': 'sk',
    'литва': 'lt',
    'латвия': 'lv',
    'эстония': 'ee',
    'ирландия': 'ie',
    'люксембург': 'lu',
    'мальта': 'mt',
    'кипр': 'cy'
}

def get_country_code(country_name):
    """Преобразование названия страны в 2-буквенный код"""
    return COUNTRY_CODES.get(country_name.lower().strip(), 'xx')

def hash_user_data(data):
    """Хеширование пользовательских данных для Facebook"""
    if not data:
        return None
    
    # Приводим к нижнему регистру и убираем пробелы
    data = str(data).lower().strip()
    
    # Для телефона убираем все кроме цифр и +
    if data.startswith('+'):
        data = '+' + ''.join(c for c in data[1:] if c.isdigit())
    
    # SHA256 хеширование
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def send_facebook_conversion(application_data, source_settings):
    """Отправка конверсии в Facebook Conversion API"""
    
    # Генерируем уникальный event_id
    timestamp = int(datetime.now().timestamp())
    event_id = f"lead_{application_data['id']}_{timestamp}"
    
    # Подготавливаем данные пользователя
    phone_hash = hash_user_data(application_data['phone'])
    country_code = get_country_code(application_data['country'])
    
    # Получаем fbclid если есть
    fbclid = get_user_click_id(application_data['user_id'], 'fbclid')
    
    # Формируем данные для отправки
    user_data = {
        "ph": [phone_hash],
        "country": [country_code]
    }
    
    # Добавляем fbclid если есть
    if fbclid:
        # Facebook ожидает fbc в специальном формате
        user_data["fbc"] = f"fb.1.{timestamp}.{fbclid}"
    
    # Полезная нагрузка
    payload = {
        "data": [{
            "event_name": "Lead",
            "event_time": timestamp,
            "event_id": event_id,
            "action_source": "app",  # Telegram - это app
            "user_data": user_data,
            "custom_data": {
                "currency": "EUR",
                "value": 0
            }
        }],
        "access_token": source_settings['access_token']
    }
    
    # URL для Facebook Conversion API
    url = f"https://graph.facebook.com/v18.0/{source_settings['pixel_id']}/events"
    
    # Сохраняем попытку отправки
    request_data = {
        'pixel_id': source_settings['pixel_id'],
        'event_data': payload['data'][0]
    }
    
    save_conversion_log(
        application_id=application_data['id'],
        event_id=event_id,
        request_data=request_data,
        status='pending'
    )
    
    try:
        # Отправляем запрос
        response = requests.post(url, json=payload, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            # Успешная отправка
            save_conversion_log(
                application_id=application_data['id'],
                event_id=event_id,
                request_data=request_data,
                response_data=response_data,
                status='success'
            )
            
            print(f"✅ Facebook конверсия отправлена: {event_id}")
            return True, response_data
        else:
            # Ошибка от Facebook
            error_msg = response_data.get('error', {}).get('message', 'Unknown error')
            
            save_conversion_log(
                application_id=application_data['id'],
                event_id=event_id,
                request_data=request_data,
                response_data=response_data,
                status='failed',
                error_message=error_msg
            )
            
            print(f"❌ Facebook ошибка: {error_msg}")
            return False, response_data
            
    except requests.exceptions.RequestException as e:
        # Ошибка сети
        error_msg = str(e)
        
        save_conversion_log(
            application_id=application_data['id'],
            event_id=event_id,
            request_data=request_data,
            status='failed',
            error_message=error_msg
        )
        
        print(f"❌ Ошибка отправки: {error_msg}")
        return False, {"error": error_msg}

def retry_failed_conversions():
    """Повторная отправка неудачных конверсий"""
    import psycopg2.extras
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Получаем неудачные конверсии за последние 24 часа
    cur.execute("""
        SELECT 
            fc.*,
            a.user_id,
            a.full_name,
            a.phone,
            a.country,
            ts.settings
        FROM facebook_conversions fc
        JOIN applications a ON fc.application_id = a.id
        JOIN bot_users bu ON a.user_id = bu.user_id
        JOIN traffic_sources ts ON bu.source_id = ts.id
        WHERE fc.status = 'failed'
        AND fc.created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
        AND ts.platform = 'facebook'
        LIMIT 50
    """)
    
    failed_conversions = cur.fetchall()
    cur.close()
    conn.close()
    
    retry_count = 0
    success_count = 0
    
    for conversion in failed_conversions:
        application_data = {
            'id': conversion['application_id'],
            'user_id': conversion['user_id'],
            'full_name': conversion['full_name'],
            'phone': conversion['phone'],
            'country': conversion['country']
        }
        
        source_settings = json.loads(conversion['settings'])
        
        # Повторная отправка
        success, _ = send_facebook_conversion(application_data, source_settings)
        
        retry_count += 1
        if success:
            success_count += 1
    
    return {
        'total_retried': retry_count,
        'successful': success_count,
        'failed': retry_count - success_count
    }
