import json
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta, timezone

# Qdrant импорт для создания фильтров
from qdrant_client.http import models as qdrant_models

from app.services.vector_db_service import vector_db_service
from app.services.embedding_service import embedding_service
from app.services.reranker_service import reranker_service
from app.services.news_service import NewsService
from app.models.news import NewsPost
from app.services.llm_service import llm_service
from app.ai.models import model_selector, TaskType, ComplexityLevel
from app.ai.schemas import StructuredQuerySchema
from app.services.agent_settings_service import agent_settings_service
from app.services.cache_service import cache_service
from app.schemas.agent_settings import AgentSettingsSchema



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
        self.reranker = reranker_service
        self.llm_service = llm_service
        self.model_selector = model_selector
        self.search_limit = 50
        self.rerank_top_k = 15  # Сколько оставляем после reranking
        self.context_news_count = 10
        self.final_sources_count = 5
        self.settings_service = agent_settings_service
        self.cache = cache_service
        self.cache_ttl = 300  # 5 минут для ответов агента

    async def _search_relevant_news(self, structured_query: StructuredQuerySchema, settings: AgentSettingsSchema, override_filters: Optional[dict] = None) -> List[NewsPost]:
        """
        Выполняет "умный" гибридный поиск в Qdrant.
        """
        # 1. Векторизуем очищенный запрос от LLM
        query_vector = self.embedding.get_embedding(f"query: {structured_query.search_query}")

        final_filter = None
        if override_filters:
            # Если переданы переопределяющие фильтры, используем только их
            logger.info(f"Using override filters for search: {override_filters}")
            qdrant_filter_conditions = []
            if "time_range_days" in override_filters:
                start_date = datetime.now(timezone.utc) - timedelta(days=override_filters["time_range_days"])
                qdrant_filter_conditions.append(
                    qdrant_models.FieldCondition(key="published_at", range=qdrant_models.Range(gte=int(start_date.timestamp())))
                )
            if "importance_gte" in override_filters:
                 qdrant_filter_conditions.append(
                    qdrant_models.FieldCondition(key="importance_score", range=qdrant_models.Range(gte=override_filters["importance_gte"]))
                )
            final_filter = qdrant_models.Filter(must=qdrant_filter_conditions)
        else:
            # 2. Собираем единый, корректный фильтр для Qdrant
            qdrant_filter_conditions = []

            # Шаг 2.1: Объединяем категории из запроса и интересов пользователя
            final_categories = set()
            if structured_query.filter_categories:
                # Используем .value, если filter_categories содержит Enum-объекты
                final_categories.update([cat.value for cat in structured_query.filter_categories])
            if settings.focus_interests:
                final_categories.update(settings.focus_interests)

            if final_categories:
                qdrant_filter_conditions.append(
                    qdrant_models.FieldCondition(
                        key="category",
                        match=qdrant_models.MatchAny(any=list(final_categories))
                    )
                )

            # Шаг 2.2: Определяем временной диапазон. Настройки пользователя в приоритете.
            time_days = settings.historical_context_days if settings else structured_query.time_range_days

            start_date = datetime.now(timezone.utc) - timedelta(days=time_days)
            qdrant_filter_conditions.append(
                qdrant_models.FieldCondition(
                    key="published_at",
                    range=qdrant_models.Range(gte=int(start_date.timestamp()))
                )
            )

            final_filter = qdrant_models.Filter(must=qdrant_filter_conditions) if qdrant_filter_conditions else None

        # 3. Выполняем поиск
        search_results = self.vector_db.search(vector=query_vector, limit=self.search_limit, query_filter=final_filter)

        if not search_results:
            logger.warning("No relevant news found in vector database with the given filter.")
            return []

        news_ids = [result.id for result in search_results]
        logger.info(f"Found {len(news_ids)} candidate news items in Qdrant using hybrid search.")

        # 4. Получаем полные данные из PostgreSQL
        return await self.news_service.get_news_by_ids(news_ids)

    def _check_relevance(self, query: str, news_items: List[NewsPost]) -> bool:
        """
        Relevance gate: проверяем, есть ли среди найденных новостей
        достаточно релевантные для формирования ответа.
        Используем reranker scores — если лучший результат ниже порога, данных недостаточно.
        """
        if not news_items:
            return False

        try:
            top_docs = [
                item.summary or item.original_text[:500]
                for item in news_items[:5]
            ]
            ranked = self.reranker.rerank(query, top_docs, top_k=3)

            if not ranked:
                return False

            best_score = ranked[0][1]
            logger.info(f"Relevance gate: best reranker score = {best_score:.4f}")

            # Порог подобран эмпирически для ms-marco cross-encoder
            # Ниже -2.0 — контент совсем не по теме
            return best_score > -2.0

        except Exception as e:
            logger.warning(f"Relevance gate check failed: {e}")
            return True  # При ошибке пропускаем — лучше ответить, чем промолчать

    def _rerank_news(self, query: str, news_items: List[NewsPost]) -> List[NewsPost]:
        """Переранжирование новостей cross-encoder-ом для более точной релевантности."""
        if len(news_items) <= self.context_news_count:
            return news_items

        try:
            documents = [
                item.summary or item.original_text[:500]
                for item in news_items
            ]
            ranked = self.reranker.rerank(query, documents, top_k=self.rerank_top_k)

            reranked_items = [news_items[idx] for idx, score in ranked]
            logger.info(f"Reranked {len(news_items)} -> {len(reranked_items)} items")
            return reranked_items
        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
            return news_items

    def _build_format_instructions(self, settings: AgentSettingsSchema) -> str:
        """Формирует инструкции по формату ответа в зависимости от стиля пользователя."""
        style = settings.information_style.value
        depth = settings.analysis_depth.value

        if style == "только факты":
            return (
                "ФОРМАТ ОТВЕТА:\n"
                "- Начни с одного предложения-вывода.\n"
                "- Далее перечисли ключевые факты маркированным списком.\n"
                "- Не добавляй рассуждения и личные оценки."
            )
        elif style == "развернутые анализы" or depth == "экспертный уровень":
            return (
                "ФОРМАТ ОТВЕТА:\n"
                "- Начни с краткого резюме (1-2 предложения).\n"
                "- Затем раскрой тему подробно, группируя информацию по смысловым блокам.\n"
                "- Покажи связи между событиями и возможные последствия.\n"
                "- Завершай кратким итогом."
            )
        else:
            # "краткие сводки" — дефолт
            return (
                "ФОРМАТ ОТВЕТА:\n"
                "- Начни с краткого резюме (1-2 предложения).\n"
                "- Далее ключевые моменты маркированным списком.\n"
                "- Будь лаконичен, не превышай 5-7 пунктов."
            )

    async def _synthesize_answer(self, query: str, news_context: List[NewsPost], settings: AgentSettingsSchema) -> str:
        """
        Генерирует связный ответ на основе найденных новостей с помощью LLM.
        """
        if not news_context:
            return "Не удалось найти достаточно информации для ответа на ваш вопрос."

        # 1. Формируем контекст из текстов новостей
        context_str = ""
        for i, news in enumerate(news_context, 1):
            context_str += f"Источник {i} (ID: {news.id}, Опубликовано: {news.published_at.strftime('%Y-%m-%d %H:%M')}):\n"
            text_to_use = news.summary if news.summary else news.original_text
            context_str += f'"{text_to_use}"\n\n'

        # 2. Выбираем модель для анализа
        model_name = self.model_selector.select_model(
            task_type=TaskType.ANALYSIS,
            complexity=ComplexityLevel.MEDIUM
        )

        # 3. Формируем промпт с инструкциями по формату
        format_instructions = self._build_format_instructions(settings)

        system_prompt = f"""Ты - AI-новостной аналитик для трейдеров по имени {settings.agent_name}.

Твои инструкции по общению с пользователем:
- Стиль подачи информации: {settings.information_style.value}.
- Тон общения: {settings.communication_tone.value}.
- Глубина анализа: {settings.analysis_depth.value}.

{format_instructions}

Твои общие правила:
- Отвечай структурированно, ясно и по делу.
- Не выдумывай информацию, которой нет в источниках.
- Если в источниках нет ответа на вопрос, честно скажи об этом.
- Не давай никаких финансовых советов или прогнозов.
- При необходимости указывай номера источников в скобках, например: (Источник 1)."""

        user_prompt = f"""Проанализируй следующие новостные источники и дай развернутый ответ на мой вопрос.

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
            max_tokens=1500,
            temperature=0.3
        )

        answer = response["choices"][0]["message"]["content"]
        logger.info(f"Synthesized answer generated successfully.")
        return answer.strip()

    def _build_cache_key(self, query: str, user_id: str, override_filters: Optional[dict]) -> str:
        """Формирует уникальный ключ кеша из параметров запроса."""
        parts = [query.strip().lower(), user_id]
        if override_filters:
            parts.append(json.dumps(override_filters, sort_keys=True))
        return "|".join(parts)

    async def process_query(self, query: str, user_id: str, override_filters: Optional[dict] = None) -> Tuple[str, List[NewsSource]]:
        """
        "умный" пайплайн обработки запроса.
        """
        # --- Проверяем кеш ---
        cache_key = self._build_cache_key(query, user_id, override_filters)
        cached = await self.cache.get("agent", cache_key)
        if cached:
            logger.info(f"Cache hit for query: {query[:50]}...")
            sources = [NewsSource(**s) for s in cached["sources"]]
            return cached["answer"], sources

        # --- Шаг 0: Получение настроек пользователя ---
        settings = await self.settings_service.get_settings(user_id)
        logger.info(f"Using settings for user {user_id}: {settings.model_dump_json(indent=2)}")

        # --- Шаг 1: Расширение запроса с учетом настроек ---
        if override_filters:
            # Для дашбордов пропускаем Query Expansion
            structured_query = StructuredQuerySchema(search_query=query, time_range_days=override_filters.get("time_range_days", 7))
        else:
            structured_query = await self.llm_service.generate_structured_query(query, settings)
        logger.info(f"Structured query generated: {structured_query.model_dump_json(indent=2)}")

        # --- Шаг 2: Гибридный поиск релевантных новостей ---
        news_items = await self._search_relevant_news(structured_query, settings, override_filters)
        if not news_items:
            return "К сожалению, по вашему запросу не удалось найти релевантных новостей за указанный период.", []

        # --- Шаг 2.5: Reranking — переранжируем cross-encoder-ом ---
        news_items = self._rerank_news(query, news_items)

        # --- Шаг 2.6: Relevance gate — проверяем достаточность данных ---
        if not override_filters and not self._check_relevance(query, news_items):
            logger.info(f"Relevance gate: insufficient data for query '{query}'")
            return (
                "По вашему запросу не удалось найти достаточно релевантной информации в новостной базе. "
                "Попробуйте переформулировать вопрос или расширить временной диапазон.",
                []
            )

        # --- Шаг 3: Синтез ответа на основе найденного контекста ---
        context_for_synthesis = news_items[:self.context_news_count]
        # ВАЖНО: передаем исходный query, чтобы LLM отвечала на вопрос пользователя, а не на переформулированный
        generated_answer = await self._synthesize_answer(query, context_for_synthesis, settings)

        # --- Шаг 4: Формирование источников для ответа ---
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

        # --- Кешируем результат ---
        await self.cache.set("agent", cache_key, {
            "answer": generated_answer,
            "sources": [vars(s) for s in sources]
        }, ttl=self.cache_ttl)

        return generated_answer, sources


# Singleton instance
agent_service = AgentService()
