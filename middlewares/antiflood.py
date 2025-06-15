from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timedelta
from aiogram import BaseMiddleware
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

class AntifloodMiddleware(BaseMiddleware):
    """Middleware для защиты от флуда"""
    
    def __init__(self, rate_limit: int = 1, time_window: int = 1):
        """
        rate_limit: количество сообщений
        time_window: временное окно в секундах
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.user_messages: Dict[int, list] = {}
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        current_time = datetime.now()
        
        # Инициализируем список сообщений пользователя
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Удаляем старые сообщения из окна
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if current_time - msg_time < timedelta(seconds=self.time_window)
        ]
        
        # Проверяем лимит
        if len(self.user_messages[user_id]) >= self.rate_limit:
            logger.warning(f"User {user_id} is flooding. Message ignored.")
            await event.answer(
                "⚠️ Слишком много сообщений! Подождите немного перед отправкой следующего."
            )
            return
        
        # Добавляем текущее сообщение
        self.user_messages[user_id].append(current_time)
        
        # Передаем управление следующему обработчику
        return await handler(event, data)
