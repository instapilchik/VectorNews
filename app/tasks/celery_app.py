from celery import Celery
from app.config import settings

celery_app = Celery(
    "ai_news_manager",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.telegram_parser",
        "app.tasks.news_classifier"  # Для этапа 3
    ]
)
# Если мы в режиме разработки, включаем "eager" режим
if settings.environment == "development":
    celery_app.conf.task_always_eager = True

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Расписание задач
    beat_schedule={
        "parse-telegram-channels": {
            "task": "app.tasks.telegram_parser.parse_all_channels",
            "schedule": settings.parse_interval_minutes * 60.0,  # в секундах
        },
        "classify-news-batch": {
            "task": "app.tasks.news_classifier.process_unprocessed_news_dispatcher", # TODO: проверить
            "schedule": 60.0,  # каждые 5 минут (заглушка для этапа 3)
        },
    },
)
