from celery import current_task
from app.tasks.celery_app import celery_app, run_async
from app.services.telegram_service import TelegramService
from app.config import settings
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def parse_all_channels(self):
    """Парсинг всех настроенных каналов"""
    try:
        logger.info("Starting scheduled parsing of all channels")
        total_saved = run_async(_parse_all_channels_async())
        logger.info(f"Parsing completed. Total saved: {total_saved}")
        return {"status": "success", "total_saved": total_saved}
    except Exception as e:
        logger.error(f"Error in parse_all_channels: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _parse_all_channels_async():
    """Асинхронная функция парсинга всех каналов"""
    telegram_service = TelegramService()
    total_saved = 0

    try:
        await telegram_service.connect()

        for channel in settings.telegram_channels:
            try:
                logger.info(f"Parsing channel: {channel}")
                saved_count = await telegram_service.parse_with_overlap(channel)
                total_saved += saved_count

                # Небольшая пауза между каналами
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error parsing channel {channel}: {e}")
                continue

        return total_saved

    finally:
        await telegram_service.disconnect()


@celery_app.task(bind=True)
def parse_single_channel(self, channel_username: str, days_back: int = 7):
    """Парсинг одного канала (для восстановления после сбоев)"""
    try:
        logger.info(f"Manual parsing of channel: {channel_username}")
        result = run_async(_parse_single_channel_async(channel_username, days_back))
        return {"status": "success", "channel": channel_username, "saved": result}
    except Exception as e:
        logger.error(f"Error in parse_single_channel {channel_username}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


async def _parse_single_channel_async(channel_username: str, days_back: int):
    """Асинхронная функция парсинга одного канала"""
    telegram_service = TelegramService()

    try:
        await telegram_service.connect()

        from datetime import datetime, timedelta
        stop_date = datetime.utcnow() - timedelta(days=days_back)

        news_items = await telegram_service.parse_channel_messages(
            channel_username=channel_username,
            stop_at_date=stop_date
        )

        if news_items:
            from app.services.news_service import NewsService
            news_service = NewsService()
            saved_count = await news_service.save_news_batch(news_items)
            return saved_count

        return 0

    finally:
        await telegram_service.disconnect()


@celery_app.task(bind=True)
def initial_db_fill(self):
    """Первичное наполнение БД (запускается вручную)"""
    try:
        logger.info("Starting initial database fill")
        total_saved = 0

        for channel in settings.telegram_channels:
            logger.info(f"Initial fill for channel: {channel}")
            result = parse_single_channel.delay(channel, days_back=14)  # 2 недели назад
            # В реальности лучше запускать последовательно для контроля

        return {"status": "started", "message": "Initial fill tasks dispatched"}
    except Exception as e:
        logger.error(f"Error in initial_db_fill: {e}")
        raise e
