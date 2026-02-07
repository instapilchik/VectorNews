"""Тесты для dashboard-задач: HDBSCAN параметры и cleanup_stale_cache."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


def _sync_run(coro):
    """Синхронный запуск корутины для тестов."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestCalculateHdbscanParams:
    def test_very_small_dataset(self):
        """Менее 30 точек — минимальные параметры кластеризации."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(15)
        assert params["min_cluster_size"] == 3
        assert params["min_samples"] == 2
        assert params["cluster_selection_method"] == "leaf"

    def test_small_dataset(self):
        """30-99 точек."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(50)
        assert params["min_cluster_size"] == 4
        assert params["min_samples"] == 2
        assert params["cluster_selection_method"] == "leaf"

    def test_medium_dataset(self):
        """100-299 точек."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(200)
        assert params["min_cluster_size"] == 5
        assert params["min_samples"] == 3
        assert params["cluster_selection_method"] == "eom"

    def test_large_dataset(self):
        """300+ точек."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(500)
        assert params["min_cluster_size"] == 8
        assert params["min_samples"] == 3
        assert params["cluster_selection_method"] == "eom"

    def test_boundary_30(self):
        """Граничное значение 30 — должно попасть во вторую группу."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(30)
        assert params["min_cluster_size"] == 4

    def test_boundary_100(self):
        """Граничное значение 100 — должно попасть в третью группу."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(100)
        assert params["min_cluster_size"] == 5

    def test_boundary_300(self):
        """Граничное значение 300 — должно попасть в четвертую группу."""
        from app.tasks.dashboards import _calculate_hdbscan_params
        params = _calculate_hdbscan_params(300)
        assert params["min_cluster_size"] == 8


class TestCleanupStaleCache:
    def test_removes_keys_without_ttl(self):
        """Ключи без TTL (ttl=-1) должны быть удалены."""
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(side_effect=[
            (1, ["dashboard:old_key1", "dashboard:old_key2"]),
            (0, []),
        ])
        mock_redis.ttl = AsyncMock(return_value=-1)
        mock_redis.delete = AsyncMock()

        with patch("app.tasks.dashboards.redis_client", mock_redis), \
             patch("app.tasks.dashboards._run_async", side_effect=_sync_run):
            from app.tasks.dashboards import cleanup_stale_cache
            result = cleanup_stale_cache()

        assert result["status"] == "success"
        assert result["cleaned_keys"] == 2

    def test_skips_keys_with_ttl(self):
        """Ключи с TTL не должны удаляться."""
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(side_effect=[
            (0, ["dashboard:valid_key"]),
        ])
        mock_redis.ttl = AsyncMock(return_value=3600)
        mock_redis.delete = AsyncMock()

        with patch("app.tasks.dashboards.redis_client", mock_redis), \
             patch("app.tasks.dashboards._run_async", side_effect=_sync_run):
            from app.tasks.dashboards import cleanup_stale_cache
            result = cleanup_stale_cache()

        assert result["status"] == "success"
        assert result["cleaned_keys"] == 0
        mock_redis.delete.assert_not_called()

    def test_handles_empty_scan(self):
        """Пустой результат сканирования — ничего не удаляем."""
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(return_value=(0, []))

        with patch("app.tasks.dashboards.redis_client", mock_redis), \
             patch("app.tasks.dashboards._run_async", side_effect=_sync_run):
            from app.tasks.dashboards import cleanup_stale_cache
            result = cleanup_stale_cache()

        assert result["status"] == "success"
        assert result["cleaned_keys"] == 0

    def test_handles_redis_error(self):
        """При ошибке Redis задача не падает, а возвращает error."""
        mock_redis = AsyncMock()
        mock_redis.scan = AsyncMock(side_effect=ConnectionError("Redis down"))

        with patch("app.tasks.dashboards.redis_client", mock_redis), \
             patch("app.tasks.dashboards._run_async", side_effect=_sync_run):
            from app.tasks.dashboards import cleanup_stale_cache
            result = cleanup_stale_cache()

        assert result["status"] == "error"
