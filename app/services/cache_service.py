import hashlib
import json
import logging
from typing import Optional, Any

from app.database import redis_client

logger = logging.getLogger(__name__)

# TTL по умолчанию — 10 минут
DEFAULT_TTL = 600


class CacheService:
    """
    Сервис кеширования на базе Redis.
    Используется для кеширования ответов агента и дашбордов,
    чтобы не гонять LLM и reranker на повторных запросах.
    """

    def __init__(self):
        self.redis = redis_client

    def _make_key(self, prefix: str, raw_key: str) -> str:
        """Генерирует стабильный ключ из произвольной строки."""
        digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{digest}"

    async def get(self, prefix: str, raw_key: str) -> Optional[Any]:
        """Получить закешированное значение. Возвращает None при промахе."""
        key = self._make_key(prefix, raw_key)
        try:
            data = await self.redis.get(key)
            if data is not None:
                logger.debug(f"Cache hit for {key}")
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None

    async def set(self, prefix: str, raw_key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        """Записать значение в кеш с TTL (в секундах)."""
        key = self._make_key(prefix, raw_key)
        try:
            await self.redis.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
            logger.debug(f"Cache set for {key}, ttl={ttl}s")
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")

    async def invalidate(self, prefix: str, raw_key: str) -> None:
        """Удалить конкретный ключ из кеша."""
        key = self._make_key(prefix, raw_key)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Cache invalidate error for {key}: {e}")

    async def invalidate_prefix(self, prefix: str) -> int:
        """Удалить все ключи с данным префиксом. Возвращает количество удалённых."""
        pattern = f"{prefix}:*"
        deleted = 0
        try:
            async for key in self.redis.scan_iter(match=pattern, count=100):
                await self.redis.delete(key)
                deleted += 1
            if deleted:
                logger.info(f"Invalidated {deleted} keys with prefix '{prefix}'")
        except Exception as e:
            logger.warning(f"Cache invalidate_prefix error for {pattern}: {e}")
        return deleted


cache_service = CacheService()
