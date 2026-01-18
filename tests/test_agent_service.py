"""Тесты AgentService — юнит-тесты для reranking и relevance gate."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


def _make_news(news_id, summary="Test news", text="Some original text"):
    """Создает мок объекта NewsPost."""
    news = MagicMock()
    news.id = news_id
    news.summary = summary
    news.original_text = text
    news.published_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    news.tg_link = f"https://t.me/test/{news_id}"
    news.source_channel = "test_channel"
    return news


@pytest.fixture
def agent_service():
    """Создает AgentService с замоканными зависимостями."""
    with patch("app.services.agent_service.vector_db_service"), \
         patch("app.services.agent_service.embedding_service"), \
         patch("app.services.agent_service.reranker_service"), \
         patch("app.services.agent_service.llm_service"), \
         patch("app.services.agent_service.model_selector"), \
         patch("app.services.agent_service.agent_settings_service"), \
         patch("app.services.agent_service.cache_service"):
        from app.services.agent_service import AgentService
        svc = AgentService()
        svc.reranker = MagicMock()
        svc.cache = AsyncMock()
        svc.cache.get = AsyncMock(return_value=None)
        return svc


class TestReranking:
    def test_rerank_small_list_no_change(self, agent_service):
        """Если новостей меньше context_news_count, reranking не нужен."""
        items = [_make_news(i) for i in range(5)]
        result = agent_service._rerank_news("test query", items)
        assert len(result) == 5
        agent_service.reranker.rerank.assert_not_called()

    def test_rerank_reorders_items(self, agent_service):
        """Reranker должен переупорядочить элементы по score."""
        items = [_make_news(i) for i in range(20)]
        # reranker возвращает пары (original_index, score)
        agent_service.reranker.rerank.return_value = [
            (15, 5.0), (3, 4.5), (7, 4.0), (0, 3.5), (11, 3.0)
        ]
        result = agent_service._rerank_news("test query", items)

        assert len(result) == 5
        assert result[0].id == 15
        assert result[1].id == 3

    def test_rerank_failure_returns_original(self, agent_service):
        """При ошибке reranker-а возвращается исходный список."""
        items = [_make_news(i) for i in range(20)]
        agent_service.reranker.rerank.side_effect = RuntimeError("model error")
        result = agent_service._rerank_news("test query", items)
        assert len(result) == 20

    def test_rerank_empty_list(self, agent_service):
        """Пустой список не должен ломать reranking."""
        result = agent_service._rerank_news("test query", [])
        assert result == []


class TestRelevanceGate:
    def test_no_items_returns_false(self, agent_service):
        """Пустой список — данных недостаточно."""
        assert agent_service._check_relevance("query", []) is False

    def test_high_score_passes(self, agent_service):
        """Высокий score reranker-а — данные релевантны."""
        items = [_make_news(1, summary="Bitcoin вырос до 100k")]
        agent_service.reranker.rerank.return_value = [(0, 2.5)]
        assert agent_service._check_relevance("Bitcoin price", items) is True

    def test_low_score_fails(self, agent_service):
        """Очень низкий score — данные не релевантны."""
        items = [_make_news(1, summary="Кот спит")]
        agent_service.reranker.rerank.return_value = [(0, -5.0)]
        assert agent_service._check_relevance("Bitcoin price", items) is False

    def test_reranker_error_passes(self, agent_service):
        """При ошибке reranker-а лучше пропустить, чем заблокировать."""
        items = [_make_news(1)]
        agent_service.reranker.rerank.side_effect = RuntimeError("error")
        assert agent_service._check_relevance("query", items) is True

    def test_boundary_score(self, agent_service):
        """Score ровно на границе -2.0 не проходит (строго >)."""
        items = [_make_news(1)]
        agent_service.reranker.rerank.return_value = [(0, -2.0)]
        assert agent_service._check_relevance("query", items) is False


class TestProcessQuery:
    @pytest.mark.asyncio
    async def test_cache_hit_skips_pipeline(self, agent_service):
        """Если ответ в кеше, не нужно запускать весь пайплайн."""
        agent_service.cache.get = AsyncMock(return_value={
            "answer": "Cached answer",
            "sources": [{"id": 1, "tg_link": "link", "summary": "s", "source_channel": "ch", "published_at": "2026-01-01"}]
        })
        agent_service.settings_service.get_settings = AsyncMock()

        answer, sources = await agent_service.process_query("test", "user1")

        assert answer == "Cached answer"
        assert len(sources) == 1
        # get_settings не должен вызываться при попадании в кеш
        agent_service.settings_service.get_settings.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_results_returns_message(self, agent_service):
        """Если поиск не нашел ничего, возвращается сообщение."""
        from app.schemas.agent_settings import AgentSettingsSchema
        agent_service.settings_service.get_settings = AsyncMock(
            return_value=AgentSettingsSchema()
        )
        agent_service.llm_service.generate_structured_query = AsyncMock(
            return_value=MagicMock(
                search_query="test", filter_categories=None,
                time_range_days=7, model_dump_json=MagicMock(return_value="{}")
            )
        )
        agent_service.embedding.get_embedding = MagicMock(return_value=[0.1] * 768)
        agent_service.vector_db.search = MagicMock(return_value=[])

        answer, sources = await agent_service.process_query("test", "user1")

        assert "не удалось найти" in answer.lower()
        assert sources == []
