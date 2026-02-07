"""Тесты API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_root(client):
    """Корневой endpoint должен возвращать информацию о сервисе."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "AI News Manager" in data["message"]


@pytest.mark.asyncio
async def test_health_check(client):
    """Health check должен проходить при рабочих сервисах."""
    with patch("app.main.check_db_connection", AsyncMock(return_value=True)), \
         patch("app.main.check_redis_connection", AsyncMock(return_value=True)):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_required(client):
    """Запросы без токена должны возвращать 422/401."""
    response = await client.get("/api/test")
    # FastAPI вернет 422 если обязательные заголовки отсутствуют
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_auth_invalid_token(client):
    """Неверный токен должен возвращать 401."""
    headers = {
        "x-api-token": "wrong-token",
        "x-user-id": "user-1",
    }
    response = await client.get("/api/test", headers=headers)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_valid_token(client, auth_headers):
    """Валидный токен должен пропускать запрос."""
    response = await client.get("/api/test", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"] ["user_id"] == "test-user-123"


@pytest.mark.asyncio
async def test_chat_empty_query(client, auth_headers):
    """Пустой запрос в чат должен возвращать ошибку."""
    response = await client.post("/api/agent/chat", json={"query": ""}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_success(client, auth_headers):
    """Успешный запрос в чат агента."""
    mock_sources = [
        MagicMock(
            id=1, tg_link="https://t.me/test/1", summary="Test summary",
            source_channel="test_channel", published_at="2026-01-01T00:00:00"
        )
    ]

    with patch("app.api.endpoints.agent.agent_service") as mock_agent:
        mock_agent.process_query = AsyncMock(return_value=("Test answer", mock_sources))
        response = await client.post(
            "/api/agent/chat",
            json={"query": "Что нового на рынке?"},
            headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Test answer"
    assert len(data["sources"]) == 1


@pytest.mark.asyncio
async def test_hot_topics_empty(client, auth_headers, mock_redis):
    """Hot topics при пустом кеше должен возвращать пустой список."""
    mock_redis.get.return_value = None
    response = await client.get("/api/dashboards/hot-topics", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


