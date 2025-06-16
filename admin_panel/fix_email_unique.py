import re
from datetime import datetime

with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Заменяем строку с email на более уникальную версию
old_line = "'email': f\"user{str(app_data['user_id'])}_{app_data['phone'][-4:] if app_data.get('phone') else '0000'}@gmail.com\""
new_line = f"""'email': f"user{{str(app_data['user_id'])}}_{{{app_data['phone'][-4:] if app_data.get('phone') else '0000'}}}_{{int(datetime.now().timestamp()) % 10000}}@gmail.com\""""

# Добавляем импорт datetime
if 'from datetime import datetime' not in content:
    content = 'from datetime import datetime\n' + content

# Ищем и заменяем строку с email
lines = content.split('\n')
for i, line in enumerate(lines):
    if "'email':" in line and "gmail.com" in line:
        # Формируем новую строку с правильным форматированием
        lines[i] = "            'email': f\"user{str(app_data['user_id'])}_{app_data['phone'][-4:] if app_data.get('phone') else '0000'}_{int(datetime.now().timestamp()) % 10000}@gmail.com\""
        print(f"✅ Обновлена строка {i+1}")
        break

content = '\n'.join(lines)

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("✅ Email теперь будет включать: userID_последние4цифры_timestamp")
