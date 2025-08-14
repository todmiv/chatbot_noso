from app.config import settings
import asyncpg
import redis.asyncio as redis
from typing import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

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

engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db(db_url: str = None):
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            if db_url:
                global engine, async_session
                engine = create_async_engine(db_url)
                async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            
            await db.init()
            return
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            raise ConnectionError(f"Database connection failed after {max_retries} attempts: {str(e)}")

async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session

async def get_user(user_id: int):
    async with db.pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

async def upsert_user(user_id: int, inn: str, is_member: bool, role: str = 'guest'):
    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, inn, is_member, role, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET inn=$2, is_member=$3, role=$4, updated_at=NOW()
        """, user_id, inn, is_member, role)

async def check_question_limit(user_id: int, role: str) -> bool:
    if role != 'guest':
        return True
    key = f"questions:{user_id}:{date.today()}"
    count = await db.redis.incr(key)
    if count == 1:
        await db.redis.expire(key, 86400)
    if count > 3:
        await db.redis.decr(key)
        return False
    return True

@asynccontextmanager
async def lifespan(app):
    try:
        await db.init()
        yield
    finally:
        await db.close()