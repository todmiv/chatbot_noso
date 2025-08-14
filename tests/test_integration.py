import pytest
import pytest_asyncio
from app.database.models import User, Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, create_engine

# Конфигурация
@pytest.fixture(scope="module")
def postgres_config():
    return {
        "host": "host.docker.internal",  # ИЗМЕНЕНО
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
        "password": "redispass",
        "username": "default"
    }

# Фикстура для сессии БД
@pytest_asyncio.fixture
async def db_session(postgres_config):
    # Синхронная инициализация схемы
    sync_engine = create_engine(
        f"postgresql://{postgres_config['user']}:{postgres_config['password']}@"
        f"{postgres_config['host']}:{postgres_config['port']}/{postgres_config['database']}"
    )
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()

    # Асинхронное подключение
    db_url = f"postgresql+asyncpg://{postgres_config['user']}:{postgres_config['password']}@{postgres_config['host']}:{postgres_config['port']}/{postgres_config['database']}"
    engine = create_async_engine(db_url)
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    session = async_session()
    yield session
    
    await session.close()
    await engine.dispose()

# Тесты
@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession):
    """Тест соединения с БД"""
    async with db_session.begin():
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_user_model(db_session: AsyncSession):
    """Тест CRUD операций с пользователем"""
    async with db_session.begin():
        # Создаем пользователя
        user = User(inn="123456789012", is_member=True)
        db_session.add(user)
        await db_session.flush()
        
        # Проверяем создание
        saved_user = await db_session.get(User, user.id)
        assert saved_user.inn == "123456789012"
        assert saved_user.is_member == True
        
        # Откатываем изменения после теста
        await db_session.rollback()

@pytest.mark.asyncio
async def test_redis_connection(redis_config):
    import redis.asyncio as redis
    
    r = redis.Redis(
        host=redis_config["host"],
        port=redis_config["port"],
        username=redis_config["username"],
        password=redis_config["password"],
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    
    try:
        assert await r.ping() == True
    finally:
        await r.aclose()