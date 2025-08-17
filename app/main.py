# app/main.py
"""
Основной модуль запуска Telegram бота
"""
# Добавим базовую конфигурацию логирования для вывода сообщений из connection.py
import logging
logging.basicConfig(level=logging.INFO) # Можно изменить на DEBUG для большего количества деталей

import asyncio
from contextlib import suppress
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from app.config import settings
from app.bot.handlers import router
from app.database.connection import lifespan # <-- Убедиться, что lifespan импортируется

bot = Bot(settings.bot_token)
print(f"Using Redis URL: {settings.redis_url}")  # Временная отладочная строка
storage = RedisStorage.from_url(settings.redis_url)

# Используем lifespan для инициализации/закрытия ресурсов
dp = Dispatcher(storage=storage, lifespan=lifespan) 
dp.include_router(router)

# Точка входа для запуска бота в режиме polling
# Исправить опечатку: name -> __name__
# БЫЛО:
# if name == "main":
# СТАЛО:
if __name__ == "__main__": # <-- Исправлено: __name__
    # Добавим лог при старте, чтобы точно знать, что этот блок выполняется
    logging.getLogger(__name__).info("Starting bot application...")
    with suppress(KeyboardInterrupt):
        # Добавлено allowed_updates для явного указания обрабатываемых типов обновлений
        asyncio.run(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())) # <-- Добавлено allowed_updates
