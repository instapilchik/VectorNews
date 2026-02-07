"""Тесты LLMService — извлечение метаданных и структурирование запросов."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.ai.schemas import NewsMetadataSchema, StructuredQuerySchema, NewsCategory


@pytest.fixture
def llm_service():
    """Создает LLMService с замоканным OpenRouter-клиентом."""
    with patch("app.services.llm_service.openrouter_client") as mock_client, \
         patch("app.services.llm_service.model_selector") as mock_selector:
        mock_selector.select_model = MagicMock(return_value="test-model")
        from app.services.llm_service import LLMService
        svc = LLMService()
        svc.client = mock_client
        svc.model_selector = mock_selector
        return svc


class TestMetadataPrompt:
    def test_prompt_contains_schema(self, llm_service):
        """Системный промпт должен содержать JSON Schema для валидации."""
        prompt = llm_service._get_metadata_system_prompt()
        assert "JSON" in prompt
        assert "category" in prompt
        assert "sentiment" in prompt
        assert "importance_score" in prompt

    def test_prompt_contains_rules(self, llm_service):
        """Промпт должен содержать правила для LLM."""
        prompt = llm_service._get_metadata_system_prompt()
        assert "enum" in prompt.lower() or "допустимых значений" in prompt


class TestQueryStructuringPrompt:
    def test_prompt_without_settings(self, llm_service):
        """Промпт без настроек пользователя не должен содержать контекст."""
        prompt = llm_service._get_query_structuring_system_prompt(settings=None)
        assert "search_query" in prompt
        assert "filter_categories" in prompt
        assert "КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ" not in prompt

    def test_prompt_with_settings(self, llm_service):
        """Промпт с настройками должен включать интересы пользователя."""
        from app.schemas.agent_settings import AgentSettingsSchema
        settings = AgentSettingsSchema(
            focus_interests=["Геополитика", "Криптовалюты"],
            historical_context_days=14
        )
        prompt = llm_service._get_query_structuring_system_prompt(settings=settings)
        assert "КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ" in prompt
        assert "Геополитика" in prompt
        assert "14" in prompt


class TestExtractNewsMetadata:
    @pytest.mark.asyncio
    async def test_successful_extraction(self, llm_service):
        """Успешное извлечение метаданных из текста новости."""
        mock_response = {
            "structured_data": {
                "is_spam": False,
                "is_advertisement": False,
                "is_humor": False,
                "is_financial_relevant": True,
                "category": "Экономика",
                "sector": "currency",
                "sentiment": "negative",
                "importance_score": 0.8,
                "classification_confidence": 0.9,
                "summary": "Рубль ослаб на фоне санкций",
                "keywords": ["рубль", "санкции", "курс"],
                "tags": ["рубль", "валюта"],
                "entities": {"persons": [], "companies": ["ЦБ РФ"], "locations": ["Россия"]}
            }
        }
        llm_service.client.complete_with_structured_output = AsyncMock(return_value=mock_response)

        result = await llm_service.extract_news_metadata("Рубль упал до 95 за доллар на фоне новых санкций")

        assert result is not None
        assert isinstance(result, NewsMetadataSchema)
        assert result.category == NewsCategory.ECONOMY
        assert result.importance_score == 0.8

    @pytest.mark.asyncio
    async def test_extraction_returns_none_on_empty_response(self, llm_service):
        """Если LLM не вернул structured_data, возвращается None."""
        llm_service.client.complete_with_structured_output = AsyncMock(
            return_value={"structured_data": None}
        )
        result = await llm_service.extract_news_metadata("Тестовый текст")
        assert result is None


class TestGenerateStructuredQuery:
    @pytest.mark.asyncio
    async def test_successful_generation(self, llm_service):
        """Успешная генерация структурированного запроса."""
        mock_response = {
            "structured_data": {
                "search_query": "курс рубля прогноз",
                "filter_categories": ["Экономика"],
                "time_range_days": 3
            }
        }
        llm_service.client.complete_with_structured_output = AsyncMock(return_value=mock_response)

        result = await llm_service.generate_structured_query("что с рублем?")

        assert isinstance(result, StructuredQuerySchema)
        assert result.search_query == "курс рубля прогноз"
        assert result.time_range_days == 3

    @pytest.mark.asyncio
    async def test_fallback_on_error(self, llm_service):
        """При ошибке LLM возвращается fallback с исходным запросом."""
        llm_service.client.complete_with_structured_output = AsyncMock(
            side_effect=Exception("API error")
        )
        result = await llm_service.generate_structured_query("тестовый запрос")

        assert isinstance(result, StructuredQuerySchema)
        assert result.search_query == "тестовый запрос"
        assert result.time_range_days == 7  # default

    @pytest.mark.asyncio
    async def test_fallback_on_none_response(self, llm_service):
        """Если LLM вернул None, используется fallback."""
        llm_service.client.complete_with_structured_output = AsyncMock(
            return_value={"structured_data": None}
        )
        result = await llm_service.generate_structured_query("запрос без ответа")

        assert isinstance(result, StructuredQuerySchema)
        assert result.search_query == "запрос без ответа"
