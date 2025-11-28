import logging
import json
import asyncio
import hdbscan
import numpy as np
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app
from app.services.vector_db_service import VectorDBService, models
from app.services.news_service import NewsService
from app.services.llm_service import llm_service
from app.database import redis_client

logger = logging.getLogger(__name__)


def _get_event_loop():
    """Получаем или создаём event loop для синхронных Celery-тасков."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def _run_async(coro):
    """Обёртка для запуска async кода из синхронного Celery таска."""
    loop = _get_event_loop()
    return loop.run_until_complete(coro)


def _calculate_hdbscan_params(num_points: int) -> dict:
    """Динамически подбираем параметры HDBSCAN в зависимости от размера выборки."""
    if num_points < 30:
        return {"min_cluster_size": 3, "min_samples": 2, "cluster_selection_method": "leaf"}
    elif num_points < 100:
        return {"min_cluster_size": 4, "min_samples": 2, "cluster_selection_method": "leaf"}
    elif num_points < 300:
        return {"min_cluster_size": 5, "min_samples": 3, "cluster_selection_method": "eom"}
    else:
        return {"min_cluster_size": 8, "min_samples": 3, "cluster_selection_method": "eom"}


async def _generate_topic_title(news_items) -> str:
    """Генерация заголовка темы через LLM."""
    texts = []
    for item in news_items:
        text = item.summary if item.summary else item.original_text[:300]
        texts.append(text)
    context = "\n---\n".join(texts)

    prompt = (
        "Придумай короткий заголовок (3-5 слов) для этой группы новостей. "
        "Только заголовок, без кавычек и пояснений.\n\n"
        f"{context}"
    )

    try:
        response = await llm_service.client.complete(
            model='google/gemini-2.5-flash-lite',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=30,
            temperature=0.3
        )
        title = response["choices"][0]["message"]["content"].strip().strip('"').strip("«»")
        return title
    except Exception as e:
        logger.warning(f"Failed to generate topic title: {e}")
        return "Без названия"


@celery_app.task(name="app.tasks.dashboards.calculate_hot_topics")
def calculate_hot_topics():
    """
    Анализирует векторы новостей за последние 24 часа, кластеризует их
    и определяет "горячие темы", сохраняя результат в Redis.
    """
    logger.info("Starting hot topics calculation...")
    try:
        vector_db = VectorDBService()
        news_service = NewsService()

        # 1. Получаем все векторы за последние 24 часа
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        all_points, _ = vector_db.client.scroll(
            collection_name=vector_db.collection_name,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(
                    key="published_at",
                    range=models.Range(gte=int(start_date.timestamp()))
                )
            ]),
            limit=10000,
            with_payload=True,
            with_vectors=True
        )

        num_points = len(all_points)
        logger.info(f"Fetched {num_points} vectors for clustering.")

        if num_points < 10:
            logger.info(f"Only {num_points} news items — too few for clustering. Skipping.")
            return

        vectors = np.array([point.vector for point in all_points])
        point_ids = [point.id for point in all_points]

        # 2. Нормализация и кластеризация
        from sklearn.preprocessing import normalize
        vectors_normalized = normalize(vectors, norm='l2')

        params = _calculate_hdbscan_params(num_points)
        logger.info(f"HDBSCAN params for {num_points} points: {params}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=params["min_cluster_size"],
            min_samples=params["min_samples"],
            metric='euclidean',
            cluster_selection_method=params["cluster_selection_method"]
        )
        cluster_labels = clusterer.fit_predict(vectors_normalized)

        # 3. Отбираем топ кластеры (без шума -1)
        label_counts = Counter(cluster_labels)
        top_clusters = [
            label for label, count in label_counts.most_common(6)
            if label != -1
        ][:5]

        noise_count = label_counts.get(-1, 0)
        logger.info(
            f"Clustering result: {len(top_clusters)} clusters found, "
            f"{noise_count}/{num_points} points classified as noise."
        )

        if not top_clusters:
            logger.info("No clusters found. All points classified as noise.")
            return

        # 4. Генерируем заголовки для каждого кластера
        hot_topics = []
        for cluster_id in top_clusters:
            cluster_point_ids = [
                point_ids[i] for i, label in enumerate(cluster_labels)
                if label == cluster_id
            ]

            sample_ids = cluster_point_ids[:10]
            news_items = _run_async(news_service.get_news_by_ids(sample_ids))

            if not news_items:
                continue

            title = _run_async(_generate_topic_title(news_items))

            hot_topics.append({
                "title": title,
                "news_count": len(cluster_point_ids),
                "news_ids": cluster_point_ids[:5]
            })

        # 5. Сохраняем в Redis
        if hot_topics:
            _run_async(
                redis_client.set(
                    "dashboard:hot_topics",
                    json.dumps(hot_topics, ensure_ascii=False),
                    ex=7200
                )
            )
            logger.info(f"Saved {len(hot_topics)} hot topics to Redis.")
        else:
            logger.info("No hot topics to save.")

    except Exception as e:
        logger.error(f"Error in calculate_hot_topics: {e}", exc_info=True)
