with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Находим строку с email и меняем формат
lines = content.split('\n')
for i, line in enumerate(lines):
    if "'email':" in line and "gmail.com" in line:
        # Вариант 1: С точками
        # lines[i] = "            'email': f\"user{str(app_data['user_id'])}.{app_data['phone'][-4:] if app_data.get('phone') else '0000'}.{datetime.now().strftime('%H%M%S')}@gmail.com\""
        
        # Вариант 2: Без разделителей вообще
        lines[i] = "            'email': f\"user{str(app_data['user_id'])}{app_data['phone'][-4:] if app_data.get('phone') else '0000'}{datetime.now().strftime('%H%M%S')}@gmail.com\""
        
        print(f"✅ Обновлена строка {i+1}")
        print(f"Старый формат: user1939130194_3257_092656@gmail.com")
        print(f"Новый формат: user19391301943257092656@gmail.com")
        break

with open('send_to_crm_helper.py', 'w') as f:
    f.write('\n'.join(lines))
