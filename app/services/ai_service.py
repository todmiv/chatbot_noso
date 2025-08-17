# Сервис для работы с ИИ (DeepSeek API)
from openai import AsyncOpenAI
import httpx
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com",
    http_client=httpx.AsyncClient(proxy=None)
)

# Основная функция для вопросов к ИИ с контекстом из документов
async def ask_ai(question: str, context: str = "") -> str:
    if settings.deepseek_api_key == "test_key":
        return "Тестовый ответ на вопрос: " + question
        
    system_prompt = """Ты консультант СРО НОСО. Отвечай на вопросы, используя предоставленные документы.
Если в документах нет ответа, скажи об этом. Будь вежлив и профессионален."""
    
    if context:
        system_prompt += "\n\nКонтекст из документов:\n" + context

    msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    try:
        r = await client.chat.completions.create(model="deepseek-chat", messages=msgs, max_tokens=1000)
        return r.choices[0].message.content or "Ответ не получен."
    except Exception:
        return "Ошибка при получении ответа"
