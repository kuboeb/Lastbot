with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Заменим строку с email напрямую
old_line = "'email': f\"{transliterated_name}{str(app_data['user_id'])[-5:]}@gmail.com\""
new_line = "'email': f\"{transliterate(name_parts[0])}{str(app_data['user_id'])[-5:]}@gmail.com\""

content = content.replace(old_line, new_line)

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("Fixed email generation directly")
