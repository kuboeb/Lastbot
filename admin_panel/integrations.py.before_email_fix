import json
import requests
from datetime import datetime

def send_to_crm(integration_type, settings, lead_data, application_id=None):
    """Отправка лида в CRM"""
    try:
        if integration_type == 'alphacrm':
            # Формируем URL
            domain = settings.get('domain', 'api.alphacrm.cc')
            url = f"https://{domain}/api/v2/leads"
            
            # Подготавливаем данные для AlphaCRM
            payload = {
                'aff_id': settings.get('aff_id'),
                'first_name': lead_data.get('first_name', ''),
                'last_name': lead_data.get('last_name', ''),
                'phone': lead_data.get('phone', ''),
                'email': lead_data.get('email') or f"{lead_data.get('first_name', 'user').lower().replace(' ', '')}{lead_data.get('user_id', '12345')[-5:]}@gmail.com",  # Генерируем уникальный email
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
