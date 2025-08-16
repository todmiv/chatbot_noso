import asyncio
import asyncpg
import redis.asyncio as redis
import pytest

@pytest.mark.asyncio
async def test_postgres():
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='Pass1964hfpf',
            database='sro_noso',
            host='host.docker.internal',
            port=5432
        )
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {version}")
        await conn.close()
    except Exception as e:
        pytest.fail(f"PostgreSQL error: {str(e)}")

@pytest.mark.asyncio
async def test_redis():
    try:
        r = redis.Redis(
            host='localhost',
            port=6380,
            username='default',
            password='redispass',
            decode_responses=True
        )
        assert await r.ping() == True
        print("Redis: OK")
        await r.aclose()
    except Exception as e:
        pytest.fail(f"Redis error: {str(e)}")