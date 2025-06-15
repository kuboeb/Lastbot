import json
import requests
from datetime import datetime
from flask import jsonify

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
                'email': lead_data.get('email', ''),
                'ip': lead_data.get('ip', '127.0.0.1'),
                'source': settings.get('source', 'telegram_bot'),
                # Дополнительные параметры
                'sub1': lead_data.get('country', ''),
                'sub2': lead_data.get('preferred_time', ''),
                'sub3': f"user_id: {lead_data.get('user_id', '')}",
                'sub4': f"username: {lead_data.get('username', '')}"
            }
            
            # Заголовки
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {settings.get('api_key')}"
            }
            
            # Отправка запроса
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True, 
                    'response': response.json() if response.text else {},
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False, 
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'status_code': response.status_code
                }
                
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_application_to_crm(application_data, integrations):
    """Отправить заявку во все активные CRM"""
    results = []
    
    # Формируем данные для CRM
    full_name = application_data.get('full_name', '')
    name_parts = full_name.split(' ', 1)
    
    lead_data = {
        'first_name': name_parts[0] if name_parts else '',
        'last_name': name_parts[1] if len(name_parts) > 1 else '',
        'phone': application_data.get('phone', ''),
        'country': application_data.get('country', ''),
        'preferred_time': application_data.get('preferred_time', ''),
        'user_id': application_data.get('user_id', ''),
        'username': application_data.get('username', ''),
        'email': ''  # Если нет email, оставляем пустым
    }
    
    # Отправляем в каждую активную интеграцию
    for integration in integrations:
        if integration['is_active']:
            result = send_to_crm(
                integration['type'],
                integration['settings'],
                lead_data,
                application_data.get('id')
            )
            results.append({
                'integration_id': integration['id'],
                'integration_name': integration['name'],
                'result': result
            })
    
    return results
