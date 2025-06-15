"""
Админские команды для бота
"""
from aiogram import types
from aiogram.dispatcher import Dispatcher
from config import ADMIN_ID
from utils.db_texts import text_manager
import logging

logger = logging.getLogger(__name__)

async def reload_texts_command(message: types.Message):
    """Перезагрузить тексты из БД"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        text_manager.reload()
        await message.reply("✅ Тексты успешно перезагружены из БД")
        logger.info(f"Admin {message.from_user.id} reloaded texts")
    except Exception as e:
        await message.reply(f"❌ Ошибка при перезагрузке текстов: {e}")
        logger.error(f"Error reloading texts: {e}")

def register_admin_handlers(dp: Dispatcher):
    """Регистрация админских обработчиков"""
    dp.register_message_handler(reload_texts_command, commands=['reload_texts'], user_id=ADMIN_ID)
