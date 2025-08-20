
import logging
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.database import async_session
from app.models.agent_settings import AgentSettings
from app.schemas.agent_settings import AgentSettingsSchema

logger = logging.getLogger(__name__)


class AgentSettingsService:
    async def get_settings(self, user_id: str) -> AgentSettingsSchema:
        """Получает настройки пользователя или возвращает дефолтные."""
        async with async_session() as session:
            stmt = select(AgentSettings).where(AgentSettings.user_id == user_id)
            result = await session.execute(stmt)
            settings_model = result.scalar_one_or_none()

            if settings_model:
                return AgentSettingsSchema(**settings_model.settings)

            # Если настроек нет, возвращаем дефолтные
            return AgentSettingsSchema()

    async def update_settings(self, user_id: str, settings: AgentSettingsSchema) -> AgentSettingsSchema:
        """Обновляет или создает настройки для пользователя (Upsert)."""
        async with async_session() as session:
            stmt = insert(AgentSettings).values(
                user_id=user_id,
                settings=settings.model_dump()
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id'],
                set_={'settings': stmt.excluded.settings}
            )
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Updated settings for user_id: {user_id}")
            return settings


agent_settings_service = AgentSettingsService()