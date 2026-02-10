import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func as sa_func
from app.database import async_session
from app.models.user import User
from app.services.auth_service import hash_password

logger = logging.getLogger(__name__)


class UserService:
    async def create_user(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        role: str = "user",
    ) -> User:
        async with async_session() as session:
            user = User(
                username=username,
                display_name=display_name,
                hashed_password=hash_password(password),
                role=role,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created user: {username} (role={role})")
            return user

    async def get_by_username(self, username: str) -> Optional[User]:
        async with async_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_users(self) -> list[User]:
        async with async_session() as session:
            stmt = select(User).order_by(User.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update_user(
        self,
        user_id: int,
        display_name: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[User]:
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return None

            if display_name is not None:
                user.display_name = display_name
            if password is not None:
                user.hashed_password = hash_password(password)
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active

            await session.commit()
            await session.refresh(user)
            logger.info(f"Updated user id={user_id}")
            return user

    async def update_last_login(self, user_id: int) -> None:
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                user.last_login_at = datetime.now(timezone.utc)
                await session.commit()

    async def delete_user(self, user_id: int) -> bool:
        """Деактивация пользователя (soft delete)."""
        async with async_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.is_active = False
            await session.commit()
            logger.info(f"Deactivated user id={user_id}")
            return True


user_service = UserService()
