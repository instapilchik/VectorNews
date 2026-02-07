from app.tasks.celery_app import celery_app
from app.services.news_service import NewsService
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service
from app.services.vector_db_service import vector_db_service
from celery import chain
import logging
import asyncio

logger = logging.getLogger(__name__)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """
    Инициализация служб при старте воркера Celery.
    Например, создание коллекции в Qdrant.
    """
    logger.info("Initializing services for Celery worker...")
    # Размер вектора для модели 'intfloat/multilingual-e5-base' - 768
    vector_db_service.initialize_collection(vector_size=768)
    logger.info("Services initialized.")


@celery_app.task(name="app.tasks.news_classifier.process_unprocessed_news_dispatcher")
def process_unprocessed_news_dispatcher():
    """Находит необработанные новости и запускает для каждой конвейер обработки."""
    logger.info("Dispatcher started: Looking for unprocessed news.")
    news_service = NewsService()
    unprocessed_news_list = asyncio.run(news_service.get_unprocessed_news(limit=50))

    if not unprocessed_news_list:
        logger.info("No new news to process.")
        return {"status": "no_news"}

    logger.info(f"Found {len(unprocessed_news_list)} news items to process.")
    for news_item in unprocessed_news_list:

        processing_pipeline = chain(
            enrich_metadata.s(news_item.id),
            generate_vector_embedding.s(),  # s() без аргумента, т.к. он придет из предыдущей задачи
            # finalize_processing.s()
        )
        processing_pipeline.apply_async(
            # Помечаем новость как "обрабатываемую", чтобы диспетчер не взял ее снова
            link=mark_as_processed_on_success.s(news_item.id)
        )

    return {"status": "success", "tasks_dispatched": len(unprocessed_news_list)}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=180)
def enrich_metadata(self, news_id: int):
    """Шаг 1: Извлекает метаданные из текста новости с помощью LLM."""
    logger.info(f"[enrich_metadata] Starting for news_id: {news_id}")
    try:
        news_service = NewsService()
        news_item = asyncio.run(news_service.get_news_by_id(news_id))

        if not news_item or not news_item.original_text:
            logger.warning(f"[enrich_metadata] News item {news_id} not found or has no text. Skipping.")
            return news_id

        # Вызов LLM сервиса для извлечения метаданных
        metadata = asyncio.run(llm_service.extract_news_metadata(news_item.original_text))

        if not metadata:
            # Если LLM не смог извлечь данные, считаем это временной ошибкой и пробуем снова
            raise Exception(f"Failed to extract metadata for news_id {news_id}")

        # Сохранение метаданных в БД
        asyncio.run(news_service.update_news_with_metadata(news_id, metadata))

        logger.info(f"[enrich_metadata] Successfully processed news_id: {news_id}")
        return news_id  # Передаем news_id в следующую задачу цепочки

    except Exception as e:
        logger.error(f"[enrich_metadata] Error processing news_id {news_id}: {e}")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_vector_embedding(self, news_id: int):
    """
    Шаг 2: Создает и сохраняет векторное представление для новости.
    Принимает news_id от предыдущей задачи `enrich_metadata`.
    """
    logger.info(f"[generate_vector_embedding] Starting for news_id: {news_id}")
    try:
        news_service = NewsService()
        news_item = asyncio.run(news_service.get_news_by_id(news_id))

        if not news_item or not news_item.original_text:
            logger.warning(f"[generate_vector_embedding] News item {news_id} not found or has no text.")
            return news_id

        # Для эмбеддинга лучше использовать оригинальный текст, чтобы не терять нюансы
        text_to_embed = news_item.original_text

        # 1. Получаем вектор
        vector = embedding_service.get_embedding(text_to_embed)

        # 2. Готовим payload для фильтрации в Qdrant
        payload = {
            "source_channel": news_item.source_channel,
            "published_at_iso": news_item.published_at.isoformat(),
            "published_at": int(news_item.published_at.timestamp()),
            "category": news_item.category,
            "importance_score": news_item.importance_score,
            "language": news_item.language
        }
        # Убираем None значения, чтобы не засорять payload
        payload = {k: v for k, v in payload.items() if v is not None}

        # 3. Сохраняем вектор и payload в Qdrant
        vector_db_service.upsert_point(news_id=news_item.id, vector=vector, payload=payload)

        logger.info(f"[generate_vector_embedding] Successfully processed news_id: {news_id}")
        return news_id

    except Exception as e:
        logger.error(f"[generate_vector_embedding] Error processing news_id {news_id}: {e}")
        raise self.retry(exc=e)


@celery_app.task
def mark_as_processed_on_success(previous_task_result, news_id: int):
    """
    Коллбэк: помечает новость как обработанную после успешного завершения цепочки.
    `previous_task_result` содержит результат последней задачи в цепочке (у нас это news_id).
    """
    logger.info(f"[finalize] Marking news as processed: {news_id}")
    news_service = NewsService()
    asyncio.run(news_service.mark_as_processed([news_id]))
    return {"status": "processed", "news_id": news_id}


