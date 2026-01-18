import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.config import settings


@pytest.fixture
def auth_headers():
    """Стандартные заголовки аутентификации для тестов."""
    return {
        "x-api-token": settings.api_secret_token,
        "x-user-id": "test-user-123",
    }


@pytest.fixture
def mock_redis():
    """Мок Redis-клиента."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.ping = AsyncMock()
    redis.scan_iter = MagicMock(return_value=iter([]))
    return redis


@pytest.fixture
def mock_db_session():
    """Мок асинхронной сессии БД."""
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
async def client(mock_redis):
    """HTTP-клиент для тестирования API.

    Патчим подключения к БД и Redis, чтобы тесты не зависели от внешних сервисов.
    """
    with patch("app.database.redis_client", mock_redis), \
         patch("app.database.check_db_connection", AsyncMock(return_value=True)), \
         patch("app.database.check_redis_connection", AsyncMock(return_value=True)), \
         patch("app.database.init_db", AsyncMock()):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
