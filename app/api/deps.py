from fastapi import HTTPException, Header, Depends
from app.config import settings
import logging

logger = logging.getLogger(__name__)

async def verify_api_token(x_api_token: str = Header(...)):
    """Проверка API токена для коммуникации с основным сайтом"""
    if x_api_token != settings.api_secret_token:
        logger.warning(f"Invalid API token attempt: {x_api_token}")
        raise HTTPException(status_code=401, detail="Invalid API token")
    return True

async def get_user_from_header(
    x_user_id: int = Header(...),
    x_user_data: str = Header(None),  # JSON string с доп. данными о пользователе
    _: bool = Depends(verify_api_token)
):
    """Извлечение информации о пользователе из headers"""
    try:
        user_info = {
            "user_id": x_user_id,
            "user_data": x_user_data
        }
        logger.info(f"Authenticated user: {x_user_id}")
        return user_info
    except Exception as e:
        logger.error(f"Error parsing user headers: {e}")
        raise HTTPException(status_code=400, detail="Invalid user headers")
