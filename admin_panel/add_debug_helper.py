with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Найдем место где формируется email
if "# DEBUG:" not in content:
    old_code = "'email': f\"{transliterate(name_parts[0])}{str(app_data['user_id'])[-5:]}@gmail.com\""
    
    debug_code = """# DEBUG: Проверяем транслитерацию в helper
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
            'email': f"{transliterated_name}{str(app_data['user_id'])[-5:]}@gmail.com\""""
    
    # Заменяем от lead_data = { до email включительно
    import re
    pattern = r"lead_data = \{.*?'email':.*?\}"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(), debug_code)

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("Added debug to send_to_crm_helper.py")
