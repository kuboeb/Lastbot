"""
API handler для рассылок
Этот файл подключается к боту через API
"""
import aiohttp
import asyncio
from typing import Dict, List

async def send_broadcast_messages(broadcast_id: int, bot_token: str, db_pool):
    """Отправка сообщений рассылки через Telegram Bot API"""
    
    async with db_pool.acquire() as conn:
        # Получаем данные рассылки
        broadcast = await conn.fetchrow(
            "SELECT * FROM broadcasts WHERE id = $1",
            broadcast_id
        )
        
        if not broadcast:
            return
        
        # Получаем получателей
        recipients = await conn.fetch("""
            SELECT br.*, bu.username
            FROM broadcast_recipients br
            JOIN bot_users bu ON br.user_id = bu.user_id
            WHERE br.broadcast_id = $1 AND br.status = 'pending'
        """, broadcast_id)
        
        # Настройки для отправки
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        async with aiohttp.ClientSession() as session:
            for recipient in recipients:
                try:
                    # Персонализируем сообщение
                    message = broadcast['message']
                    if recipient['username']:
                        message = message.replace('{username}', f"@{recipient['username']}")
                    
                    # Отправляем сообщение
                    async with session.post(api_url, json={
                        'chat_id': recipient['user_id'],
                        'text': message,
                        'parse_mode': 'HTML'
                    }) as resp:
                        if resp.status == 200:
                            # Обновляем статус
                            await conn.execute("""
                                UPDATE broadcast_recipients
                                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                                WHERE broadcast_id = $1 AND user_id = $2
                            """, broadcast_id, recipient['user_id'])
                            
                            # Обновляем счетчик
                            await conn.execute("""
                                UPDATE broadcasts
                                SET sent_count = sent_count + 1
                                WHERE id = $1
                            """, broadcast_id)
                        else:
                            error_data = await resp.text()
                            await conn.execute("""
                                UPDATE broadcast_recipients
                                SET status = 'error', error_message = $3
                                WHERE broadcast_id = $1 AND user_id = $2
                            """, broadcast_id, recipient['user_id'], error_data)
                    
                    # Задержка между сообщениями (30 сообщений в секунду)
                    await asyncio.sleep(0.033)
                    
                except Exception as e:
                    await conn.execute("""
                        UPDATE broadcast_recipients
                        SET status = 'error', error_message = $3
                        WHERE broadcast_id = $1 AND user_id = $2
                    """, broadcast_id, recipient['user_id'], str(e))
        
        # Обновляем статус рассылки
        await conn.execute("""
            UPDATE broadcasts
            SET status = 'sent', completed_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """, broadcast_id)
