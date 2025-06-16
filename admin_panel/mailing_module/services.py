import asyncio
import aiohttp
from datetime import datetime
import os
from typing import List, Dict

class MailingService:
    def __init__(self, bot_instance, mailing_model):
        self.bot = bot_instance
        self.model = mailing_model
        self.bot_token = os.getenv('BOT_TOKEN', '7556919860:AAFm1AmvLajbNoXjY5Llf1DFks_7kO7lT-4')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def send_message_to_user(self, user_id: int, text: str) -> bool:
        """Отправить сообщение пользователю через Telegram API"""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    'chat_id': user_id,
                    'text': text,
                    'parse_mode': 'HTML'
                }
                
                async with session.post(f"{self.api_url}/sendMessage", json=data) as resp:
                    result = await resp.json()
                    return result.get('ok', False)
                    
        except Exception as e:
            print(f"Ошибка отправки сообщения {user_id}: {e}")
            return False
    
    async def send_mailing_async(self, mailing_id: int):
        """Асинхронная отправка рассылки"""
        try:
            # Получаем данные рассылки
            mailing = self.model.get_mailing_stats(mailing_id)
            if not mailing:
                return {'success': False, 'error': 'Рассылка не найдена'}
            
            # Проверяем, что есть сообщение
            if not mailing.get('message'):
                return {'success': False, 'error': 'Текст сообщения пустой'}
            
            # Обновляем статус
            self.model.update_mailing_status(mailing_id, 'sending')
            
            # Получаем получателей
            recipients = self.model.get_mailing_recipients(mailing_id)
            
            if not recipients:
                self.model.update_mailing_status(mailing_id, 'sent')
                return {'success': True, 'sent': 0, 'failed': 0, 'total': 0}
            
            sent_count = 0
            failed_count = 0
            
            # Отправляем сообщения пачками по 30 с задержкой
            batch_size = 30
            for i in range(0, len(recipients), batch_size):
                batch = recipients[i:i + batch_size]
                
                # Отправляем пачку
                tasks = []
                for recipient in batch:
                    # Персонализируем сообщение
                    message = str(mailing['message'])
                    username = recipient.get('username', 'Друг')
                    if username and '{name}' in message:
                        message = message.replace('{name}', username)
                    
                    task = self.send_message_to_user(recipient['user_id'], message)
                    tasks.append(task)
                
                # Ждем завершения всех отправок в пачке
                results = await asyncio.gather(*tasks)
                
                # Подсчитываем результаты
                for j, success in enumerate(results):
                    recipient = batch[j]
                    if success:
                        sent_count += 1
                        self.model.update_recipient_status(mailing_id, recipient['user_id'], 'sent')
                    else:
                        failed_count += 1
                        self.model.update_recipient_status(mailing_id, recipient['user_id'], 'failed')
                
                # Задержка между пачками (2 секунды)
                if i + batch_size < len(recipients):
                    await asyncio.sleep(2)
            
            # Обновляем статус рассылки
            self.model.update_mailing_status(mailing_id, 'sent')
            self.model.update_mailing_stats(mailing_id, sent_count, failed_count)
            
            return {
                'success': True,
                'sent': sent_count,
                'failed': failed_count,
                'total': len(recipients)
            }
            
        except Exception as e:
            print(f"Ошибка в send_mailing_async: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def send_mailing(self, mailing_id: int):
        """Синхронная обертка для отправки рассылки"""
        # Создаем новый event loop для выполнения асинхронной функции
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.send_mailing_async(mailing_id))
        finally:
            loop.close()
