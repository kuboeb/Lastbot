with open('integrations.py', 'r') as f:
    content = f.read()

# Найдем место где формируется email и добавим отладку
old_line = "'email': lead_data.get('email') or f\"{transliterate(lead_data.get('first_name', 'user'))}{lead_data.get('user_id', '12345')[-5:]}@gmail.com\","

new_lines = """'email': lead_data.get('email') or f"{transliterate(lead_data.get('first_name', 'user'))}{lead_data.get('user_id', '12345')[-5:]}@gmail.com",  # Генерируем уникальный email"""

# Добавим print перед формированием payload
debug_code = """
            # DEBUG: Проверяем транслитерацию
            first_name = lead_data.get('first_name', 'user')
            print(f"DEBUG INTEGRATIONS: Original name: '{first_name}'")
            transliterated = transliterate(first_name)
            print(f"DEBUG INTEGRATIONS: Transliterated: '{transliterated}'")
            existing_email = lead_data.get('email')
            print(f"DEBUG INTEGRATIONS: Existing email: '{existing_email}'")
            
            # Подготавливаем данные для AlphaCRM
            payload = {"""

content = content.replace("# Подготавливаем данные для AlphaCRM\n            payload = {", debug_code)

with open('integrations.py', 'w') as f:
    f.write(content)

print("Added debug to integrations.py")
