import re

with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Найдем место, где используется payload в логировании
# Проблема в том, что payload определен внутри send_to_crm, а используется снаружи

# Заменим json.dumps(payload) на json.dumps(result.get('payload', lead_data))
content = re.sub(
    r'json\.dumps\(payload\)',
    "json.dumps(result.get('payload', lead_data))",
    content
)

# Если есть другие места где используется payload
content = re.sub(
    r"json\.dumps\(result\.get\('payload', lead_data\)\)",
    "json.dumps(result.get('payload', lead_data))",
    content
)

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("Fixed send_to_crm_helper.py")
