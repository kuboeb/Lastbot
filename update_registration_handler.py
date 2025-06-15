import re

# Читаем файл
with open('handlers/registration.py', 'r') as f:
    content = f.read()

# Проверяем, не добавлен ли уже импорт
if 'from admin_panel.send_to_crm_helper import send_application_to_active_crms' not in content:
    # Добавляем импорт в начало файла после других импортов
    import_pattern = r'(import .*\n|from .* import .*\n)+'
    match = re.search(import_pattern, content)
    if match:
        last_import_pos = match.end()
        content = content[:last_import_pos] + 'from admin_panel.send_to_crm_helper import send_application_to_active_crms\n' + content[last_import_pos:]

# Находим место после INSERT INTO applications и добавляем отправку в CRM
pattern = r'(cur\.execute\s*\(\s*["\']INSERT INTO applications.*?\).*?conn\.commit\(\))'

def add_crm_send(match):
    original = match.group(0)
    # Добавляем получение ID новой заявки и отправку в CRM
    addition = """
        
        # Получаем ID созданной заявки
        cur.execute("SELECT lastval()")
        application_id = cur.fetchone()[0]
        
        # Отправляем в CRM
        try:
            send_application_to_active_crms(application_id)
            await bot.send_message(
                message.from_user.id,
                "✅ Ваши данные отправлены менеджеру!",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Ошибка отправки в CRM: {e}")
            # Не показываем ошибку пользователю, просто логируем"""
    
    return original + addition

# Применяем изменения
content = re.sub(pattern, add_crm_send, content, flags=re.DOTALL)

# Альтернативный поиск если первый не сработал
if 'send_application_to_active_crms' not in content:
    # Ищем RETURNING id
    pattern2 = r'(INSERT INTO applications.*?RETURNING id.*?application_id = cur\.fetchone\(\)\[0\])'
    
    def add_crm_send2(match):
        original = match.group(0)
        addition = """
        
        # Отправляем в CRM
        try:
            logger.info(f"Отправка заявки {application_id} в CRM")
            send_application_to_active_crms(application_id)
            logger.info(f"Заявка {application_id} успешно отправлена в CRM")
        except Exception as e:
            logger.error(f"Ошибка отправки заявки {application_id} в CRM: {e}")"""
        
        return original + addition
    
    content = re.sub(pattern2, add_crm_send2, content, flags=re.DOTALL)

# Сохраняем изменения
with open('handlers/registration.py', 'w') as f:
    f.write(content)

print("Обновлен handlers/registration.py")

# Проверяем результат
if 'send_application_to_active_crms' in content:
    print("✅ Автоматическая отправка в CRM добавлена!")
else:
    print("❌ Не удалось добавить автоматическую отправку, проверьте файл вручную")
