import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message
from app.bot.handlers import profile_handler, start_registration, process_inn
from app.database.connection import get_user, upsert_user

@pytest.mark.asyncio
async def test_profile_handler_no_user():
    message = AsyncMock(spec=Message)
    message.from_user.id = 123
    message.answer = AsyncMock()

    with patch('app.bot.handlers.get_user', AsyncMock(return_value=None)):
        await profile_handler(message)
        message.answer.assert_called_with("Ваш ИНН пока не указан. Нажмите «Ввести ИНН».", reply_markup=ANY)

@pytest.mark.asyncio
async def test_profile_handler_member():
    message = AsyncMock(spec=Message)
    message.from_user.id = 123
    message.answer = AsyncMock()
    user = {'inn': '123456789012', 'is_member': True}

    with patch('app.bot.handlers.get_user', AsyncMock(return_value=user)):
        await profile_handler(message)
        message.answer.assert_called_with("ИНН: 123456789012\nСтатус: Член СРО", reply_markup=ANY)

# Другие unit-тесты для handlers
