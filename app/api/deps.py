from fastapi import HTTPException, Header, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


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


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """JWT-based authentication. Decodes Bearer token and returns user info dict."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    from app.services.auth_service import decode_token
    from app.services.user_service import user_service

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await user_service.get_by_id(int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return {
        "user_id": str(user.id),
        "user_data": None,
        "role": user.role,
        "username": user.username,
        "display_name": user.display_name,
    }


async def require_admin(user_info: dict = Depends(get_current_user)):
    """Requires the current user to have admin role."""
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_info


async def get_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
):
    """
    Hybrid auth: tries JWT first, falls back to legacy X-API-Token + X-User-Id headers.
    Returns a user_info dict compatible with both auth methods.
    """
    # Try JWT first
    if credentials is not None:
        from app.services.auth_service import decode_token
        from app.services.user_service import user_service

        payload = decode_token(credentials.credentials)
        if payload is not None:
            user_id = payload.get("sub")
            if user_id:
                user = await user_service.get_by_id(int(user_id))
                if user and user.is_active:
                    return {
                        "user_id": str(user.id),
                        "user_data": None,
                        "role": user.role,
                        "username": user.username,
                        "display_name": user.display_name,
                    }

    # Fallback to legacy header auth
    api_token = request.headers.get("x-api-token")
    user_id = request.headers.get("x-user-id")

    if api_token and user_id:
        if api_token != settings.api_secret_token:
            raise HTTPException(status_code=401, detail="Invalid API token")
        return {
            "user_id": user_id,
            "user_data": request.headers.get("x-user-data"),
        }

    raise HTTPException(status_code=401, detail="Not authenticated")
