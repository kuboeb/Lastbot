import re

# Читаем файл bot.py
with open('/home/Lastbot/bot.py', 'r') as f:
    content = f.read()

# Находим место где формируется email
old_pattern = r"email = f'user{user_id}@gmail\.com'"
new_pattern = """# Извлекаем последние 4 цифры телефона для уникальности
    phone_digits = re.sub(r'[^\d]', '', phone)[-4:] if phone else '0000'
    email = f'user{user_id}_{phone_digits}@gmail.com'"""

# Заменяем старый формат на новый
if "email = f'user{user_id}@gmail.com'" in content:
    content = content.replace(
        "email = f'user{user_id}@gmail.com'",
        new_pattern
    )
    
    # Добавляем импорт re если его нет
    if 'import re' not in content.split('\n')[0:20]:
        content = 'import re\n' + content
    
    with open('/home/Lastbot/bot.py', 'w') as f:
        f.write(content)
    
    print("✅ Формат email обновлен: user{id}_{последние4цифры}@gmail.com")
else:
    print("⚠️ Старый формат email не найден, ищем альтернативный...")
    # Показываем где формируется email
    import re
    matches = re.findall(r'.*email.*=.*@gmail\.com.*', content)
    for match in matches:
        print(f"Найдено: {match.strip()}")
