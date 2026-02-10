from fastapi import APIRouter, HTTPException, Depends
import logging

from app.api.deps import require_admin
from app.schemas.auth import UserResponse
from app.schemas.user import UserCreateRequest, UserUpdateRequest
from app.services.user_service import user_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users", response_model=list[UserResponse], summary="Список пользователей")
async def list_users(admin: dict = Depends(require_admin)):
    """Get all users (admin only)."""
    users = await user_service.get_users()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=201, summary="Создание пользователя")
async def create_user(body: UserCreateRequest, admin: dict = Depends(require_admin)):
    """Create a new user (admin only)."""
    existing = await user_service.get_by_username(body.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = await user_service.create_user(
        username=body.username,
        password=body.password,
        display_name=body.display_name,
        role=body.role,
    )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse, summary="Обновление пользователя")
async def update_user(user_id: int, body: UserUpdateRequest, admin: dict = Depends(require_admin)):
    """Update an existing user (admin only)."""
    user = await user_service.update_user(
        user_id=user_id,
        display_name=body.display_name,
        password=body.password,
        role=body.role,
        is_active=body.is_active,
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", summary="Деактивация пользователя")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    """Deactivate a user (admin only, soft delete)."""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated"}
