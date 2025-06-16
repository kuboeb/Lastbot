import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from config import config
from database import db_manager

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт обработчиков
from handlers import start, registration, info

async def test_start_handler(message: Message):
    """Тестовый обработчик для проверки"""
    logger.info(f"TEST: Received /start from user {message.from_user.id}")
    logger.info(f"TEST: Full text: {message.text}")
    logger.info(f"TEST: Has args: {' ' in message.text}")
    if ' ' in message.text:
        args = message.text.split(' ', 1)[1]
        logger.info(f"TEST: Args: {args}")
    await message.answer("Test handler received your message!")

async def main():
    # Инициализация
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Подключаем тестовый обработчик
    dp.message.register(test_start_handler, CommandStart())
    
    # Подключаем остальные роутеры
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(info.router)
    
    # Запуск
    logger.info("Starting test bot...")
    await db_manager.connect()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
