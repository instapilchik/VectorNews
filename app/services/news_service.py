from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.dialects.postgresql import insert
from app.ai.schemas import NewsMetadataSchema
from app.models.news import NewsPost
from app.database import async_session, get_db_info, check_db_connection
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        pass

    async def get_news_by_id(self, news_id: int) -> Optional[NewsPost]:
        """Получение одной новости по её ID."""
        async with async_session() as session:
            stmt = select(NewsPost).where(NewsPost.id == news_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_news_by_ids(self, news_ids: List[int]) -> List[NewsPost]:
        """Получение списка новостей по списку их ID."""
        if not news_ids:
            return []
        async with async_session() as session:
            stmt = select(NewsPost).where(NewsPost.id.in_(news_ids))
            result = await session.execute(stmt)
            # Сохраняем исходный порядок ID, который вернул Qdrant (по релевантности)
            news_map = {news.id: news for news in result.scalars().all()}
            sorted_news = [news_map[id] for id in news_ids if id in news_map]
            return sorted_news

    async def update_news_with_metadata(self, news_id: int, metadata: NewsMetadataSchema) -> None:
        """Обновление новости обогащенными метаданными."""
        async with async_session() as session:
            try:
                news_post = await session.get(NewsPost, news_id)
                if not news_post:
                    logger.warning(f"News post with id {news_id} not found for metadata update.")
                    return

                news_post.category = metadata.category.value
                news_post.summary = metadata.summary
                news_post.keywords = metadata.keywords
                news_post.entities = metadata.entities.model_dump()
                news_post.importance_score = metadata.importance_score

                await session.commit()
                logger.info(f"Successfully updated metadata for news_id: {news_id}")

            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating news metadata for id {news_id}: {e}")
                raise e

    async def save_news_batch(self, news_items: List[Dict]) -> int:
        """Сохранение батча новостей с дедупликацией"""
        if not news_items:
            return 0

        async with async_session() as session:
            try:
                saved_count = 0
                for item in news_items:
                    # Используем ON CONFLICT для дедупликации
                    stmt = insert(NewsPost).values(**item)
                    stmt = stmt.on_conflict_do_nothing(
                        index_elements=['telegram_id', 'source_channel']
                    )
                    result = await session.execute(stmt)
                    if result.rowcount > 0:
                        saved_count += 1

                await session.commit()
                logger.info(f"Saved {saved_count} new news items out of {len(news_items)} total")
                return saved_count

            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving news batch: {e}", exc_info=True)
                raise e

    async def get_last_parsed_time(self, channel: str) -> Optional[datetime]:
        """Получение времени последней записи для канала"""
        async with async_session() as session:
            stmt = select(NewsPost.published_at).where(
                NewsPost.source_channel == channel
            ).order_by(desc(NewsPost.published_at)).limit(1)

            result = await session.execute(stmt)
            last_time = result.scalar_one_or_none()
            return last_time

    async def get_unprocessed_news(self, limit: int = 20) -> List[NewsPost]:
        """Получение необработанных новостей для классификации"""
        async with async_session() as session:
            stmt = select(NewsPost).where(
                and_(
                    NewsPost.is_processed == False,
                    NewsPost.original_text.isnot(None)
                )
            ).order_by(NewsPost.created_at).limit(limit)

            result = await session.execute(stmt)
            return result.scalars().all()

    async def mark_as_processed(self, news_ids: List[int]) -> None:
        """Пометка новостей как обработанных"""
        async with async_session() as session:
            stmt = select(NewsPost).where(NewsPost.id.in_(news_ids))
            result = await session.execute(stmt)
            news_posts = result.scalars().all()

            for post in news_posts:
                post.is_processed = True
                post.processed_at = datetime.utcnow()

            await session.commit()

    async def search_news(
            self,
            query: str = None,
            time_range: str = "1d",
            sectors: List[str] = None,
            limit: int = 50
    ) -> List[NewsPost]:
        """Поиск новостей с фильтрацией"""
        async with async_session() as session:
            # Определяем временной диапазон
            time_delta = {
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "1d": timedelta(days=1),
                "3d": timedelta(days=3),
                "1w": timedelta(weeks=1)
            }.get(time_range, timedelta(days=1))

            since_date = datetime.utcnow() - time_delta

            # Базовый запрос
            stmt = select(NewsPost).where(
                and_(
                    NewsPost.published_at >= since_date,
                    NewsPost.is_spam == False
                )
            )

            # Фильтр по тексту
            if query:
                stmt = stmt.where(
                    or_(
                        NewsPost.original_text.ilike(f"%{query}%"),
                        NewsPost.processed_text.ilike(f"%{query}%")
                    )
                )

            # Фильтр по секторам
            if sectors:
                stmt = stmt.where(NewsPost.sector.in_(sectors))

            stmt = stmt.order_by(desc(NewsPost.importance_score), desc(NewsPost.published_at)).limit(limit)

            result = await session.execute(stmt)
            return result.scalars().all()
