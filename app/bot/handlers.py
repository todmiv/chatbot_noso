# app/bot/handlers.py
"""
Основной роутер для обработки команд Telegram-бота
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.bot.keyboards import MAIN_MENU
from app.services.ai_service import ask_ai
from app.services.document_service import doc_service
# Импортируем новую функцию проверки и зависимость
from app.services.sro_registry_service import sro_registry_service # <-- Новый импорт
from app.database.connection import get_user, upsert_user, check_question_limit
import os

logger = logging.getLogger(__name__)

router = Router()

class Registration(StatesGroup):
    inn = State()

# Обработчик команды просмотра профиля пользователя
@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    logger.info(f"Profile handler called for user {message.from_user.id}")
    try:
        user = await get_user(message.from_user.id)
        logger.debug(f"User data retrieved: {user}")
    except Exception as e:
        logger.error(f"Error retrieving user {message.from_user.id} in profile_handler: {e}")
        await message.answer("Ошибка при получении данных профиля. Попробуйте позже.", reply_markup=MAIN_MENU)
        return

    if user is None:
        logger.debug("User record not found in database")
        await message.answer("Ваш профиль не найден. Нажмите «Ввести ИНН» для регистрации.", reply_markup=MAIN_MENU)
    elif user['inn'] is None:
        logger.debug("User INN is NULL in database")
        await message.answer("Ваш ИНН пока не указан. Нажмите «Ввести ИНН».", reply_markup=MAIN_MENU)
    else:
        logger.debug(f"User role: {user['role']}")
        # Используем user['role'] для определения статуса, как в ТЗ и модели
        if user['role'] == 'member':
            status = "Член СРО"
        elif user['role'] == 'guest':
            status = "Гость"
        else:
            status = f"Роль: {user['role']}"

        await message.answer(f"ИНН: {user['inn']}\nСтатус: {status}", reply_markup=MAIN_MENU)


# Начало процесса регистрации по ИНН (10 или 12 цифр)
@router.message(F.text == "Ввести ИНН")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(Registration.inn)
    # Обновлено сообщение с указанием поддерживаемых длин ИНН
    await message.answer("Введите ваш ИНН (10 или 12 цифр):", reply_markup=MAIN_MENU)


@router.message(Registration.inn)
async def process_inn(message: Message, state: FSMContext):
    inn = message.text.strip()
    # Изменить проверку длины ИНН для поддержки 10 и 12 цифр (как в ТЗ)
    if not ((len(inn) == 10 or len(inn) == 12) and inn.isdigit()):
        # Обновить сообщение об ошибке
        await message.answer("ИНН должен состоять из 10 (для организаций) или 12 (для физических лиц) цифр. Попробуйте снова.", reply_markup=MAIN_MENU)
        await state.clear()
        return

    try:
        # Логируем начало проверки ИНН через новый сервис
        logger.info(f"Checking INN {inn} for user {message.from_user.id} via SRO Registry Service")
        
        # Используем новый сервис для проверки
        membership_data = await sro_registry_service.check_membership_by_inn(inn)
        
        if membership_data is None:
            # Организация не найдена или произошла ошибка
            logger.info(f"INN {inn} not found or check failed for user {message.from_user.id}")
            await message.answer("ИНН не найден в реестре СРО НОСО или произошла ошибка при проверке. Попробуйте позже или обратитесь в СРО.", reply_markup=MAIN_MENU)
            await state.clear()
            return
            
        # Получаем статус членства из результата
        is_member = membership_data.get('is_member', False)
        logger.info(f"INN {inn} check result for user {message.from_user.id}: is_member={is_member}")
        
    except Exception as e:
        logger.error(f"Error checking INN {inn} for user {message.from_user.id} via SRO Registry Service: {e}", exc_info=True)
        await message.answer("Ошибка при проверке ИНН. Попробуйте позже.", reply_markup=MAIN_MENU)
        await state.clear()
        return

    # Определяем роль пользователя
    role = 'member' if is_member else 'guest'

    # Пытаемся сохранить/обновить данные пользователя в БД
    try:
        await upsert_user(message.from_user.id, inn, is_member, role)
        logger.info(f"User {message.from_user.id} data upserted successfully with INN {inn}, role {role}.")
    except Exception as db_error:
        logger.error(f"Error upserting user {message.from_user.id} with INN {inn}: {db_error}", exc_info=True)
        await message.answer("Ошибка при сохранении данных пользователя. Попробуйте позже.", reply_markup=MAIN_MENU)
        await state.clear()
        return

    # Отправляем сообщение пользователю в зависимости от статуса
    if is_member:
        await message.answer("Верификация успешна! Вы член СРО.", reply_markup=MAIN_MENU)
    else:
        # Сообщение немного изменено, чтобы отразить, что проверка была через реестр
        await message.answer("ИНН не найден в списке членов СРО НОСО. Вы получили статус 'Гость'.", reply_markup=MAIN_MENU)

    await state.clear()


# Обработчик команды/кнопки вопроса ИИ
@router.message(F.text == "❓ Задайте вопрос")
async def question_handler(message: Message):
    # В MVP этапе просто просим написать вопрос или прикрепить PDF
    await message.answer("Напишите ваш вопрос или прикрепите PDF.", reply_markup=MAIN_MENU)


# Обработчик получения PDF-документа
@router.message(F.document)
async def handle_pdf(message: Message, document: Document):
    if document.mime_type == "application/pdf":
        os.makedirs("documents/uploaded", exist_ok=True)
        file_path = f"documents/uploaded/{document.file_name}"
        # Используем await для асинхронной загрузки файла (исправлено)
        await message.bot.download(document, destination=file_path)
        await message.answer(f"Документ {document.file_name} сохранен в разделе 'Загруженные'", reply_markup=MAIN_MENU)
    else:
        await message.answer("Пожалуйста, отправьте PDF-файл.", reply_markup=MAIN_MENU)


# Обработчик текстовых сообщений (основной сценарий вопроса ИИ)
@router.message(F.text)
async def ai_answer(message: Message):
    # Получаем пользователя для проверки лимита
    user = await get_user(message.from_user.id)
    if not user:
        user_role = 'guest'
        user_id = message.from_user.id
        logger.info(f"Guest user {user_id} asking a question.")
    else:
        user_role = user['role']
        user_id = user['id']
        logger.info(f"User {user_id} (role: {user_role}) asking a question.")

    # Проверяем лимит вопросов для гостей
    is_allowed = await check_question_limit(user_id, user_role)
    if not is_allowed:
        await message.answer("Вы превысили лимит вопросов на сегодня (3 вопроса).", reply_markup=MAIN_MENU)
        return

    # Ищем релевантные документы
    docs = await doc_service.search(message.text)
    # Формируем контекст из найденных документов
    context = "\n".join(f"Документ: {d['name']}\n{d['text']}" for d in docs[:3])

    # Получаем ответ от ИИ
    answer = await ask_ai(message.text, context)

    # Формируем итоговое сообщение с ответом и источниками
    if docs:
        sources = "\n".join(
            f"🔹 {d['name']} (релевантность: {d['score']:.1%})"
            for d in docs[:3]
        )
        answer = f"{answer}\n\n📚 Использованные документы:\n{sources}"

    await message.answer(answer, reply_markup=MAIN_MENU)
