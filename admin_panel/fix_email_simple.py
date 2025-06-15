with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Заменяем строку с email на простую версию с user_id
old_email = "'email': f\"{transliterate(name_parts[0])}{str(app_data['user_id'])[-5:]}@gmail.com\""
new_email = "'email': f\"user{str(app_data['user_id'])}@gmail.com\""

content = content.replace(old_email, new_email)

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("Email теперь будет: user{user_id}@gmail.com")
