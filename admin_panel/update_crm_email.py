import re

# Читаем файл send_to_crm_helper.py
with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Ищем где формируется email
print("Текущий код формирования email:")
for line in content.split('\n'):
    if 'email' in line and ('gmail' in line or '@' in line):
        print(f"  {line.strip()}")

# Заменяем формирование email
old_patterns = [
    r'"email":\s*f"user{user_id}@gmail\.com"',
    r"'email':\s*f'user{user_id}@gmail\.com'",
    r'"email":\s*f"user{application\[\'user_id\'\]}@gmail\.com"',
    r"'email':\s*f'user{application\['user_id'\]}@gmail\.com'"
]

replaced = False
for pattern in old_patterns:
    if re.search(pattern, content):
        # Добавляем код для извлечения последних 4 цифр телефона
        new_code = '''# Извлекаем последние 4 цифры телефона для уникальности email
        phone_digits = re.sub(r'[^\\d]', '', application['phone'])[-4:] if application.get('phone') else '0000'
        "email": f"user{application['user_id']}_{phone_digits}@gmail.com"'''
        
        content = re.sub(pattern, new_code, content)
        replaced = True
        print(f"\n✅ Заменен паттерн: {pattern}")
        break

if replaced:
    # Добавляем импорт re если его нет
    if 'import re' not in content:
        content = 'import re\n' + content
    
    with open('send_to_crm_helper.py', 'w') as f:
        f.write(content)
    print("\n✅ Файл обновлен!")
else:
    print("\n❌ Паттерн для замены не найден")

# Показываем где именно формируется email
print("\nПоиск всех мест с email:")
for i, line in enumerate(content.split('\n')):
    if 'email' in line.lower() and any(x in line for x in ['@', 'gmail', 'mail']):
        print(f"  Строка {i+1}: {line.strip()}")
