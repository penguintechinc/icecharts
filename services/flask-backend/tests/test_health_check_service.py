"""Tests for health check service."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.health_check_service import HealthCheckService


@pytest.fixture
def health_service():
    """Create a health check service instance."""
    return HealthCheckService()


class TestHealthCheckService:
    """Test health check service functionality."""

    def test_check_all_returns_required_fields(self, health_service):
        """Test that check_all returns all required fields."""
        with patch("app.services.health_check_service.get_db") as mock_get_db:
            with patch(
                "app.services.health_check_service.redis.from_url"
            ) as mock_redis:
                mock_get_db.return_value.executesql.return_value = True
                mock_redis.return_value.ping.return_value = True
                mock_redis.return_value.info.return_value = {
                    "redis_version": "6.0.0",
                    "connected_clients": 1,
                    "used_memory": 1024,
                    "uptime_in_seconds": 3600,
                }

                result = health_service.check_all()

                assert "status" in result
                assert "timestamp" in result
                assert "uptime_seconds" in result
                assert "components" in result

    def test_determine_overall_status_all_healthy(self, health_service):
        """Test overall status when all components are healthy."""
        statuses = ["healthy", "healthy", "healthy", "healthy", "healthy"]
        result = HealthCheckService._determine_overall_status(statuses)
        assert result == "healthy"

    def test_determine_overall_status_one_degraded(self, health_service):
        """Test overall status when one component is degraded."""
        statuses = ["healthy", "healthy", "degraded", "healthy", "healthy"]
        result = HealthCheckService._determine_overall_status(statuses)
        assert result == "degraded"

    def test_determine_overall_status_multiple_degraded(self, health_service):
        """Test overall status when multiple components are degraded."""
        statuses = ["healthy", "degraded", "degraded", "healthy", "healthy"]
        result = HealthCheckService._determine_overall_status(statuses)
        assert result == "degraded"

    def test_determine_overall_status_one_unhealthy(self, health_service):
        """Test overall status when one component is unhealthy."""
        statuses = ["healthy", "healthy", "unhealthy", "healthy", "healthy"]
        result = HealthCheckService._determine_overall_status(statuses)
        assert result == "unhealthy"

    def test_determine_overall_status_mixed(self, health_service):
        """Test overall status with mixed component statuses."""
        statuses = ["healthy", "degraded", "unhealthy", "healthy"]
        result = HealthCheckService._determine_overall_status(statuses)
        assert result == "unhealthy"

    def test_check_database_healthy(self, health_service):
        """Test database check when database is healthy."""
        with patch("app.services.health_check_service.get_db") as mock_get_db:
            with patch("app.services.health_check_service.current_app") as mock_app:
                mock_app.config.get.side_effect = lambda key, default=None: {
                    "DB_HOST": "localhost",
                    "DB_PORT": 5432,
                    "DB_NAME": "test_db",
                }.get(key, default)

                mock_get_db.return_value.executesql.return_value = True

                result = health_service._check_database()

                assert result["status"] == "healthy"
                assert "response_time_ms" in result
                assert "details" in result

    def test_check_database_unhealthy(self, health_service):
        """Test database check when database connection fails."""
        with patch("app.services.health_check_service.get_db") as mock_get_db:
            mock_get_db.return_value.executesql.side_effect = Exception(
                "Connection failed"
            )

            result = health_service._check_database()

            assert result["status"] == "unhealthy"
            assert "error" in result

    def test_check_redis_healthy(self, health_service):
        """Test Redis check when Redis is healthy."""
        with patch("app.services.health_check_service.current_app") as mock_app:
            with patch(
                "app.services.health_check_service.redis.from_url"
            ) as mock_redis:
                mock_app.config.get.return_value = "redis://localhost:6379/0"
                mock_redis.return_value.ping.return_value = True
                mock_redis.return_value.info.return_value = {
                    "redis_version": "6.0.0",
                    "connected_clients": 5,
                    "used_memory": 1024 * 1024,
                    "uptime_in_seconds": 3600,
                }

                result = health_service._check_redis()

                assert result["status"] == "healthy"
                assert "details" in result
                assert result["details"]["version"] == "6.0.0"

    def test_check_redis_not_configured(self, health_service):
        """Test Redis check when Redis is not configured."""
        with patch("app.services.health_check_service.current_app") as mock_app:
            mock_app.config.get.return_value = None

            result = health_service._check_redis()

            assert result["status"] == "unknown"
            assert "not configured" in result["message"]

    def test_check_redis_connection_error(self, health_service):
        """Test Redis check when connection fails."""
        import redis

        with patch("app.services.health_check_service.current_app") as mock_app:
            with patch(
                "app.services.health_check_service.redis.from_url"
            ) as mock_redis:
                mock_app.config.get.return_value = "redis://localhost:6379/0"
                mock_redis.return_value.ping.side_effect = redis.ConnectionError(
                    "Connection refused"
                )

                result = health_service._check_redis()

                assert result["status"] == "unhealthy"
                assert "Cannot connect" in result["message"]

    def test_check_api_service_healthy(self, health_service):
        """Test API service check."""
        with patch("app.services.health_check_service.current_app") as mock_app:
            mock_app.config.get.side_effect = lambda key, default=None: {
                "APP_VERSION": "1.0.0",
                "ENV": "test",
                "DEBUG": False,
            }.get(key, default)

            result = health_service._check_api_service()

            assert result["status"] == "healthy"
            assert result["details"]["version"] == "1.0.0"

    def test_check_storage_no_providers(self, health_service):
        """Test storage check when no providers are configured."""
        with patch("app.services.health_check_service.get_db") as mock_get_db:
            mock_get_db.return_value.return_value.select.return_value = []

            result = health_service._check_storage()

            assert result["status"] == "unknown"
            assert "No active storage providers" in result["message"]

    def test_check_system_resources_healthy(self, health_service):
        """Test system resource check when resources are healthy."""
        with patch("app.services.health_check_service.psutil") as mock_psutil:
            # Mock virtual_memory
            mock_memory = MagicMock()
            mock_memory.percent = 50
            mock_memory.total = 8 * (1024**3)
            mock_memory.available = 4 * (1024**3)
            mock_memory.used = 4 * (1024**3)
            mock_psutil.virtual_memory.return_value = mock_memory

            # Mock disk_usage
            mock_disk = MagicMock()
            mock_disk.percent = 40
            mock_disk.total = 100 * (1024**3)
            mock_disk.used = 40 * (1024**3)
            mock_disk.free = 60 * (1024**3)
            mock_psutil.disk_usage.return_value = mock_disk

            # Mock cpu_percent
            mock_psutil.cpu_percent.return_value = 30
            mock_psutil.cpu_count.return_value = 4

            result = health_service._check_system_resources()

            assert result["status"] == "healthy"
            assert "details" in result
            assert result["details"]["cpu"]["count"] == 4
            assert result["details"]["memory"]["status"] == "healthy"
            assert result["details"]["disk"]["status"] == "healthy"

    def test_check_system_resources_memory_degraded(self, health_service):
        """Test system resource check when memory usage is high."""
        with patch("app.services.health_check_service.psutil") as mock_psutil:
            # Mock virtual_memory with high usage
            mock_memory = MagicMock()
            mock_memory.percent = 85
            mock_memory.total = 8 * (1024**3)
            mock_memory.available = 1 * (1024**3)
            mock_memory.used = 7 * (1024**3)
            mock_psutil.virtual_memory.return_value = mock_memory

            # Mock disk_usage
            mock_disk = MagicMock()
            mock_disk.percent = 40
            mock_disk.total = 100 * (1024**3)
            mock_disk.used = 40 * (1024**3)
            mock_disk.free = 60 * (1024**3)
            mock_psutil.disk_usage.return_value = mock_disk

            # Mock cpu_percent
            mock_psutil.cpu_percent.return_value = 30
            mock_psutil.cpu_count.return_value = 4

            result = health_service._check_system_resources()

            assert result["status"] == "degraded"
            assert result["details"]["memory"]["status"] == "degraded"

    def test_check_system_resources_disk_unhealthy(self, health_service):
        """Test system resource check when disk usage is critical."""
        with patch("app.services.health_check_service.psutil") as mock_psutil:
            # Mock virtual_memory
            mock_memory = MagicMock()
            mock_memory.percent = 50
            mock_memory.total = 8 * (1024**3)
            mock_memory.available = 4 * (1024**3)
            mock_memory.used = 4 * (1024**3)
            mock_psutil.virtual_memory.return_value = mock_memory

            # Mock disk_usage with critical usage
            mock_disk = MagicMock()
            mock_disk.percent = 97
            mock_disk.total = 100 * (1024**3)
            mock_disk.used = 97 * (1024**3)
            mock_disk.free = 3 * (1024**3)
            mock_psutil.disk_usage.return_value = mock_disk

            # Mock cpu_percent
            mock_psutil.cpu_percent.return_value = 30
            mock_psutil.cpu_count.return_value = 4

            result = health_service._check_system_resources()

            assert result["status"] == "unhealthy"
            assert result["details"]["disk"]["status"] == "unhealthy"

    def test_check_system_resources_psutil_not_available(self, health_service):
        """Test system resource check when psutil is not available."""
        with patch("app.services.health_check_service.psutil", side_effect=ImportError):
            result = health_service._check_system_resources()

            assert result["status"] == "unknown"
            assert "psutil library not installed" in result["message"]
