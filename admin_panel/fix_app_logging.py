import re

with open('app.py', 'r') as f:
    content = f.read()

# В app.py нужно изменить логирование, чтобы сохранялся payload, а не test_data
# Но проблема в том, что payload формируется внутри send_to_crm

# Давайте изменим подход - будем возвращать payload из send_to_crm
with open('integrations.py', 'r') as f:
    integrations_content = f.read()

# Модифицируем возвращаемое значение send_to_crm
integrations_content = integrations_content.replace(
    "return {\n                    'success': True, \n                    'response': response.json() if response.text else {},\n                    'status_code': response.status_code\n                }",
    "return {\n                    'success': True, \n                    'response': response.json() if response.text else {},\n                    'status_code': response.status_code,\n                    'payload': payload\n                }"
)

integrations_content = integrations_content.replace(
    "return {\n                    'success': False, \n                    'error': f'HTTP {response.status_code}: {response.text}',\n                    'status_code': response.status_code\n                }",
    "return {\n                    'success': False, \n                    'error': f'HTTP {response.status_code}: {response.text}',\n                    'status_code': response.status_code,\n                    'payload': payload\n                }"
)

# Также для ошибок
integrations_content = integrations_content.replace(
    "return {'success': False, 'error': str(e)}",
    "return {'success': False, 'error': str(e), 'payload': payload if 'payload' in locals() else {}}"
)

with open('integrations.py', 'w') as f:
    f.write(integrations_content)

# Теперь обновим app.py чтобы использовать payload из результата
content = re.sub(
    r'json\.dumps\(test_data\)',
    "json.dumps(result.get('payload', test_data))",
    content
)

content = re.sub(
    r'json\.dumps\(test_lead\)',
    "json.dumps(result.get('payload', test_lead))",
    content
)

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed logging to save actual payload with sub fields")
