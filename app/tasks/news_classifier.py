from app.tasks.celery_app import celery_app
from app.services.news_service import NewsService
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def classify_unprocessed_news(self):
    """Классификация новостей (заглушка для этапа 3)"""
    logger.info("News classification task called (stub for stage 3)")
    # TODO: Реализовать в этапе 3
    pass

@celery_app.task(bind=True)
def classify_news_batch(self, news_ids: list):
    """Батчевая классификация новостей (заглушка для этапа 3)"""
    logger.info(f"Batch classification task called for {len(news_ids)} items (stub for stage 3)")
    # TODO: Реализовать в этапе 3
    pass
