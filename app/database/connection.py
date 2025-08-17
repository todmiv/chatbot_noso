# app/database/connection.py
import logging  # <-- Убедиться, что импортирован
import asyncio  # <-- Убедиться, что импортирован
from app.config import settings
import asyncpg
import redis.asyncio as redis
from typing import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__) # <-- Убедиться, что создан

class Database:
    def __init__(self, db_url: str, redis_url: str):
        self.db_url = db_url
        self.redis_url = redis_url
        # Инициализировать атрибуты как None для явности
        self.pool = None
        self.redis = None

    async def init(self):
        """Инициализирует соединения с PostgreSQL и Redis."""
        logger.info("Начало инициализации пула соединений PostgreSQL...")
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            logger.info("Пул соединений PostgreSQL успешно создан.")
        except Exception as e:
            logger.error(f"Ошибка при создании пула PostgreSQL: {e}", exc_info=True)
            raise

        logger.info("Начало инициализации клиента Redis...")
        try:
            # Убираем захардкоженный пароль
            self.redis = redis.from_url(
                self.redis_url,
                socket_timeout=10,
                socket_connect_timeout=10
            )
            logger.info("Клиент Redis успешно создан.")
        except Exception as e:
             logger.error(f"Ошибка при создании клиента Redis: {e}", exc_info=True)
             if self.pool:
                 await self.pool.close()
                 self.pool = None
                 logger.info("Пул PostgreSQL закрыт из-за ошибки инициализации Redis.")
             raise

    async def close(self):
        logger.info("Начало закрытия соединений с БД...")
        # ... (остальной код close как в предыдущем примере) ...
        if self.pool:
            try:
                await self.pool.close()
                logger.info("Пул соединений PostgreSQL закрыт.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии пула PostgreSQL: {e}")
        if self.redis:
            try:
                await self.redis.aclose()
                logger.info("Соединение с Redis закрыто.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии соединения Redis: {e}")
        logger.info("Закрытие соединений с БД завершено.")

# Создание глобального экземпляра Database
db = Database(settings.database_url, settings.redis_url)

# SQLAlchemy engine и sessionmaker для альтернативного доступа (например, через get_db)
# Исправляем замену префикса URL. Лучше использовать URL напрямую, если он уже правильный.
# engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
engine = create_async_engine(settings.database_url) # <-- Используем URL как есть
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Функция init_db для альтернативной инициализации или тестов
async def init_db(db_url: str = None):
    """Функция для инициализации БД, в том числе с повторными попытками.
       Используется в тестах или отдельно от lifespan.
    """
    # Импортируем asyncio внутри функции, если он не импортирован глобально
    # import asyncio # <-- Уже импортирован глобально
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Попытка инициализации БД #{attempt+1}...")
            # Если передан новый URL, обновляем engine и async_session
            if db_url:
                global engine, async_session
                # Исправляем замену префикса URL
                # engine = create_async_engine(db_url.replace("postgresql://", "postgresql+asyncpg://"))
                engine = create_async_engine(db_url) # <-- Используем URL как есть
                async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                # Также обновляем URL в экземпляре db для последующего использования в db.init()
                db.db_url = db_url

            # Вызываем метод init глобального экземпляра db
            await db.init()
            logger.info(f"Инициализация БД успешна на попытке #{attempt+1}.")
            return
        except Exception as e: # Ловим все остальные ошибки
            logger.error(f"Попытка инициализации БД #{attempt+1} не удалась: {str(e)}", exc_info=True)
            if attempt < max_retries - 1:
                logger.info(f"Ожидание {retry_delay} секунд перед повторной попыткой...")
                await asyncio.sleep(retry_delay) # <-- Теперь asyncio доступен
                continue
            logger.error(f"Инициализация БД не удалась после {max_retries} попыток.")
            raise ConnectionError(f"Инициализация БД не удалась после {max_retries} попыток: {str(e)}")

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
    """Асинхронный контекстный менеджер для инициализации и закрытия ресурсов."""
    try:
        logger.info("LIFESPAN HAS BEEN ENTERED") # <-- Убедиться, что есть
        logger.info("Lifespan: Начало инициализации БД через lifespan...")
        await db.init()
        logger.info("Lifespan: Инициализация БД через lifespan успешно завершена.")
        yield
    except Exception as e:
        logger.critical(f"Lifespan: Критическая ошибка инициализации БД: {e}", exc_info=True)
        raise
    finally:
        logger.info("Lifespan: Начало закрытия соединений с БД...")
        await db.close()
        logger.info("Lifespan: Закрытие соединений с БД завершено.")
