import re
from typing import Optional, Tuple

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация номера телефона
    Возвращает (is_valid, error_message)
    """
    # Удаляем пробелы, дефисы и скобки
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Проверяем, начинается ли с +
    if not cleaned.startswith('+'):
        return False, "Номер должен начинаться с +"
    
    # Проверяем формат
    if not re.match(r'^\+\d{10,15}$', cleaned):
        return False, "Неверный формат. Пример: +34123456789"
    
    return True, None

def validate_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация имени и фамилии
    """
    name = name.strip()
    
    if len(name) < 3:
        return False, "Слишком короткое имя"
    
    if len(name) > 100:
        return False, "Слишком длинное имя"
    
    # Проверяем, что есть хотя бы два слова
    words = name.split()
    if len(words) < 2:
        return False, "Пожалуйста, введите имя и фамилию"
    
    # Проверяем на недопустимые символы
    if not all(word.replace('-', '').replace("'", '').isalpha() for word in words):
        return False, "Имя может содержать только буквы"
    
    return True, None

def validate_country(country: str) -> Tuple[bool, Optional[str]]:
    """
    Валидация страны
    """
    country = country.strip()
    
    if len(country) < 2:
        return False, "Введите название страны"
    
    if len(country) > 50:
        return False, "Слишком длинное название"
    
    # Список заблокированных стран/регионов (только Украина по ТЗ)
    blocked_keywords = [
        'украина', 'ukraine', 'україна', 'ua', 'укр'
    ]
    
    country_lower = country.lower()
    for keyword in blocked_keywords:
        if keyword in country_lower:
            return False, "К сожалению, курс временно недоступен для жителей Украины"
    
    return True, None

def format_phone(phone: str) -> str:
    """
    Форматирование номера телефона
    """
    # Удаляем все кроме цифр и +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Добавляем + если его нет
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    return cleaned

def is_valid_username(username: Optional[str]) -> bool:
    """
    Проверка валидности username
    """
    if not username:
        return False
    
    # Telegram username должен быть 5-32 символа
    if len(username) < 5 or len(username) > 32:
        return False
    
    # Должен содержать только латиницу, цифры и подчеркивания
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False
    
    return True

def sanitize_html(text: str) -> str:
    """
    Экранирование HTML символов для безопасного вывода
    """
    replacements = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#39;'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def validate_time_slot(time_slot: str) -> bool:
    """
    Проверка корректности временного слота
    """
    valid_slots = [
        "9:00 - 12:00",
        "12:00 - 15:00",
        "15:00 - 18:00",
        "18:00 - 21:00"
    ]
    
    return time_slot in valid_slots

def extract_source_params(start_param: str) -> dict:
    """
    Извлечение параметров из start параметра
    """
    result = {
        'referrer_id': None,
        'source_code': None,
        'click_id': None,
        'additional_params': {}
    }
    
    if not start_param:
        return result
    
    # Реферальная ссылка
    if start_param.startswith('ref'):
        match = re.match(r'ref(\d+)', start_param)
        if match:
            result['referrer_id'] = int(match.group(1))
        return result
    
    # Источник трафика
    if start_param.startswith('src_'):
        parts = start_param[4:].split('-')
        if parts:
            result['source_code'] = parts[0]
            
            # Ищем click_id
            for part in parts[1:]:
                if part.startswith('fbclid_'):
                    result['click_id'] = part[7:]
                    result['additional_params']['fbclid'] = part[7:]
                elif part.startswith('gclid_'):
                    result['click_id'] = part[6:]
                    result['additional_params']['gclid'] = part[6:]
                else:
                    # Другие параметры
                    if '_' in part:
                        key, value = part.split('_', 1)
                        result['additional_params'][key] = value
    
    return result
