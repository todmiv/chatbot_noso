import asyncio
from aiogram import Bot, Dispatcher
from app.config import settings
from app.bot.handlers import router
from app.database.connection import lifespan

bot = Bot(settings.bot_token)
dp = Dispatcher(lifespan=lifespan)
dp.include_router(router)

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
