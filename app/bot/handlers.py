# Основной роутер для обработки команд Telegram-бота
from aiogram import Router, F
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.bot.keyboards import MAIN_MENU
from app.services.ai_service import ask_ai
from app.services.document_service import doc_service
from app.database.connection import get_user, upsert_user
from app.config import settings
import httpx
import os

router = Router()

class Registration(StatesGroup):
    inn = State()

# Обработчик команды просмотра профиля пользователя
@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    user = await get_user(message.from_user.id)
    if user is None or user['inn'] is None:
        await message.answer("Ваш ИНН пока не указан. Нажмите «Ввести ИНН».", reply_markup=MAIN_MENU)
    else:
        status = "Член СРО" if user['is_member'] else "Гость"
        await message.answer(f"ИНН: {user['inn']}\nСтатус: {status}", reply_markup=MAIN_MENU)

# Начало процесса регистрации по ИНН (12 цифр)
@router.message(F.text == "Ввести ИНН")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(Registration.inn)
    await message.answer("Введите ваш ИНН (12 цифр):", reply_markup=MAIN_MENU)

@router.message(Registration.inn)
async def process_inn(message: Message, state: FSMContext):
    inn = message.text.strip()
    if not ((len(inn) == 10 or len(inn) == 12) and inn.isdigit()):
        await message.answer("ИНН должен состоять из 10 (для организаций) или 12 (для физических лиц) цифр. Попробуйте снова.")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.sro_api_url}/check_inn/{inn}")
            response.raise_for_status()
            data = response.json()
            is_member = data.get('is_member', False)
    except Exception as e:
        await message.answer("Ошибка при проверке ИНН. Попробуйте позже.")
        await state.clear()
        return
    
    role = 'member' if is_member else 'guest'
    await upsert_user(message.from_user.id, inn, is_member, role)
    
    if is_member:
        await message.answer("Верификация успешна! Вы член СРО.")
    else:
        await message.answer("ИНН не найден или не подтвержден. Обратитесь в СРО.")
    
    await state.clear()

@router.message(F.text == "❓ Вопрос ИИ")
async def question_handler(message: Message):
    await message.answer("Напишите ваш вопрос или прикрепите PDF.", reply_markup=MAIN_MENU)

@router.message(F.document)
async def handle_pdf(message: Message, document: Document):
    if document.mime_type == "application/pdf":
        os.makedirs("documents/uploaded", exist_ok=True)
        file_path = f"documents/uploaded/{document.file_name}"
        await document.download(destination_file=file_path)
        await message.answer(f"Документ {document.file_name} сохранен в разделе 'Загруженные'", reply_markup=MAIN_MENU)
    else:
        await message.answer("Пожалуйста, отправьте PDF-файл.", reply_markup=MAIN_MENU)

@router.message(F.text)
async def ai_answer(message: Message):
    docs = await doc_service.search(message.text)
    context = "\n".join(f"Документ: {d['name']}\n{d['text']}" for d in docs[:3])
    answer = await ask_ai(message.text, context)
    
    if docs:
        sources = "\n".join(
            f"🔹 {d['name']} (релевантность: {d['score']:.1%})"
            for d in docs[:3]
        )
        answer = f"{answer}\n\n📚 Использованные документы:\n{sources}"
    
    await message.answer(answer, reply_markup=MAIN_MENU)


