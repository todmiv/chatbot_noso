"""
Telegram-бот: хендлеры и UI-клавиатуры.
"""
from .handlers import router as bot_router
from .keyboards import MAIN_MENU

__all__ = ["bot_router", "MAIN_MENU"]
