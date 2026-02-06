import json
import logging
from typing import Optional
from app.ai.client import openrouter_client
from app.ai.models import model_selector, TaskType, ComplexityLevel
from app.ai.schemas import NewsMetadataSchema, StructuredQuerySchema, NewsCategory
from pydantic import ValidationError, BaseModel
from app.schemas.agent_settings import AgentSettingsSchema # НОВЫЙ ИМПОРТ

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = openrouter_client
        self.model_selector = model_selector

    def _get_metadata_system_prompt(self) -> str:
        """Промпт для задачи извлечения метаданных из новости."""
        return f"""
        Ты — беспристрастный и точный AI-аналитик финансовых новостей. 
        Всегда отвечай строго в формате JSON, который я тебе даю.
        Формат (JSON Schema):
        {json.dumps(NewsMetadataSchema.model_json_schema(), ensure_ascii=False, indent=2)}

        Твои правила:
        - Не добавляй никаких комментариев или текста вне JSON.
        - Все поля обязательны.
        - Значения должны быть на русском языке.
        - Если информации нет — ставь пустой массив или null, но поле должно присутствовать.
        """

    def _get_query_structuring_system_prompt(self, settings: Optional[AgentSettingsSchema] = None) -> str:
        """Промпт для задачи структурирования запроса пользователя."""
        categories_list = [e.value for e in NewsCategory]

        schema_json_string = json.dumps(StructuredQuerySchema.model_json_schema(), ensure_ascii=False, indent=2)

        # --- КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ ---
        user_context_prompt = ""
        if settings and settings.focus_interests:
            user_context_prompt = f"\nКОНТЕКСТ ПОЛЬЗОВАТЕЛЯ: Его основные интересы - {settings.focus_interests}. Учитывай это при переформулировании общего запроса в более конкретный."

        return f"""Ты - AI-помощник для анализа запросов к новостной базе. Твоя задача - превратить запрос пользователя в структурированный JSON-объект для поиска.

Доступные категории: {categories_list}.

Правила:
- `search_query`: переформулируй запрос для семантического поиска, убери мусор.
- `filter_categories`: укажи 1-3 конкретные категории, ТОЛЬКО если запрос явно про конкретную тему. Для широких запросов ("новости за неделю", "что нового", "топ новостей", "сводка") — верни null, чтобы искать по всем категориям.
- `time_range_days`: определи глубину поиска (1, 3, 7, 14, 30).
{user_context_prompt}

Строго придерживайся следующей JSON Schema:
```json
{schema_json_string}
```"""
    async def _extract_structured_data(
            self,
            system_prompt: str,
            user_prompt: str,
            schema: BaseModel,
            model_name: str
    ) -> Optional[BaseModel]:
        """Универсальный и исправленный метод для извлечения структурированных данных."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response_schema_dict = {"type": "json_object", "json_schema": schema.model_json_schema()}
            response = await self.client.complete_with_structured_output(
                model=model_name,
                messages=messages,
                response_format=response_schema_dict,
                temperature=0.1
            )

            structured_data = response.get("structured_data")
            if not structured_data:
                logger.error(f"LLM failed to return structured data for model {model_name}.")
                return None

            # Валидация данных через Pydantic
            validated_data = schema(**structured_data)
            logger.info(f"Successfully extracted and validated data using schema {schema.__name__}.")
            return validated_data

        except ValidationError as e:
            logger.error(f"Pydantic validation error for LLM response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during structured data extraction: {e}")
            raise e

    async def extract_news_metadata(self, text: str) -> Optional[NewsMetadataSchema]:
        """Извлекает метаданные новости."""
        model_name = self.model_selector.select_model(
            TaskType.NEWS_CLASSIFICATION,
            ComplexityLevel.SIMPLE)

        system_prompt = self._get_metadata_system_prompt()
        user_prompt = f"Проанализируй следующий новостной текст и верни результат в формате JSON:\n\n---\n{text}\n---"

        return await self._extract_structured_data(
            system_prompt,
            user_prompt,
            NewsMetadataSchema,
            model_name)


    async def generate_structured_query(self, query: str, settings: Optional[AgentSettingsSchema] = None) -> StructuredQuerySchema:
        """Генерирует структурированную 'дорожную карту' для поиска из запроса пользователя."""
        model_name = self.model_selector.select_model(TaskType.FILTERING, ComplexityLevel.SIMPLE, prefer_speed=True)

        system_prompt = self._get_query_structuring_system_prompt(settings) # Передаем настройки
        user_prompt = f"Запрос пользователя: '{query}'"

        try:
            structured_query = await self._extract_structured_data(
                system_prompt,
                user_prompt,
                StructuredQuerySchema,
                model_name
            )
            return structured_query or StructuredQuerySchema(search_query=query)  # Fallback
        except Exception:
            logger.warning(f"Failed to generate structured query for: '{query}'. Using fallback.")
            return StructuredQuerySchema(search_query=query)


llm_service = LLMService()
