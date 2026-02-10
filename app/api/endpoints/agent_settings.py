import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.agent_settings import AgentSettingsSchema
from app.services.agent_settings_service import agent_settings_service
from app.api.deps import get_authenticated_user, limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings", response_model=AgentSettingsSchema, summary="Получить настройки агента")
@limiter.limit("30/minute")
async def get_agent_settings(request: Request, user_info=Depends(get_authenticated_user)):
    user_id = user_info.get("user_id")
    try:
        return await agent_settings_service.get_settings(user_id)
    except Exception as e:
        logger.error(f"Error getting settings for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve agent settings.")


@router.put("/settings", response_model=AgentSettingsSchema, summary="Обновить настройки агента")
@limiter.limit("10/minute")
async def update_agent_settings(
    settings: AgentSettingsSchema,
    request: Request,
    user_info=Depends(get_authenticated_user)
):
    user_id = user_info.get("user_id")
    try:
        return await agent_settings_service.update_settings(user_id, settings)
    except Exception as e:
        logger.error(f"Error updating settings for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update agent settings.")
