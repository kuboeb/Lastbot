from flask import Flask, request, jsonify
import os
import asyncio
from bot import bot, dp
from config import Config
import asyncpg

app = Flask(__name__)

@app.route('/api/send_broadcast', methods=['POST'])
def send_broadcast():
    """API endpoint для запуска рассылки"""
    data = request.get_json()
    
    # Проверяем API ключ
    if data.get('api_key') != os.getenv('INTERNAL_API_KEY'):
        return jsonify({'error': 'Invalid API key'}), 403
    
    broadcast_id = data.get('broadcast_id')
    if not broadcast_id:
        return jsonify({'error': 'broadcast_id required'}), 400
    
    # Запускаем асинхронную задачу
    asyncio.create_task(process_broadcast(broadcast_id))
    
    return jsonify({'success': True, 'message': 'Broadcast started'})

async def process_broadcast(broadcast_id):
    """Обработка рассылки"""
    conn = await asyncpg.connect(Config.DATABASE_URL)
    
    try:
        # Получаем рассылку
        broadcast = await conn.fetchrow(
            "SELECT * FROM broadcasts WHERE id = $1", broadcast_id
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
        
        # Отправляем сообщения
        for recipient in recipients:
            try:
                # Персонализация
                message = broadcast['message']
                if recipient['username']:
                    message = message.replace('{username}', f"@{recipient['username']}")
                
                # Отправка через бота
                await bot.send_message(recipient['user_id'], message)
                
                # Обновляем статус
                await conn.execute("""
                    UPDATE broadcast_recipients
                    SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                    WHERE broadcast_id = $1 AND user_id = $2
                """, broadcast_id, recipient['user_id'])
                
                await conn.execute("""
                    UPDATE broadcasts SET sent_count = sent_count + 1
                    WHERE id = $1
                """, broadcast_id)
                
                # Задержка между сообщениями
                await asyncio.sleep(0.1)
                
            except Exception as e:
                await conn.execute("""
                    UPDATE broadcast_recipients
                    SET status = 'error', error_message = $3
                    WHERE broadcast_id = $1 AND user_id = $2
                """, broadcast_id, recipient['user_id'], str(e))
        
        # Завершаем рассылку
        await conn.execute("""
            UPDATE broadcasts 
            SET status = 'sent', completed_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """, broadcast_id)
        
    finally:
        await conn.close()

if __name__ == '__main__':
    app.run(port=int(os.getenv('BOT_API_PORT', 8002)))
