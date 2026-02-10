import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from typing import List, Optional

from app.ai.schemas import NewsCategory
from app.api.deps import get_authenticated_user, limiter
from app.api.endpoints.agent import ChatResponse, NewsSourceResponse
from app.services.agent_service import agent_service
from app.services.news_service import NewsService
from app.database import redis_client
import json

# Временная Pydantic модель для ответа, чтобы не тянуть всю модель SQLAlchemy
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class HotTopic(BaseModel):
    title: str
    news_count: int
    news_ids: List[int]


class NewsCard(BaseModel):
    id: int
    title: str = Field(..., description="Заголовок/краткое содержание новости")
    source_channel: str
    published_at: datetime
    tg_link: str
    importance_score: Optional[float] = None

    class Config:
        orm_mode = True  # Позволяет Pydantic работать с объектами SQLAlchemy


@router.get(
    "/thematic",
    response_model=List[NewsCard],
    summary="Получить новости по тематике"
)
@limiter.limit("30/minute")
async def get_thematic_dashboard(
        request: Request,
        category: NewsCategory = Query(..., description="Категория для фильтрации"),
        limit: int = Query(20, ge=5, le=50),
        user_info=Depends(get_authenticated_user)
):
    """
    Возвращает список последних новостей для указанной тематической категории.
    """
    try:
        news_service = NewsService()
        news_items = await news_service.get_news_by_category(category=category.value, limit=limit)

        # Преобразуем summary в title для карточки
        response_items = []
        for item in news_items:
            response_items.append(NewsCard(
                id=item.id,
                title=item.summary or item.original_text[:120],
                source_channel=item.source_channel,
                published_at=item.published_at,
                tg_link=item.tg_link,
                importance_score=item.importance_score
            ))

        return response_items
    except Exception as e:
        logger.error(f"Error in thematic dashboard for category {category}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve thematic news.")


@router.get(
    "/daily-briefing",
    response_model=ChatResponse,
    summary="Сводка 'Главное за день'"
)
@limiter.limit("10/minute")
async def get_daily_briefing(request: Request, user_info=Depends(get_authenticated_user)):
    """
    Генерирует персонализированную сводку ключевых новостей за последние 24 часа.
    """
    try:
        user_id = user_info.get("user_id")
        fixed_query = "Сделай краткую и структурированную сводку 3-5 самых важных новостей за последние 24 часа. Сгруппируй их по темам."

        answer, sources = await agent_service.process_query(
            query=fixed_query,
            user_id=user_id,
            override_filters={"time_range_days": 1, "importance_gte": 0.7}
        )

        response_sources = [NewsSourceResponse(**vars(s)) for s in sources]
        return ChatResponse(answer=answer, sources=response_sources)
    except Exception as e:
        logger.error(f"Error in daily briefing dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate daily briefing.")

@router.get(
    "/hot-topics",
    response_model=List[HotTopic],
    summary="Дашборд 'Горячие темы'"
)
@limiter.limit("30/minute")
async def get_hot_topics(request: Request, user_info=Depends(get_authenticated_user)):
    """
    Возвращает список самых обсуждаемых тем, рассчитанный в фоновом режиме.
    """
    try:
        cached_data = await redis_client.get("dashboard:hot_topics")
        if cached_data:
            return json.loads(cached_data)
        return []
    except Exception as e:
        logger.error(f"Error retrieving hot topics from cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve hot topics.")
