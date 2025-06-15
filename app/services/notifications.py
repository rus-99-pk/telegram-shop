import logging
from aiogram import Bot
from app.config import config

logger = logging.getLogger(__name__)

async def notify_developer_of_error(bot: Bot, error_text: str):
    """Отправляет сообщение об ошибке разработчику."""
    try:
        await bot.send_message(
            chat_id=config.developer_id,
            text=f"‼️ <b>Критическая ошибка в боте!</b> ‼️\n\n<pre>{error_text}</pre>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление разработчику: {e}")