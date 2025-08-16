# app/database/connection.py
import logging
import asyncio  # Импортируем asyncio для использования asyncio.sleep в init_db
from app.config import settings
import asyncpg
import redis.asyncio as redis
from typing import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import DBAPIError # Убираем неиспользуемый импорт, если он не нужен в init_db

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_url: str, redis_url: str):
        self.db_url = db_url
        self.redis_url = redis_url
        # Инициализируем атрибуты pool и redis как None или без инициализации,
        # они будут созданы в методе init.
        self.pool = None
        self.redis = None

    async def init(self):
        """Инициализирует соединения с PostgreSQL и Redis."""
        logger.info(f"Creating PostgreSQL connection pool with URL: REDACTED_FOR_LOG") # Не логируем полный URL из соображений безопасности
        try:
            # Создаём пул соединений с PostgreSQL
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.info("PostgreSQL connection pool created successfully.")
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection pool: {e}", exc_info=True)
            # Если пул не создан, дальнейшая работа с БД невозможна
            raise

        logger.info(f"Creating Redis client with URL: REDACTED_FOR_LOG") # Не логируем полный URL из соображений безопасности
        try:
            # Создаём клиент Redis.
            # Примечание: redis.from_url обычно не вызывает await и не подключается сразу.
            # Подключение происходит при первом запросе.
            # Пароль и таймауты можно указать в redis_url или явно, как сделано ниже.
            # Убедитесь, что пароль в redis_url совпадает с тем, что указан в docker-compose.yml.
            # Если пароль уже в redis_url, указывать его здесь снова не обязательно, но можно для явности.
            self.redis = redis.from_url(
                self.redis_url,
                # password="redispass", # Убедитесь, что пароль правильный и соответствует docker-compose.yml
                # Если пароль уже в URL, можно не указывать. Если указан и в URL, и здесь, используется значение из from_url.
                socket_timeout=10,
                socket_connect_timeout=10
            )
            logger.info("Redis client created successfully.")
        except Exception as e:
             logger.error(f"Failed to create Redis client: {e}", exc_info=True)
             # Закрываем пул PostgreSQL, если Redis не подключился (хорошая практика)
             if self.pool:
                 await self.pool.close()
                 self.pool = None # Сбрасываем пул
                 logger.info("Closed PostgreSQL pool due to Redis init failure.")
             raise # Перебрасываем исключение

    async def close(self):
        """Закрывает соединения с PostgreSQL и Redis."""
        logger.info("Closing database connections...")
        if self.pool:
            try:
                await self.pool.close()
                logger.info("PostgreSQL connection pool closed.")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL pool: {e}")
        if self.redis:
            try:
                await self.redis.aclose() # Используем aclose() для асинхронного клиента
                logger.info("Redis connection closed.")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        logger.info("Database connections closed.")

# Создание глобального экземпляра Database
db = Database(settings.database_url, settings.redis_url)

# SQLAlchemy engine и sessionmaker для альтернативного доступа (например, через get_db)
engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Функция init_db для альтернативной инициализации или тестов
async def init_db(db_url: str = None):
    """Функция для инициализации БД, в том числе с повторными попытками.
       Используется в тестах или отдельно от lifespan.
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to initialize database connection (attempt {attempt+1})...")
            # Если передан новый URL, обновляем engine и async_session
            if db_url:
                global engine, async_session
                engine = create_async_engine(db_url.replace("postgresql://", "postgresql+asyncpg://"))
                async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                # Также обновляем URL в экземпляре db для последующего использования в db.init()
                db.db_url = db_url

            # Вызываем метод init глобального экземпляра db
            await db.init()
            logger.info(f"Database connection initialized successfully on attempt {attempt+1}.")
            return
        # except DBAPIError as e: # Если не используем DBAPIError, убираем этот блок
        #     logger.error(f"PostgreSQL DBAPI error (attempt {attempt+1}): {str(e)}")
        #     if attempt < max_retries - 1:
        #         await asyncio.sleep(retry_delay)
        #         continue
        #     raise ConnectionError(f"Could not connect to PostgreSQL (DBAPI) after {max_retries} attempts: {str(e)}")
        except Exception as e: # Ловим все остальные ошибки
            logger.error(f"Database connection attempt {attempt+1} failed: {str(e)}", exc_info=True)
            if attempt < max_retries - 1:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                continue
            logger.error(f"Database connection failed after {max_retries} attempts.")
            raise ConnectionError(f"Database connection failed after {max_retries} attempts: {str(e)}")

# Асинхронный генератор для получения SQLAlchemy сессии
async def get_db() -> AsyncIterator[AsyncSession]:
    """Получает асинхронную сессию SQLAlchemy."""
    async with async_session() as session:
        yield session

# Функции для работы с PostgreSQL через asyncpg pool
async def get_user(user_id: int):
    """Получает пользователя из БД по user_id."""
    # Проверяем, инициализирован ли пул
    if db.pool is None:
        logger.error("Database pool is not initialized. Cannot get user.")
        # Можно выбросить исключение или вернуть None
        return None

    async with db.pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)

async def upsert_user(user_id: int, inn: str, is_member: bool, role: str = 'guest'):
    """Создаёт или обновляет пользователя в БД."""
    # Проверяем, инициализирован ли пул
    if db.pool is None:
        logger.error("Database pool is not initialized. Cannot upsert user.")
        raise RuntimeError("Database pool is not initialized.")

    async with db.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, inn, is_member, role, created_at, updated_at)
            VALUES ($1, $2, $3, $4, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET inn=$2, is_member=$3, role=$4, updated_at=NOW()
        """, user_id, inn, is_member, role)

# Функция для работы с Redis (ограничение количества вопросов)
async def check_question_limit(user_id: int, role: str) -> bool:
    """Проверяет, не превышен ли лимит вопросов для пользователя за день."""
    # Проверяем, инициализирован ли клиент Redis
    if db.redis is None:
        logger.error("Redis client is not initialized. Cannot check question limit.")
        # В случае проблем с Redis можно либо разрешить, либо запретить.
        # Здесь выбрано разрешить, чтобы не блокировать работу бота.
        return True

    if role != 'guest':
        return True # Лимит применяется только к гостям

    key = f"questions:{user_id}:{date.today()}"
    # Увеличиваем счётчик и получаем новое значение
    count = await db.redis.incr(key)

    # Если это первое обращение за день, устанавливаем TTL на 24 часа (86400 секунд)
    if count == 1:
        await db.redis.expire(key, 86400)

    # Проверяем лимит (например, 3 вопроса в день для гостей)
    if count > 3:
        # Если лимит превышен, откатываем инкремент
        await db.redis.decr(key)
        return False # Лимит превышен

    return True # Лимит не превышен

# Lifespan менеджер для aiogram
@asynccontextmanager
async def lifespan(app):
    """Асинхронный контекстный менеджер для инициализации и закрытия ресурсов при запуске/остановке приложения."""
    try:
        logger.info("Starting database initialization via lifespan...")
        await db.init() # Используем метод init глобального экземпляра
        logger.info("Database initialization via lifespan completed successfully.")
        yield # Передаём управление приложению
    except Exception as e:
        logger.error(f"Database initialization failed in lifespan: {e}", exc_info=True)
        # Пробрасываем исключение, чтобы остановить запуск приложения
        raise
    finally:
        logger.info("Starting database connection cleanup via lifespan...")
        await db.close() # Закрываем соединения
        logger.info("Database connection cleanup via lifespan completed.")
