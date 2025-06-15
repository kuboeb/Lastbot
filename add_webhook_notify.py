import re

with open('handlers/registration.py', 'r') as f:
    content = f.read()

# Если основной метод не сработал, добавим webhook уведомление
if 'webhook' not in content and 'requests.post' not in content:
    # Находим место после await session.commit()
    pattern = r'(await session\.commit\(\))'
    
    if pattern in content:
        replacement = r'''\1
        
        # Уведомляем админку о новой заявке через webhook
        try:
            import aiohttp
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    'http://localhost:8000/api/send-application-to-crm/' + str(application.id),
                    headers={'X-API-Key': 'your-secret-api-key'},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Заявка {application.id} отправлена в CRM через API")
                    else:
                        logger.error(f"Ошибка API: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка отправки в CRM API: {e}")'''
        
        content = re.sub(pattern, replacement, content)
        
        with open('handlers/registration.py', 'w') as f:
            f.write(content)
        
        print("✅ Добавлен webhook для отправки в CRM")
