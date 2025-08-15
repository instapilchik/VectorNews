import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.api.deps import get_user_from_header
from app.services.agent_service import agent_service, NewsSource

router = APIRouter()

# --- Pydantic модели для API ---

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Текст запроса от пользователя")
    user_id: str # В будущем для персонализации
    chat_history: Optional[List[dict]] = Field(None, description="История предыдущего диалога")

class NewsSourceResponse(BaseModel):
    id: int
    tg_link: str
    summary: str
    source_channel: str
    published_at: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[NewsSourceResponse]


@router.post("/chat", response_model=ChatResponse, summary="Отправить сообщение ИИ-агенту")
async def handle_chat(
    request: ChatRequest,
    user=Depends(get_user_from_header) # Защищаем эндпоинт
):
    """
    Основной эндпоинт для взаимодействия с ИИ-агентом.
    Принимает запрос пользователя, находит релевантные новости и возвращает ответ-заглушку и источники.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        answer, sources = await agent_service.process_query(request.query)

        # Преобразуем внутренние объекты NewsSource в Pydantic-модели для ответа
        response_sources = [NewsSourceResponse(**vars(s)) for s in sources]

        return ChatResponse(answer=answer, sources=response_sources)

    except Exception as e:
        logging.getLogger(__name__).error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your request.")
