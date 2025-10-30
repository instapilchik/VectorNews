import logging
import json
import hdbscan
import numpy as np
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app
from app.services.vector_db_service import VectorDBService, models
from app.services.news_service import NewsService
from app.services.llm_service import llm_service
from app.database import redis_client
import asyncio
logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.dashboards.calculate_hot_topics")
def calculate_hot_topics():
    """
    Анализирует векторы новостей за последние 24 часа, кластеризует их
    и определяет "горячие темы", сохраняя результат в Redis.
    # TODO: Никак не кластеризирует внутри дня! исправить, переделать.
    """
    logger.info("Starting 'hot topics' calculation task...")
    try:
        vector_db = VectorDBService()
        news_service = NewsService()

        # 1. Получаем все векторы за последние 24 часа
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        # Qdrant scroll API для получения большого количества точек
        all_points, _ = vector_db.client.scroll(
            collection_name=vector_db.collection_name,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="published_at", range=models.Range(gte=int(start_date.timestamp())))
            ]),
            limit=10000,  # Максимальное количество новостей для анализа
            with_payload=False,
            with_vectors=True
        )

        if len(all_points) < 20:  # Минимальное количество для кластеризации
            logger.info("Not enough news to calculate hot topics. Skipping.")
            return

        vectors = np.array([point.vector for point in all_points])
        point_ids = [point.id for point in all_points]

        # 2. Кластеризация с HDBSCAN
        from sklearn.preprocessing import normalize
        vectors_normalized = normalize(vectors, norm='l2')
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=8,  # Минимум новостей в теме
            min_samples=3,  # Более строгие требования
            metric='euclidean',  # После нормализации = cosine
            cluster_selection_method='eom'  # Лучше для varying densities
        )
        cluster_labels = clusterer.fit_predict(vectors_normalized)

        # 3. Обработка кластеров
        # Отбираем топ-3 самых больших кластера (исключая -1 - шум)
        top_clusters = [label for label, count in Counter(cluster_labels).most_common(4) if label != -1][:3]

        hot_topics = []
        for cluster_id in top_clusters:
            cluster_point_ids = [point_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]

            # 4. Получаем тексты и генерируем заголовок для темы
            news_items = asyncio.run(news_service.get_news_by_ids(cluster_point_ids[:10]))  # 10 новостей для контекста
            context = "\n".join([item.summary or item.original_text for item in news_items])

            # Используем LLM для генерации названия темы
            prompt = f"Придумай короткий, ёмкий заголовок (3-5 слов) для этой группы новостей:\n\n---\n{context}\n---"
            title_response = asyncio.run(llm_service.client.complete(
                model='google/gemini-2.5-flash-lite',
                messages=[{'role': 'user', 'content': prompt}],
                max_tokens=2000, # 20
                temperature=0.3
            ))
            title = title_response["choices"][0]["message"]["content"].strip().replace('"', '')

            hot_topics.append({"title": title, "news_count": len(cluster_point_ids),
                               "news_ids": cluster_point_ids[:5]})  # Показываем 5 новостей

        # 5. Сохраняем в Redis
        if hot_topics:
            asyncio.run(redis_client.set("dashboard:hot_topics", json.dumps(hot_topics), ex=7200))  # TTL 2 часа
            logger.info(f"Successfully calculated and saved {len(hot_topics)} hot topics.")

    except Exception as e:
        logger.error(f"Error in calculate_hot_topics task: {e}", exc_info=True)

