from datetime import datetime, timedelta
import asyncio
import random
from typing import List, Dict

class BroadcastService:
    def __init__(self, bot_instance, broadcast_model):
        self.bot = bot_instance
        self.model = broadcast_model
        self.scenarios = {
            'warming': [
                {
                    'day': 0,
                    'template': '🚀 {name}, вы записались на бесплатный курс по криптовалюте!\n\n'
                               'Уже завтра начнем погружение в мир цифровых активов.\n\n'
                               '💡 Что вас ждет:\n'
                               '• Пошаговое обучение с нуля\n'
                               '• Личный наставник\n'
                               '• Практические задания\n\n'
                               'Готовы начать? 🔥'
                },
                {
                    'day': 3,
                    'template': '📈 {name}, знаете ли вы?\n\n'
                               'Наш выпускник Александр начал с 500€ и за 3 месяца увеличил капитал до 3000€!\n\n'
                               '🎯 Его секрет прост:\n'
                               '• Следовал стратегии курса\n'
                               '• Не жадничал\n'
                               '• Учился на ошибках\n\n'
                               'Хотите так же? Записывайтесь на курс! 🚀'
                },
                {
                    'day': 5,
                    'template': '⏰ {name}, специальное предложение!\n\n'
                               'Только сегодня при записи на курс:\n'
                               '🎁 Бонусный модуль по DeFi\n'
                               '🎁 Закрытый чат с экспертами\n'
                               '🎁 Чек-лист "Первые 1000€"\n\n'
                               'Осталось 7 мест! Успейте записаться 👇'
                },
                {
                    'day': 7,
                    'template': '🔥 {name}, последний шанс!\n\n'
                               'Группа почти набрана. Осталось всего 3 места!\n\n'
                               'Не упустите возможность:\n'
                               '✅ Научиться зарабатывать на крипте\n'
                               '✅ Получить поддержку экспертов\n'
                               '✅ Изменить свою жизнь\n\n'
                               'Записаться сейчас или ждать следующий набор? 🤔'
                }
            ],
            'retention': [
                {
                    'interval_days': 3,
                    'template': '📚 {name}, новый урок уже доступен!\n\n'
                               'Тема: "Как выбрать первую криптовалюту для инвестиций"\n\n'
                               '🎯 Из урока вы узнаете:\n'
                               '• 5 критериев оценки монет\n'
                               '• Где искать информацию\n'
                               '• Как избежать скама\n\n'
                               'Приятного обучения! 📖'
                }
            ]
        }
    
    async def send_broadcast(self, broadcast_id: int, test_mode: bool = False):
        """Отправить рассылку"""
        # Получаем данные рассылки
        broadcast = self.model.get_broadcast_stats(broadcast_id)
        if not broadcast:
            return {'success': False, 'error': 'Рассылка не найдена'}
        
        # Обновляем статус
        self.model.update_broadcast_status(broadcast_id, 'sending')
        
        # Получаем получателей
        recipients = self._get_recipients(broadcast_id, test_mode)
        
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                # Добавляем случайную задержку 30-90 сек
                delay = random.randint(30, 90) if not test_mode else 1
                await asyncio.sleep(delay)
                
                # Персонализируем сообщение
                message = self._personalize_message(broadcast['message'], recipient)
                
                # Отправляем
                await self.bot.send_message(recipient['user_id'], message)
                
                sent_count += 1
                self._update_recipient_status(broadcast_id, recipient['user_id'], 'sent')
                
            except Exception as e:
                failed_count += 1
                self._update_recipient_status(broadcast_id, recipient['user_id'], 'failed')
        
        # Обновляем статус рассылки
        self.model.update_broadcast_status(broadcast_id, 'sent')
        
        return {
            'success': True,
            'sent': sent_count,
            'failed': failed_count
        }
    
    def _get_recipients(self, broadcast_id: int, test_mode: bool) -> List[Dict]:
        """Получить список получателей"""
        # В тестовом режиме отправляем только админу
        if test_mode:
            return [{'user_id': 7825279349, 'username': 'admin'}]  # ADMIN_ID из .env
        
        # Здесь должен быть запрос к БД для получения получателей
        # Пока заглушка
        return []
    
    def _personalize_message(self, template: str, recipient: Dict) -> str:
        """Персонализировать сообщение"""
        message = template
        message = message.replace('{name}', recipient.get('username', 'Друг'))
        message = message.replace('{days_since_start}', str(recipient.get('days', 0)))
        return message
    
    def _update_recipient_status(self, broadcast_id: int, user_id: int, status: str):
        """Обновить статус получателя"""
        # Здесь должно быть обновление в БД
        pass
    
    def create_scenario(self, name: str, audience_type: str, scenario_type: str) -> int:
        """Создать сценарий рассылки"""
        if scenario_type not in self.scenarios:
            raise ValueError(f"Неизвестный тип сценария: {scenario_type}")
        
        # Создаем первую рассылку сценария
        scenario_messages = self.scenarios[scenario_type]
        
        # Для воронки прогрева создаем все сообщения сразу
        if scenario_type == 'warming':
            broadcast_ids = []
            for step in scenario_messages:
                # Рассчитываем время отправки
                send_time = datetime.now() + timedelta(days=step['day'])
                
                broadcast_id = self.model.create_broadcast(
                    name=f"{name} - День {step['day']}",
                    message=step['template'],
                    audience_type=audience_type,
                    scenario_type=scenario_type
                )
                
                # Планируем отправку
                self._schedule_broadcast(broadcast_id, send_time)
                broadcast_ids.append(broadcast_id)
            
            return broadcast_ids[0]  # Возвращаем ID первой рассылки
        
        return 0
    
    def _schedule_broadcast(self, broadcast_id: int, send_time: datetime):
        """Запланировать отправку рассылки"""
        # Здесь должна быть интеграция с планировщиком (Celery/APScheduler)
        pass
