
@dp.message_handler(commands=['reload_texts'], user_id=config.ADMIN_ID)
async def reload_texts_command(message: types.Message):
    """Перезагрузить тексты из БД"""
    try:
        from utils.db_texts import text_manager
        text_manager.reload()
        await message.reply("✅ Тексты успешно перезагружены из БД")
    except Exception as e:
        await message.reply(f"❌ Ошибка при перезагрузке текстов: {e}")
