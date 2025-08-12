from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="❓ Вопрос ИИ")
        ],
        [
            KeyboardButton(text="📁 Документы"),
            KeyboardButton(text="⚙️ Настройки")
        ],
        [
            KeyboardButton(text="Ввести ИНН")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

QUESTION_MENU = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✍️ Написать вопрос", callback_data="write_question")],
    [InlineKeyboardButton(text="🗣️ Голосовое сообщение", callback_data="voice_question")],
    [InlineKeyboardButton(text="📎 Прикрепить файл", callback_data="attach_file")]
])

FEEDBACK_MENU = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Ответ удовлетворён", callback_data="feedback_good")],
    [InlineKeyboardButton(text="⚠️ Сообщить об ошибке", callback_data="feedback_error")],
    [InlineKeyboardButton(text="Завершить диалог", callback_data="end_dialog")]
])
