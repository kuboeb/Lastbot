import re

with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Найдем и исправим проблемную строку с дублированием
# Заменим всю проблемную часть с lead_data
old_pattern = r'# DEBUG: Проверяем транслитерацию в helper.*?lead_data = \{.*?\}.*?(?=print\(f"Sending lead data:|$)'

new_code = '''# DEBUG: Проверяем транслитерацию в helper
        print(f"DEBUG HELPER: name_parts[0] = '{name_parts[0]}'")
        transliterated_name = transliterate(name_parts[0])
        print(f"DEBUG HELPER: transliterated = '{transliterated_name}'")
        
        lead_data = {
            'first_name': name_parts[0],
            'last_name': name_parts[1] if len(name_parts) > 1 else '',
            'phone': app_data['phone'],
            'country': app_data['country'],
            'preferred_time': app_data['preferred_time'],
            'user_id': str(app_data['user_id']),
            'username': app_data['username'] or '',
            'email': f"{transliterated_name}{str(app_data['user_id'])[-5:]}@gmail.com"
        }
        
        '''

content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

# Если не сработало, попробуем другой подход
if 'gmail.com"{str(app_data' in content:
    # Убираем дублирование
    content = content.replace('gmail.com"{str(app_data[\'user_id\'])[-5:]}@gmail.com"', 'gmail.com"')

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("Fixed send_to_crm_helper.py")
