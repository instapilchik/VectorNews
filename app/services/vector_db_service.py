import logging
from datetime import datetime, timedelta
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, ScoredPoint
from app.config import settings
from typing import List, Dict, Any, Optional
from qdrant_client.http.models import SearchRequest

logger = logging.getLogger(__name__)

class VectorDBService:
    """
    Сервис для взаимодействия с векторной базой данных Qdrant.
    """
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60 # Увеличим таймаут для надежности
        )
        self.collection_name = settings.qdrant_collection_name

    def initialize_collection(self, vector_size: int):
        """

        Создает коллекцию в Qdrant, если она еще не существует.
        Этот метод следует вызывать при старте приложения или в отдельной CLI-команде.
        """
        try:
            # Проверяем, существует ли коллекция
            self.client.get_collection(collection_name=self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists.")
        except Exception:
            # Если коллекции нет, создаем ее
            logger.info(f"Collection '{self.collection_name}' not found. Creating...")
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                # Косинусное расстояние - стандарт для текстовых эмбеддингов
            )
            logger.info(f"Collection '{self.collection_name}' created successfully.")

    def upsert_point(self, news_id: int, vector: List[float], payload: Dict[str, Any]):
        """
        Добавляет или обновляет одну точку (вектор) в коллекции.
        """
        point = PointStruct(
            id=news_id,
            vector=vector,
            payload=payload
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
            wait=True # Ждем подтверждения от Qdrant
        )
        logger.debug(f"Upserted point for news_id: {news_id}")

    def find_near_duplicates(
        self,
        vector: List[float],
        published_at: datetime,
        source_channel: str,
        score_threshold: float = 0.93,
        time_window_hours: int = 1,
        limit: int = 3,
    ) -> List[ScoredPoint]:
        """
        Ищет семантически похожие новости из других каналов в заданном временном окне.
        Возвращает список кандидатов-дублей (score >= score_threshold).
        """
        time_from = published_at - timedelta(hours=time_window_hours)
        time_to = published_at + timedelta(hours=time_window_hours)

        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="published_at",
                    range=models.Range(
                        gte=int(time_from.timestamp()),
                        lte=int(time_to.timestamp()),
                    ),
                ),
            ],
            must_not=[
                models.FieldCondition(
                    key="source_channel",
                    match=models.MatchValue(value=source_channel),
                ),
            ],
        )

        try:
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=query_filter,
                score_threshold=score_threshold,
                limit=limit,
                with_payload=False,
                with_vectors=False,
            )
            return hits
        except Exception as e:
            logger.error(f"Error searching for near duplicates: {e}")
            return []

    def search(self, vector: List[float], limit: int = 10, query_filter: Optional[models.Filter] = None) -> List[models.ScoredPoint]:
        """
        Выполняет поиск ближайших векторов в Qdrant, теперь с поддержкой фильтров.
        """
        try:
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=query_filter, # ИСПОЛЬЗУЕМ ФИЛЬТР
                limit=limit,
                with_payload=False,
                with_vectors=False
            )
            return hits
        except Exception as e:
            logger.error(f"Error searching in Qdrant: {e}")
            return []

# Singleton instance
vector_db_service = VectorDBService()
