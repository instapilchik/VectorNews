from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"Загружены переменные окружения из {dotenv_path}")
else:
    print(f"Внимание: файл .env не найден в {dotenv_path}")

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.database import init_db, check_db_connection, check_redis_connection
from app.api.deps import get_authenticated_user, require_admin, limiter

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
    version="1.2.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from app.api.endpoints import agent as agent_router
from app.api.endpoints import agent_settings as agent_settings_router
from app.api.endpoints import dashboards as dashboards_router
from app.api.endpoints import auth as auth_router
from app.api.endpoints import admin_users as admin_users_router

app.include_router(agent_router.router, prefix="/api/agent", tags=["AI Agent"])
app.include_router(agent_settings_router.router, prefix="/api/agent", tags=["AI Agent Settings"])
app.include_router(dashboards_router.router, prefix="/api/dashboards", tags=["Dashboards"])
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_users_router.router, prefix="/api/admin", tags=["Admin - Users"])

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "AI News Manager API",
        "version": "1.2.0",
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



# Новые endpoints для тестирования парсинга (admin-only via JWT)
@app.post("/api/admin/parse-channel")
async def manual_parse_channel(
        channel: str,
        days_back: int = 1,
        user=Depends(require_admin)
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
async def start_initial_fill(user=Depends(require_admin)):
    """Запуск первичного наполнения БД"""
    from app.tasks.telegram_parser import initial_db_fill

    try:
        task = initial_db_fill.delay()
        return {
            "message": "Initial database fill started",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/process_unprocessed_news_dispatcher")
async def start_unprocessed(user=Depends(require_admin)):
    """Тест-ендпоинт для ручного запуска процессирования пайплайна"""
    from app.tasks.news_classifier import process_unprocessed_news_dispatcher

    try:
        task = process_unprocessed_news_dispatcher.delay()
        return {
            "message": "Processing unprocessed news started",
            "task_id": task.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/calculate_hot_topics")
async def start_hot_topics_calculation(user=Depends(require_admin)):
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
        offset: int = 0,
        hours: int = 24,
        user=Depends(get_authenticated_user)
):
    """Получение последних новостей с пагинацией"""
    from app.services.news_service import NewsService

    try:
        news_service = NewsService()
        time_range = f"{hours}h" if hours <= 24 else f"{hours // 24}d"

        news = await news_service.search_news(
            time_range=time_range, limit=limit, offset=offset
        )
        total = await news_service.count_news(time_range=time_range)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(news),
            "news": [
                {
                    "id": item.id,
                    "source": item.source_channel,
                    "text": item.original_text[:200] + "..." if len(item.original_text) > 200 else item.original_text,
                    "published_at": item.published_at,
                    "category": item.category or item.estimated_category,
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
