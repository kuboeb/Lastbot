with open('send_to_crm_helper.py', 'r') as f:
    content = f.read()

# Найдем проблемное место с дублированием
content = content.replace(
    'gmail.com"{str(app_data[\'user_id\'])[-5:]}@gmail.com"',
    'gmail.com"'
)

# Убедимся что закрывающая скобка есть
if 'lead_data = {' in content and not content[content.find('lead_data = {'):].split('}')[0].count('{') == content[content.find('lead_data = {'):].split('}')[0].count('}'):
    # Найдем место после email и добавим закрывающую скобку
    email_pos = content.find('gmail.com"')
    if email_pos != -1:
        next_newline = content.find('\n', email_pos)
        content = content[:next_newline] + '\n        }' + content[next_newline:]

with open('send_to_crm_helper.py', 'w') as f:
    f.write(content)

print("Fixed syntax in send_to_crm_helper.py")
