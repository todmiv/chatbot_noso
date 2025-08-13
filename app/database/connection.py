from app.config import settings
import asyncpg
import redis.asyncio as redis
from typing import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Класс для управления подключениями к PostgreSQL и Redis
class Database:
    def __init__(self, db_url: str, redis_url: str):
        self.db_url = db_url
        self.redis_url = redis_url

    async def init(self):
        self.pool = await asyncpg.create_pool(self.db_url)
        self.redis = redis.from_url(
            self.redis_url,
            password="redispass",
            socket_timeout=10,
            socket_connect_timeout=10
        )

    async def close(self):
        await self.pool.close()
        await self.redis.aclose()

db = Database(settings.database_url, settings.redis_url)

# Инициализация SQLAlchemy
engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db(db_url: str = None):
    """Инициализация подключения к БД"""
    if db_url:
        global engine, async_session
        engine = create_async_engine(db_url)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    await db.init()

async def get_db() -> AsyncIterator[AsyncSession]:
    """Получение сессии БД"""
    async with async_session() as session:
        yield session

# Получение пользователя по ID из БД
async def get_user(user_id: int):
    async with db.pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

# Создание или обновление пользователя (UPSERT операция)
async def upsert_user(user_id: int, inn: str, is_member: bool, role: str = 'guest'):
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, inn, is_member, role, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET inn=$2, is_member=$3, role=$4, updated_at=NOW()
        """, user_id, inn, is_member, role)

# Проверка лимита вопросов для гостей (не более 3 в день)
async def check_question_limit(user_id: int, role: str) -> bool:
    if role != 'guest':
        return True
    key = f"questions:{user_id}:{date.today()}"
    count = await db.redis.incr(key)
    if count == 1:
        await db.redis.expire(key, 86400)  # 24 часа
    if count > 3:
        await db.redis.decr(key)
        return False
    return True

@asynccontextmanager
# Контекстный менеджер для управления жизненным циклом подключений
async def lifespan(app):
    await db.init()
    yield
    await db.close()
