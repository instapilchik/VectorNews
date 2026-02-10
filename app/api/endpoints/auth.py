from fastapi import APIRouter, HTTPException, Depends
import logging

from app.api.deps import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import verify_password, create_access_token
from app.services.user_service import user_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse, summary="Авторизация пользователя")
async def login(body: LoginRequest):
    """Authenticate with username/password, returns JWT token and user info."""
    user = await user_service.get_by_username(body.username)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    token = create_access_token(user.id, user.role)
    await user_service.update_last_login(user.id)

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse, summary="Текущий пользователь")
async def get_me(user_info: dict = Depends(get_current_user)):
    """Return info about the currently authenticated user."""
    user = await user_service.get_by_id(int(user_info["user_id"]))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
