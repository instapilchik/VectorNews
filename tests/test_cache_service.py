"""Тесты CacheService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


@pytest.fixture
def cache(mock_redis):
    with patch("app.services.cache_service.redis_client", mock_redis):
        from app.services.cache_service import CacheService
        svc = CacheService()
        svc.redis = mock_redis
        return svc


@pytest.mark.asyncio
async def test_cache_miss(cache, mock_redis):
    """При отсутствии ключа возвращается None."""
    mock_redis.get.return_value = None
    result = await cache.get("test", "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_and_get(cache, mock_redis):
    """Записанное значение можно прочитать."""
    payload = {"answer": "test", "sources": []}
    mock_redis.get.return_value = json.dumps(payload)

    await cache.set("agent", "query1", payload, ttl=60)
    mock_redis.set.assert_called_once()

    result = await cache.get("agent", "query1")
    assert result == payload


@pytest.mark.asyncio
async def test_cache_invalidate(cache, mock_redis):
    """Инвалидация удаляет ключ."""
    await cache.invalidate("agent", "query1")
    mock_redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_cache_invalidate_prefix(cache, mock_redis):
    """Инвалидация по префиксу удаляет все подходящие ключи."""
    mock_redis.scan_iter = MagicMock(return_value=iter(["agent:abc", "agent:def"]))
    deleted = await cache.invalidate_prefix("agent")
    assert deleted == 2


@pytest.mark.asyncio
async def test_cache_redis_error_returns_none(cache, mock_redis):
    """При ошибке Redis get возвращает None (не падает)."""
    mock_redis.get.side_effect = ConnectionError("Redis down")
    result = await cache.get("agent", "some_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_redis_error_set_silent(cache, mock_redis):
    """При ошибке Redis set не бросает исключение."""
    mock_redis.set.side_effect = ConnectionError("Redis down")
    # Не должно поднять исключение
    await cache.set("agent", "key", {"data": 1})


def test_make_key_deterministic(cache):
    """Один и тот же ввод всегда дает один и тот же ключ."""
    k1 = cache._make_key("test", "hello world")
    k2 = cache._make_key("test", "hello world")
    assert k1 == k2


def test_make_key_different_inputs(cache):
    """Разные вводы дают разные ключи."""
    k1 = cache._make_key("test", "input1")
    k2 = cache._make_key("test", "input2")
    assert k1 != k2
