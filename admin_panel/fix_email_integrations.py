with open('integrations.py', 'r') as f:
    content = f.read()

# Заменяем сложную генерацию на простую
old_pattern = "'email': lead_data.get('email') or f\"{transliterate(lead_data.get('first_name', 'user'))}{lead_data.get('user_id', '12345')[-5:]}@gmail.com\""
new_pattern = "'email': lead_data.get('email') or f\"user{lead_data.get('user_id', '12345')}@gmail.com\""

content = content.replace(old_pattern, new_pattern)

with open('integrations.py', 'w') as f:
    f.write(content)

print("Email в integrations.py тоже изменен")
