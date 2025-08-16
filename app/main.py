# Основной модуль запуска Telegram бота
import asyncio
from contextlib import suppress
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from app.config import settings
from app.bot.handlers import router
from app.database.connection import lifespan

bot = Bot(settings.bot_token)
print(f"Using Redis URL: {settings.redis_url}")  # Временная отладочная строка
storage = RedisStorage.from_url(settings.redis_url)
dp = Dispatcher(storage=storage, lifespan=lifespan)
dp.include_router(router)

# Точка входа для запуска бота в режиме polling
if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(dp.start_polling(bot))
