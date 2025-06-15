import json
import re
import requests
from datetime import datetime

# Транслитерация для email
translit_dict = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '',
    'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
}

def transliterate(text):
    """Транслитерация русского текста в латиницу"""
    if not text:
        return ''
    result = ''
    for char in text:
        result += translit_dict.get(char, char)
    # Оставляем только латинские буквы, цифры и разрешенные символы
    result = re.sub(r'[^a-zA-Z0-9._-]', '', result)
    return result.lower() or 'user'


def send_to_crm(integration_type, settings, lead_data, application_id=None):
    """Отправка лида в CRM"""
    print(f"DEBUG: Received lead_data: {lead_data}")
    print(f"DEBUG: Email in lead_data: {lead_data.get('email', 'NOT PROVIDED')}")
    try:
        if integration_type == 'alphacrm':
            # Формируем URL
            domain = settings.get('domain', 'api.alphacrm.cc')
            url = f"https://{domain}/api/v2/leads"
            
            
            # DEBUG: Проверяем транслитерацию
            first_name = lead_data.get('first_name', 'user')
            print(f"DEBUG INTEGRATIONS: Original name: '{first_name}'")
            transliterated = transliterate(first_name)
            print(f"DEBUG INTEGRATIONS: Transliterated: '{transliterated}'")
            existing_email = lead_data.get('email')
            print(f"DEBUG INTEGRATIONS: Existing email: '{existing_email}'")
            
            # Подготавливаем данные для AlphaCRM
            payload = {
                'aff_id': settings.get('aff_id'),
                'first_name': lead_data.get('first_name', ''),
                'last_name': lead_data.get('last_name', ''),
                'phone': lead_data.get('phone', ''),
                'email': lead_data.get('email') or f"user{lead_data.get('user_id', '12345')}@gmail.com",  # Генерируем уникальный email
                'ip': lead_data.get('ip', '127.0.0.1'),
                'source': settings.get('source', 'telegram_bot'),
                'sub1': f"{lead_data.get('country', '')}, {lead_data.get('phone', '')}",
                'sub2': lead_data.get('preferred_time', ''),
                'sub3': f"user_id: {lead_data.get('user_id', '')}",
                'sub4': f"username: {lead_data.get('username', '')}",
            }
            
            # Заголовки
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {settings.get('api_key')}"
            }
            
            # Отправка запроса
            print(f"Sending payload: {payload}")
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True, 
                    'response': response.json() if response.text else {},
                    'status_code': response.status_code,
                    'payload': payload
                }
            else:
                return {
                    'success': False, 
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code,
                    'payload': payload
                }
                
    except Exception as e:
        return {'success': False, 'error': str(e), 'payload': payload if 'payload' in locals() else {}}
