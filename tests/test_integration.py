import pytest
from app.database.connection import get_db, init_db, async_session, engine
from app.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession
import os

@pytest.fixture(scope="module")
def postgres_config():
    return {
        "host": "localhost",
        "port": 5432,
        "user": "postgres",
        "password": "Pass1964hfpf",
        "database": "sro_noso"
    }

@pytest.fixture(scope="module")
def redis_config():
    return {
        "host": "localhost",
        "port": 6380,
        "password": "redispass"
    }

@pytest.fixture
async def db_session(postgres_config):
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    db_url = f"postgresql+asyncpg://{postgres_config['user']}:{postgres_config['password']}@{postgres_config['host']}:{postgres_config['port']}/{postgres_config['database']}"
    engine = create_async_engine(db_url)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        async with session.begin():
            yield session

@pytest.mark.asyncio
async def test_db_connection(db_session):
    """Тест соединения с БД с таймаутом и диагностикой"""
    import time
    start_time = time.time()
    try:
        result = await db_session.execute("SELECT 1")
        assert result.scalar() == 1
        print(f"\nDB connection test passed in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"\nDB connection failed after {time.time() - start_time:.2f}s")
        raise

@pytest.mark.asyncio
async def test_user_model(db_session):
    # Тест CRUD операций с пользователем
    user = User(inn="123456789012", is_member=True)
    db_session.add(user)
    await db_session.commit()
    
    saved_user = await db_session.get(User, user.id)
    assert saved_user.inn == "123456789012"
    assert saved_user.is_member == True

@pytest.mark.asyncio
async def test_redis_connection(redis_config):
    # Проверка соединения с Redis
    import redis
    r = redis.Redis(
        host=redis_config["host"],
        port=redis_config["port"],
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    assert r.ping() == True
