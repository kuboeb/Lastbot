#!/usr/bin/env python3
import sys
sys.path.append('/home/Lastbot/admin_panel')

from send_to_crm_helper import send_application_to_active_crms

# ID заявки для отправки
application_id = 42

print(f"Отправляем заявку ID {application_id} в CRM...")
try:
    result = send_application_to_active_crms(application_id)
    print(f"Результат: {result}")
except Exception as e:
    print(f"Ошибка: {e}")
