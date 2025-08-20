from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.api.deps import get_user_from_header
from app.services.agent_service import agent_service, NewsSource

router = APIRouter()

# --- Pydantic модели для API ---

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Текст запроса от пользователя")
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
    user_info=Depends(get_user_from_header) # Защищаем эндпоинт и получаем user_id
):
    """
    Основной эндпоинт для взаимодействия с ИИ-агентом.
    Принимает запрос пользователя, использует его ID для персонализации
    и возвращает сгенерированный, персонализированный ответ и источники.
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # 1. Извлекаем user_id из информации, полученной от get_user_from_header
        user_id = user_info.get("user_id")
        if not user_id:
            # Это важная проверка безопасности
            raise HTTPException(status_code=401, detail="Could not identify user from token.")

        # 2. Передаем и query, и user_id в сервис
        answer, sources = await agent_service.process_query(
            query=request.query,
            user_id=user_id
        )

        # Преобразуем внутренние объекты NewsSource в Pydantic-модели для ответа
        response_sources = [NewsSourceResponse(**vars(s)) for s in sources]

        return ChatResponse(answer=answer, sources=response_sources)

    except Exception as e:
        logging.getLogger(__name__).error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your request.")
