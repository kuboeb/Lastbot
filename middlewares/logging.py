from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования всех действий"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        start_time = datetime.now()
        
        # Определяем тип события
        if isinstance(event, Message):
            event_type = "message"
            user_id = event.from_user.id
            username = event.from_user.username
            content = event.text or "[non-text message]"
            
            log_data = {
                "type": event_type,
                "user_id": user_id,
                "username": username,
                "content": content[:100],  # Первые 100 символов
                "chat_id": event.chat.id,
                "message_id": event.message_id,
                "timestamp": start_time.isoformat()
            }
            
        elif isinstance(event, CallbackQuery):
            event_type = "callback"
            user_id = event.from_user.id
            username = event.from_user.username
            content = event.data
            
            log_data = {
                "type": event_type,
                "user_id": user_id,
                "username": username,
                "callback_data": content,
                "message_id": event.message.message_id if event.message else None,
                "timestamp": start_time.isoformat()
            }
        
        # Логируем входящее событие
        logger.info(f"Incoming {event_type}: {json.dumps(log_data, ensure_ascii=False)}")
        
        try:
            # Вызываем обработчик
            result = await handler(event, data)
            
            # Логируем успешную обработку
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Successfully processed {event_type} from user {user_id} "
                f"in {processing_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Error processing {event_type} from user {user_id} "
                f"after {processing_time:.2f}s: {str(e)}",
                exc_info=True
            )
            
            # Отправляем сообщение об ошибке пользователю
            if isinstance(event, Message):
                await event.answer(
                    "❌ Произошла ошибка при обработке вашего запроса. "
                    "Пожалуйста, попробуйте позже или обратитесь в поддержку."
                )
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "❌ Произошла ошибка. Попробуйте еще раз.",
                    show_alert=True
                )
            
            raise
