from fastapi import APIRouter, Depends
from app.schemas.agent_settings import AgentSettingsSchema
from app.services.agent_settings_service import agent_settings_service
from app.api.deps import get_user_from_header # Предполагаем, что он возвращает user_id

router = APIRouter()

@router.get("/settings", response_model=AgentSettingsSchema, summary="Получить настройки агента")
async def get_agent_settings(user_info=Depends(get_user_from_header)):
    user_id = user_info.get("user_id") # Адаптируй под свою структуру user_info
    return await agent_settings_service.get_settings(user_id)

@router.put("/settings", response_model=AgentSettingsSchema, summary="Обновить настройки агента")
async def update_agent_settings(
    settings: AgentSettingsSchema,
    user_info=Depends(get_user_from_header)
):
    user_id = user_info.get("user_id")
    return await agent_settings_service.update_settings(user_id, settings)
