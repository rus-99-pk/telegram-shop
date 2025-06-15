import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.config import config
from app.database.models import Base
from app.handlers import user, admin

# Настройка логирования для вывода информации о работе бота
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Главная асинхронная функция запуска бота
async def main():
    # Создаем асинхронный движок для работы с базой данных SQLite
    engine = create_async_engine('sqlite+aiosqlite:///db/database.db', echo=True) # echo=True выводит SQL-запросы в консоль
    # Создаем фабрику сессий для асинхронной работы с БД
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # Создаем все таблицы, описанные в models.py, если их еще нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Инициализируем бота с токеном из конфига
    bot = Bot(
        token=config.bot_token.get_secret_value(),
        # Устанавливаем parse_mode по умолчанию, чтобы не указывать его в каждом send_message
        default=DefaultBotProperties(parse_mode='HTML')
    )
    # Инициализируем диспетчер для обработки входящих обновлений
    dp = Dispatcher()

    # Регистрируем Middleware для добавления сессии БД в каждый обработчик
    dp.update.middleware(DbSessionMiddleware(session_pool=session_maker))
    
    # Подключаем роутеры с обработчиками
    dp.include_router(user.router)  # Пользовательские хэндлеры
    dp.include_router(admin.router) # Админские хэндлеры

    # Удаляем вебхук и пропускаем накопившиеся обновления перед запуском
    await bot.delete_webhook(drop_pending_updates=True)
    # Запускаем поллинг (опрос серверов Telegram на наличие новых сообщений)
    await dp.start_polling(bot)

# Middleware для управления сессиями базы данных
class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool

    # Этот метод вызывается для каждого входящего обновления (сообщения, колбэка и т.д.)
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Открываем новую сессию из пула
        async with self.session_pool() as session:
            # "Прокидываем" сессию в данные, доступные внутри хэндлера
            data["session"] = session
            # Вызываем следующий обработчик в цепочке, передавая ему обновленные данные
            return await handler(event, data)


# Точка входа в приложение
if __name__ == '__main__':
    try:
        # Запускаем главную функцию main в цикле событий asyncio
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Обрабатываем graceful-завершение работы бота (Ctrl+C)
        logging.info("Bot stopped")