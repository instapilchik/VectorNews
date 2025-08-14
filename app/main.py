from pathlib import Path
from dotenv import load_dotenv
# Загрузка переменных окружения из .env
dotenv_path = Path(__file__).resolve().parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"Загружены переменные окружения из {dotenv_path}")
else:
    print(f"Внимание: файл .env не найден в {dotenv_path}")

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.database import init_db, check_db_connection, check_redis_connection
from app.api.deps import get_user_from_header


# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events для FastAPI"""
    # Startup
    logger.info("Starting AI News Manager microservice...")

    # Проверяем подключения
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()

    if not db_ok:
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")

    if not redis_ok:
        logger.error("Failed to connect to Redis")
        raise Exception("Redis connection failed")

    # Создаем таблицы
    await init_db()

    logger.info("All systems ready!")

    yield

    # Shutdown
    logger.info("Shutting down AI News Manager microservice...")

app = FastAPI(
    title="AI News Manager",
    description="Персональный новостной аналитик для трейдеров",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",      # URL для Swagger UI
    redoc_url="/api/redoc"     # URL для ReDoc
)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "AI News Manager API",
        "version": "1.0.0",
        "environment": settings.environment
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = await check_db_connection()
    redis_status = await check_redis_connection()

    return {
        "status": "healthy" if db_status and redis_status else "unhealthy",
        "services": {
            "database": "ok" if db_status else "error",
            "redis": "ok" if redis_status else "error"
        },
        "environment": settings.environment
    }


@app.get("/api/test")
async def test_auth(user=Depends(get_user_from_header)):
    """Тестовый endpoint для проверки аутентификации"""
    return {
        "message": "Authentication successful!",
        "user": user
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
