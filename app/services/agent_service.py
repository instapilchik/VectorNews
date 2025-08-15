import logging
from typing import List
from app.services.vector_db_service import vector_db_service
from app.services.embedding_service import embedding_service
from app.services.news_service import NewsService
from app.models.news import NewsPost

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
        self.search_limit = 50  # Сколько кандидатов ищем в векторной базе
        self.final_sources_count = 5  # Сколько источников показываем пользователю

    async def _search_relevant_news_ids(self, query: str) -> List[int]:
        """
        Шаг 1: Векторизует запрос и находит ID релевантных новостей в Qdrant.
        """
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

    async def process_query(self, query: str) -> (str, List[NewsSource]):
        """
        Основной метод обработки запроса для Этапа 3.1.
        Находит релевантные новости и формирует "заглушку" ответа.
        """
        # 1. Найти ID релевантных новостей
        relevant_ids = await self._search_relevant_news_ids(query)
        if not relevant_ids:
            return "К сожалению, не удалось найти релевантных новостей по вашему запросу.", []

        # 2. Получить полные данные для этих новостей из PostgreSQL
        # Используем `get_news_by_ids` для эффективности
        news_items = await self.news_service.get_news_by_ids(relevant_ids)

        # 3. Сформировать ответ-заглушку и список источников
        answer_stub = "Вот что удалось найти по вашему запросу. Ниже приведены наиболее релевантные источники:"

        # Преобразуем полные модели NewsPost в легковесные NewsSource
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

        return answer_stub, sources


# Singleton instance
agent_service = AgentService()
