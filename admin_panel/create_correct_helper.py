# Читаем оригинальную версию функции
with open('send_to_crm_helper.py', 'r') as f:
    lines = f.readlines()

# Находим строку с email и заменяем только её
for i, line in enumerate(lines):
    if "'email':" in line and "lower().replace" in line:
        # Заменяем на версию с транслитерацией
        lines[i] = "            'email': f\"{transliterate(name_parts[0])}{str(app_data['user_id'])[-5:]}@gmail.com\"\n"
        print(f"Заменена строка {i+1}: {line.strip()} -> {lines[i].strip()}")

# Сохраняем
with open('send_to_crm_helper.py', 'w') as f:
    f.writelines(lines)

print("Исправлено!")
