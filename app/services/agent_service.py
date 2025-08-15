
import logging
from typing import List, Tuple
from app.services.vector_db_service import vector_db_service
from app.services.embedding_service import embedding_service
from app.services.news_service import NewsService
from app.models.news import NewsPost
from app.services.llm_service import llm_service  # НОВЫЙ ИМПОРТ
from app.ai.models import model_selector, TaskType, ComplexityLevel  # НОВЫЙ ИМПОРТ

logger = logging.getLogger(__name__)


# Определим простую структуру для источников, чтобы не тащить всю модель NewsPost
class NewsSource:
    def __init__(self, id: int, tg_link: str, summary: str, source_channel: str, published_at: str):
        self.id = id
        self.tg_link = tg_link
        self.summary = summary
        self.source_channel = source_channel
        self.published_at = published_at


class AgentService:
    def __init__(self):
        self.news_service = NewsService()
        self.vector_db = vector_db_service
        self.embedding = embedding_service
        self.llm_service = llm_service
        self.model_selector = model_selector
        self.search_limit = 50  # Сколько кандидатов ищем в векторной базе
        self.context_news_count = 10  # Сколько новостей даем в контекст LLM
        self.final_sources_count = 5  # Сколько источников показываем пользователю

    async def _search_relevant_news_ids(self, query: str) -> List[int]:
        """Шаг 1: Векторизует запрос и находит ID релевантных новостей в Qdrant."""
        logger.info(f"Searching for relevant news for query: '{query[:50]}...'")

        # Префикс 'query:' используется для запросов, как рекомендовано для e5 моделей
        query_vector = self.embedding.get_embedding(f"query: {query}")

        # Ищем в Qdrant. Пока без фильтров, просто топ-N по семантической близости.
        search_results = self.vector_db.search(vector=query_vector, limit=self.search_limit)

        if not search_results:
            logger.warning("No relevant news found in vector database.")
            return []

        news_ids = [result.id for result in search_results]
        logger.info(f"Found {len(news_ids)} candidate news items in Qdrant.")
        return news_ids

    async def _synthesize_answer(self, query: str, news_context: List[NewsPost]) -> str:
        """
        Шаг 2: Генерирует связный ответ на основе найденных новостей с помощью LLM.
        """
        if not news_context:
            return "Не удалось найти достаточно информации для ответа на ваш вопрос."

        # 1. Формируем контекст из текстов новостей
        context_str = ""
        for i, news in enumerate(news_context, 1):
            context_str += f"Источник {i} (ID: {news.id}, Опубликовано: {news.published_at.strftime('%Y-%m-%d %H:%M')}):\n"
            # Приоритет отдаем summary, если оно есть, т.к. оно более емкое
            text_to_use = news.summary if news.summary else news.original_text
            context_str += f'"{text_to_use}"\n\n'

        # 2. Выбираем модель для анализа
        model_name = self.model_selector.select_model(
            task_type=TaskType.ANALYSIS,
            complexity=ComplexityLevel.MEDIUM
        )

        # 3. Формируем промпт для LLM
        system_prompt = """
        Ты - AI-новостной аналитик для трейдеров. Твоя задача - отвечать на вопросы пользователя, строго основываясь на предоставленных новостных источниках.
        - Отвечай структурированно, ясно и по делу.
        - Не выдумывай информацию, которой нет в источниках.
        - Если в источниках нет ответа на вопрос, честно скажи об этом.
        - Не давай никаких финансовых советов или прогнозов. Твоя роль - анализ и интерпретация новостей.
        """

        user_prompt = f"""
        Проанализируй следующие новостные источники и дай развернутый ответ на мой вопрос.

        НОВОСТНЫЕ ИСТОЧНИКИ:
        ---
        {context_str}
        ---

        МОЙ ВОПРОС:
        "{query}"
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # 4. Вызываем LLM
        logger.info(f"Synthesizing answer with model: {model_name}")
        response = await self.llm_service.client.complete(
            model=model_name,
            messages=messages,
            max_tokens=1500,  # Увеличим лимит для развернутого ответа
            temperature=0.3  # Низкая температура для более фактического ответа
        )

        answer = response["choices"][0]["message"]["content"]
        logger.info(f"Synthesized answer generated successfully.")
        return answer.strip()

    async def process_query(self, query: str) -> Tuple[str, List[NewsSource]]:
        """
        Основной метод обработки запроса. Теперь с генерацией ответа.
        """
        # 1. Найти ID релевантных новостей
        relevant_ids = await self._search_relevant_news_ids(query)
        if not relevant_ids:
            return "К сожалению, не удалось найти релевантных новостей по вашему запросу.", []

        # 2. Получить полные данные для этих новостей из PostgreSQL
        news_items = await self.news_service.get_news_by_ids(relevant_ids)
        if not news_items:
            # Такое может случиться, если ID в Qdrant есть, а в Postgres уже нет
            logger.warning(f"Could not retrieve news details for IDs: {relevant_ids}")
            return "Произошла ошибка при извлечении деталей новостей.", []

        # 3. Сгенерировать ответ на основе контекста
        # Передаем в контекст только часть самых релевантных новостей, чтобы не превысить лимит токенов
        context_for_synthesis = news_items[:self.context_news_count]
        generated_answer = await self._synthesize_answer(query, context_for_synthesis)

        # 4. Сформировать список источников для показа пользователю
        sources = [
            NewsSource(
                id=item.id,
                tg_link=item.tg_link,
                summary=item.summary or item.original_text[:250],  # Используем summary, если есть
                source_channel=item.source_channel,
                published_at=item.published_at.isoformat()
            )
            for item in news_items[:self.final_sources_count]  # Ограничиваем количество источников для показа
        ]

        return generated_answer, sources


# Singleton instance
agent_service = AgentService()
