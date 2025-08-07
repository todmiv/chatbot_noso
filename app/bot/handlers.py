from aiogram import Router, F
from aiogram.types import Message
from app.bot.keyboards import MAIN_MENU
from app.services.ai_service import ask_ai

router = Router()

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    await message.answer("Ваш ИНН пока не указан. Нажмите «Ввести ИНН».", reply_markup=MAIN_MENU)

@router.message(F.text == "❓ Вопрос ИИ")
async def question_handler(message: Message):
    await message.answer("Напишите ваш вопрос или прикрепите PDF.", reply_markup=MAIN_MENU)

@router.message(F.text)
async def ai_answer(message: Message):
    answer = await ask_ai(message.text)
    await message.answer(answer, reply_markup=MAIN_MENU)
