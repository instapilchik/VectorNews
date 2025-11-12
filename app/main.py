from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"Загружены переменные окружения из {dotenv_path}")
else:
    print(f"Внимание: файл .env не найден в {dotenv_path}")

from fastapi import FastAPI, Depends, HTTPException
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

if settings.environment == "development":
    import nest_asyncio
    nest_asyncio.apply()


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
from app.api.endpoints import agent as agent_router
from app.api.endpoints import agent_settings as agent_settings_router
from app.api.endpoints import dashboards as dashboards_router

app.include_router(agent_router.router, prefix="/api/agent", tags=["AI Agent"])
app.include_router(agent_settings_router.router, prefix="/api/agent", tags=["AI Agent Settings"])
app.include_router(dashboards_router.router, prefix="/api/dashboards", tags=["Dashboards"])

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "AI News Manager API",
        "version": "1.0.0",
        "environment": settings.environment,
        "telegram_channels": settings.telegram_channels
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


# Новые endpoints для тестирования парсинга
@app.post("/api/admin/parse-channel")
async def manual_parse_channel(
        channel: str,
        days_back: int = 1,
        user=Depends(get_user_from_header)
):
    """Ручной запуск парсинга канала (для админов)"""
    from app.tasks.telegram_parser import parse_single_channel

    try:
        task = parse_single_channel.delay(channel, days_back)
        return {
            "message": f"Parsing task started for {channel}",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/initial-fill")
async def start_initial_fill(user=Depends(get_user_from_header)):
    """Запуск первичного наполнения БД"""
    from app.tasks.telegram_parser import initial_db_fill
    # from app.services.vector_db_service import vector_db_service
    # vector_db_service.initialize_collection(vector_size=768)

    try:
        task = initial_db_fill.delay()
        return {
            "message": "Initial database fill started",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/process_unprocessed_news_dispatcher")
async def start_unprocessed(user=Depends(get_user_from_header)):
    """Тест-ендпоинт для ручного запуска процессирования пайплайна"""
    from app.tasks.news_classifier import process_unprocessed_news_dispatcher
    # from app.services.vector_db_service import vector_db_service
    # vector_db_service.initialize_collection(vector_size=768)

    try:
        task = process_unprocessed_news_dispatcher.delay()
        return {
            "message": "Processing unprocessed news started",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/calculate_hot_topics")
async def start_hot_topics_calculation(user=Depends(get_user_from_header)):
    """Ендпоинт для ручного запуска расчёта горячих тем"""
    from app.tasks.dashboards import calculate_hot_topics

    try:
        task = calculate_hot_topics.delay()
        return {
            "message": "Hot topics calculation started",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news/recent")
async def get_recent_news(
        limit: int = 20,
        hours: int = 24,
        user=Depends(get_user_from_header)
):
    """Получение последних новостей"""
    from app.services.news_service import NewsService

    try:
        news_service = NewsService()
        time_range = f"{hours}h" if hours <= 24 else f"{hours // 24}d"
        news = await news_service.search_news(time_range=time_range, limit=limit)

        return {
            "count": len(news),
            "news": [
                {
                    "id": item.id,
                    "source": item.source_channel,
                    "text": item.original_text[:200] + "..." if len(item.original_text) > 200 else item.original_text,
                    "published_at": item.published_at,
                    "category": item.estimated_category,
                    "views": item.views_count,
                    "tg_link": item.tg_link
                }
                for item in news
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )