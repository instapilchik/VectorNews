import json
import logging
from typing import Optional

from app.ai.client import openrouter_client
from app.ai.models import model_selector, TaskType, ComplexityLevel
from app.ai.schemas import NewsMetadataSchema
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = openrouter_client
        self.model_selector = model_selector

    def _get_system_prompt(self) -> str:
        # добавили схему в промпт для лучшего качества
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

    async def extract_news_metadata(self, text: str) -> Optional[NewsMetadataSchema]:
        """
        Извлекает структурированные метаданные из текста новости.
        """
        model_name = self.model_selector.select_model(
            task_type=TaskType.NEWS_CLASSIFICATION,
            complexity=ComplexityLevel.SIMPLE,
            prefer_cost=True
        )

        system_prompt = self._get_system_prompt()
        user_prompt = f"Проанализируй следующий новостной текст и верни результат в формате JSON:\n\n---\n{text}\n---"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response_schema = {"type": "json_object", "json_schema": NewsMetadataSchema.model_json_schema()}

            response = await self.client.complete_with_structured_output(
                model=model_name,
                messages=messages,
                response_format=response_schema,
                temperature=0.1
            )

            structured_data = response.get("structured_data")
            if not structured_data:
                logger.error(f"LLM failed to return structured data for model {model_name}.")
                return None

            # Валидация данных через Pydantic
            validated_data = NewsMetadataSchema(**structured_data)
            # TODO: при ошибках валидации отправлять на еще одну попытку
            logger.info(f"Successfully extracted and validated metadata for model {model_name}.")
            return validated_data

        except ValidationError as e:
            logger.error(f"Pydantic validation error for LLM response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during LLM metadata extraction: {e}")
            raise e


llm_service = LLMService()
