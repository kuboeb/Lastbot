from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
import logging

logger = logging.getLogger(__name__)
router = Router(name="start_simple")

@router.message(CommandStart())
async def cmd_start_simple(message: Message):
    """Упрощенный обработчик start"""
    user_id = message.from_user.id
    text = message.text
    
    logger.info(f"SIMPLE START: user={user_id}, text={text}")
    
    # Проверяем параметры
    if ' ' in text:
        _, params = text.split(' ', 1)
        logger.info(f"SIMPLE START: params={params}")
        
        # Проверяем fbclid
        if '__fbclid_' in params:
            try:
                fbclid = params.split('__fbclid_')[1]
                logger.info(f"SIMPLE START: found fbclid={fbclid}")
                
                # Сохраняем
                from handlers.facebook_utils import save_user_fbclid
                result = save_user_fbclid(user_id, fbclid, params)
                logger.info(f"SIMPLE START: save result={result}")
                
                await message.answer(f"✅ Сохранен fbclid: {fbclid[:20]}...")
            except Exception as e:
                logger.error(f"SIMPLE START: error={e}")
                await message.answer(f"❌ Ошибка: {e}")
        else:
            await message.answer("ℹ️ Параметры получены, но fbclid не найден")
    else:
        await message.answer("👋 Привет! Это упрощенный обработчик.")
