import httpx
import json
import logging
from typing import Dict, List, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Клиент для работы с OpenRouter API"""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-news-manager.com",  # Опционально
            "X-Title": "AI News Manager",
        }

    async def complete(
            self,
            messages: List[Dict[str, str]],
            model: str,
            tools: Optional[List[Dict]] = None,
            max_tokens: int = 1000,
            temperature: float = 0.7,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Отправка запроса на генерацию через OpenRouter

        Args:
            messages: Список сообщений в формате OpenAI
            model: Название модели (e.g., "anthropic/claude-3-sonnet")
            tools: Список tools для агента
            max_tokens: Максимальное количество токенов
            temperature: Температура генерации
            **kwargs: Дополнительные параметры

        Returns:
            Ответ от API в формате OpenAI
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs
            }

            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    raise Exception(f"OpenRouter API error: {response.status_code}")

                result = response.json()

                # Логируем использование
                usage = result.get("usage", {})
                logger.info(f"Model {model} used: {usage.get('total_tokens', 0)} tokens")

                return result

        except httpx.TimeoutException:
            logger.error("OpenRouter API timeout")
            raise Exception("OpenRouter API timeout")
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            raise e

    async def complete_with_structured_output(
            self,
            messages: List[Dict[str, str]],
            model: str,
            response_format: Dict,
            max_tokens: int = 1000,
            temperature: float = 0.1,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Запрос с структурированным ответом (JSON Schema)
        Полезно для классификации новостей
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "response_format": response_format,
                **kwargs
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )

                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    raise Exception(f"OpenRouter API error: {response.status_code}")

                result = response.json()

                # Пытаемся распарсить JSON ответ
                content = result["choices"][0]["message"]["content"]
                try:
                    structured_data = json.loads(content)
                    result["structured_data"] = structured_data
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse structured output: {e}")
                    result["structured_data"] = None

                return result

        except Exception as e:
            logger.error(f"Error in structured completion: {e}")
            raise e

    async def get_available_models(self) -> List[Dict]:
        """Получение списка доступных моделей"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self.headers
                )

                if response.status_code == 200:
                    return response.json()["data"]
                else:
                    logger.error(f"Failed to get models: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []


# Singleton instance
openrouter_client = OpenRouterClient()