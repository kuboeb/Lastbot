from datetime import datetime

# Примеры данных
app_data = {
    'user_id': '1939130194',
    'phone': '+324243253257'
}

# Старый формат
old_email = f"user{str(app_data['user_id'])}_{app_data['phone'][-4:]}_{datetime.now().strftime('%H%M%S')}@gmail.com"

# Новый формат (без подчеркиваний)
new_email = f"user{str(app_data['user_id'])}{app_data['phone'][-4:]}{datetime.now().strftime('%H%M%S')}@gmail.com"

print(f"Старый формат: {old_email}")
print(f"Новый формат: {new_email}")

# Или с точками
email_with_dots = f"user{str(app_data['user_id'])}.{app_data['phone'][-4:]}.{datetime.now().strftime('%H%M%S')}@gmail.com"
print(f"С точками: {email_with_dots}")
