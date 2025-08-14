# test_connectivity.py
import asyncio
import asyncpg
import redis.asyncio as redis

async def test_postgres():
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='Pass1964hfpf',
            database='sro_noso',
            host='host.docker.internal',
            port=5432
        )
        print("PostgreSQL: OK")
        await conn.close()
    except Exception as e:
        print(f"PostgreSQL error: {str(e)}")

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
        print(f"Redis error: {str(e)}")

asyncio.run(test_postgres())
asyncio.run(test_redis())