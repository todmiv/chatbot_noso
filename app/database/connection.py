import asyncpg
import redis.asyncio as redis
from typing import AsyncGenerator
from contextlib import asynccontextmanager

class Database:
    def __init__(self, db_url: str, redis_url: str):
        self.db_url = db_url
        self.redis_url = redis_url

    async def init(self):
        self.pool = await asyncpg.create_pool(self.db_url)
        self.redis = redis.from_url(self.redis_url)

    async def close(self):
        await self.pool.close()
        await self.redis.aclose()

db = Database(settings.db_url, settings.redis_url)

@asynccontextmanager
async def lifespan(app):
    await db.init()
    yield
    await db.close()
