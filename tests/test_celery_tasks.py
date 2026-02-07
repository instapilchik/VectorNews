"""Тесты Celery-задач: news_classifier pipeline."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


def _make_news_item(news_id=1, text="Рубль упал до 95 за доллар"):
    """Создает мок объекта NewsPost."""
    item = MagicMock()
    item.id = news_id
    item.original_text = text
    item.source_channel = "@test_channel"
    item.published_at = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    item.category = "Экономика"
    item.importance_score = 0.8
    item.language = "ru"
    return item


def _sync_run(coro):
    """Замена asyncio.run — просто вызывает корутину синхронно через loop."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestEnrichMetadata:
    def test_successful_enrichment(self):
        """Задача enrich_metadata должна вызвать LLM и сохранить результат."""
        mock_news = _make_news_item()
        mock_metadata = MagicMock()

        with patch("app.tasks.news_classifier.NewsService") as MockNewsService, \
             patch("app.tasks.news_classifier.llm_service") as mock_llm, \
             patch("app.tasks.news_classifier.asyncio.run", side_effect=_sync_run):

            mock_svc = MockNewsService.return_value
            mock_svc.get_news_by_id = AsyncMock(return_value=mock_news)
            mock_llm.extract_news_metadata = AsyncMock(return_value=mock_metadata)
            mock_svc.update_news_with_metadata = AsyncMock()

            from app.tasks.news_classifier import enrich_metadata
            # Вызываем напрямую (не через .delay) — в eager-режиме Celery так и делает
            result = enrich_metadata(1)

            assert result == 1
            mock_llm.extract_news_metadata.assert_called_once()
            mock_svc.update_news_with_metadata.assert_called_once()

    def test_skips_when_no_text(self):
        """Если у новости нет текста, задача должна пропустить обработку."""
        mock_news = _make_news_item()
        mock_news.original_text = None

        with patch("app.tasks.news_classifier.NewsService") as MockNewsService, \
             patch("app.tasks.news_classifier.llm_service") as mock_llm, \
             patch("app.tasks.news_classifier.asyncio.run", side_effect=_sync_run):

            mock_svc = MockNewsService.return_value
            mock_svc.get_news_by_id = AsyncMock(return_value=mock_news)

            from app.tasks.news_classifier import enrich_metadata
            result = enrich_metadata(1)

            assert result == 1
            mock_llm.extract_news_metadata.assert_not_called()


class TestGenerateVectorEmbedding:
    def test_successful_embedding(self):
        """Задача должна создать вектор и сохранить его в Qdrant."""
        mock_news = _make_news_item()

        with patch("app.tasks.news_classifier.NewsService") as MockNewsService, \
             patch("app.tasks.news_classifier.embedding_service") as mock_emb, \
             patch("app.tasks.news_classifier.vector_db_service") as mock_vdb, \
             patch("app.tasks.news_classifier.asyncio.run", side_effect=_sync_run):

            mock_svc = MockNewsService.return_value
            mock_svc.get_news_by_id = AsyncMock(return_value=mock_news)
            mock_emb.get_embedding = MagicMock(return_value=[0.1] * 768)

            from app.tasks.news_classifier import generate_vector_embedding
            result = generate_vector_embedding(1)

            assert result == 1
            mock_emb.get_embedding.assert_called_once_with(mock_news.original_text)
            mock_vdb.upsert_point.assert_called_once()

    def test_skips_when_no_text(self):
        """Если у новости нет текста, пропускаем создание эмбеддинга."""
        mock_news = _make_news_item()
        mock_news.original_text = None

        with patch("app.tasks.news_classifier.NewsService") as MockNewsService, \
             patch("app.tasks.news_classifier.embedding_service") as mock_emb, \
             patch("app.tasks.news_classifier.vector_db_service"), \
             patch("app.tasks.news_classifier.asyncio.run", side_effect=_sync_run):

            mock_svc = MockNewsService.return_value
            mock_svc.get_news_by_id = AsyncMock(return_value=mock_news)

            from app.tasks.news_classifier import generate_vector_embedding
            result = generate_vector_embedding(1)

            assert result == 1
            mock_emb.get_embedding.assert_not_called()


class TestMarkAsProcessed:
    def test_marks_news_as_processed(self):
        """Коллбэк должен пометить новость как обработанную."""
        with patch("app.tasks.news_classifier.NewsService") as MockNewsService, \
             patch("app.tasks.news_classifier.asyncio.run", side_effect=_sync_run):

            mock_svc = MockNewsService.return_value
            mock_svc.mark_as_processed = AsyncMock()

            from app.tasks.news_classifier import mark_as_processed_on_success
            result = mark_as_processed_on_success(42, 42)

            assert result["status"] == "processed"
            assert result["news_id"] == 42
