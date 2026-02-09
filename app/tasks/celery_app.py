import asyncio
from celery import Celery
from celery.schedules import crontab
from app.config import settings


def run_async(coro):
    """
    Запуск async-корутины из синхронного Celery-таска.
    После выполнения сбрасывает пул соединений SQLAlchemy,
    чтобы избежать конфликта event loop при следующем вызове.
    """
    from app.database import engine
    try:
        return asyncio.run(coro)
    finally:
        engine.sync_engine.dispose()

celery_app = Celery(
    "ai_news_manager",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.telegram_parser",
        "app.tasks.news_classifier",
        "app.tasks.dashboards"
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# В режиме разработки включаем "eager" режим, расписание Beat не нужно
if settings.environment == "development":
    celery_app.conf.task_always_eager = True
else:
    celery_app.conf.beat_schedule = {
        "parse-telegram-channels": {
            "task": "app.tasks.telegram_parser.parse_all_channels",
            "schedule": settings.parse_interval_minutes * 60.0,  # каждые 30 мин (по умолчанию)
        },
        "classify-news-batch": {
            "task": "app.tasks.news_classifier.process_unprocessed_news_dispatcher",
            "schedule": 900.0,  # каждые 15 минут
        },
        "calculate-hot-topics": {
            "task": "app.tasks.dashboards.calculate_hot_topics",
            "schedule": 7200.0,  # каждые 2 часа
        },
        "cleanup-redis-cache": {
            "task": "app.tasks.dashboards.cleanup_stale_cache",
            "schedule": crontab(hour=3, minute=0),  # ежедневно в 03:00 UTC
        },
    }
