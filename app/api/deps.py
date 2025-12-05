from fastapi import HTTPException, Header, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def _rate_limit_key(request: Request) -> str:
    """Ключ для rate limiting: X-User-Id если есть, иначе IP."""
    user_id = request.headers.get("x-user-id")
    if user_id:
        return user_id
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)


async def verify_api_token(x_api_token: str = Header(...)):
    """Проверка API токена для коммуникации с основным сайтом"""
    if x_api_token != settings.api_secret_token:
        logger.warning(f"Invalid API token attempt")
        raise HTTPException(status_code=401, detail="Invalid API token")
    return True


async def get_user_from_header(
    x_user_id: str = Header(...),
    x_user_data: str = Header(None),
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
