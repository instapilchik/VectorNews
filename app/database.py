from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import redis.asyncio as redis
from app.config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

# PostgreSQL
engine = create_async_engine(
    settings.database_url,
    # echo=settings.environment == "development",  # SQL логи в dev режиме
    pool_size=10,
    max_overflow=20
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Redis
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

async def get_db_info():
    logger.debug(f"Database URL: {settings.database_url}")
    return settings.database_url

async def get_db():
    """Dependency для получения DB сессии"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

async def get_redis():
    """Dependency для получения Redis клиента"""
    return redis_client

async def init_db():
    """Создание таблиц в БД и инициализация коллекции Qdrant"""
    try:
        from app.models import Base as ModelsBase
        from app.models.news import NewsPost
        from app.models.agent_settings import AgentSettings

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(ModelsBase.metadata.create_all)
        logger.info("Database tables created successfully")

        from app.services.vector_db_service import vector_db_service
        vector_db_service.initialize_collection(vector_size=768)
    except Exception as e:
        logger.error(f"Error initializing database/collections: {e}")
        raise e

async def check_db_connection():
    """Проверяет соединение с базой данных"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
        return True
    except Exception as e:
        # Улучшим логирование, чтобы видеть реальную причину ошибки
        logger.error(f"Database connection failed: {e}")
        return False

async def check_redis_connection():
    """Проверка подключения к Redis"""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False