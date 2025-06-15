from sqlalchemy import select
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from datetime import datetime
import logging

from database import db_manager, BotUser, UserAction, TrackingEvent

logger = logging.getLogger(__name__)

class TrackingMiddleware(BaseMiddleware):
    """Middleware для отслеживания активности пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        
        try:
            async with db_manager.get_session() as session:
                # Обновляем последнюю активность пользователя
                user = (await session.execute(select(BotUser).where(BotUser.user_id == user_id))).scalar_one_or_none()
                if user:
                    user.last_activity = datetime.now()
                    
                    # Если есть источник трафика, логируем событие
                    if user.source_id:
                        tracking_event = TrackingEvent(
                            source_id=user.source_id,
                            user_id=user_id,
                            event_type='message'
                        )
                        session.add(tracking_event)
                    
                    await session.commit()
        except Exception as e:
            logger.error(f"Error in tracking middleware: {e}")
        
        # Передаем управление следующему обработчику
        return await handler(event, data)
