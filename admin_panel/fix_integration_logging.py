import re

with open('integrations.py', 'r') as f:
    content = f.read()

# Найдем место, где сохраняется лог
old_pattern = r"request_data=json\.dumps\(lead_data\)"
new_pattern = "request_data=json.dumps(payload)"

# Заменяем
content = re.sub(old_pattern, new_pattern, content)

# Также убедимся, что payload доступен в месте сохранения лога
# Ищем функцию log_integration_request
if "def log_integration_request" in content:
    # Если есть отдельная функция логирования, нужно передавать payload
    content = re.sub(
        r"log_integration_request\((.*?), lead_data\)",
        r"log_integration_request(\1, payload)",
        content
    )

with open('integrations.py', 'w') as f:
    f.write(content)

print("Fixed integration logging to save actual payload with sub fields")
