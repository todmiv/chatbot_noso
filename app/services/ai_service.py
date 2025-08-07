from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(api_key=settings.deepseek_key, base_url="https://api.deepseek.com")

async def ask_ai(question: str, context: str = "") -> str:
    msgs = [
        {"role": "system", "content": "Ты консультант СРО НОСО. Отвечай кратко и по делу."},
        {"role": "user", "content": f"{context}\n{question}"}
    ]
    r = await client.chat.completions.create(model="deepseek-chat", messages=msgs, max_tokens=1000)
    return r.choices[0].message.content or "Ответ не получен."
