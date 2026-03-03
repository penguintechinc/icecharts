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

    def test_check_all_returns_required_fields(self, app, health_service):
        """Test that check_all returns all required fields."""
        with app.app_context():
            with patch.object(health_service, "_check_database") as mock_db:
                with patch.object(health_service, "_check_redis") as mock_redis:
                    with patch.object(health_service, "_check_storage") as mock_storage:
                        with patch.object(health_service, "_check_api_service") as mock_api:
                            with patch.object(
                                health_service, "_check_system_resources"
                            ) as mock_sys:
                                mock_db.return_value = {"status": "healthy"}
                                mock_redis.return_value = {"status": "healthy"}
                                mock_storage.return_value = {"status": "healthy"}
                                mock_api.return_value = {"status": "healthy"}
                                mock_sys.return_value = {"status": "healthy"}

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

    def test_check_database_healthy(self, app, health_service):
        """Test database check when database is healthy."""
        with app.app_context():
            with patch("app.models.get_db") as mock_get_db:
                mock_get_db.return_value.executesql.return_value = True

                result = health_service._check_database()

                assert result["status"] == "healthy"
                assert "response_time_ms" in result
                assert "details" in result

    def test_check_database_unhealthy(self, app, health_service):
        """Test database check when database connection fails."""
        with app.app_context():
            with patch("app.models.get_db") as mock_get_db:
                mock_get_db.return_value.executesql.side_effect = Exception(
                    "Connection failed"
                )

                result = health_service._check_database()

                assert result["status"] == "unhealthy"
                assert "error" in result

    def test_check_redis_healthy(self, app, health_service):
        """Test Redis check when Redis is healthy."""
        with app.app_context():
            app.config["REDIS_URL"] = "redis://localhost:6379/0"
            with patch(
                "app.services.health_check_service.redis"
            ) as mock_redis_module:
                mock_conn = MagicMock()
                mock_conn.ping.return_value = True
                mock_conn.info.return_value = {
                    "redis_version": "6.0.0",
                    "connected_clients": 5,
                    "used_memory": 1024 * 1024,
                    "uptime_in_seconds": 3600,
                }
                mock_redis_module.from_url.return_value = mock_conn

                result = health_service._check_redis()

                assert result["status"] == "healthy"
                assert "details" in result
                assert result["details"]["version"] == "6.0.0"

    def test_check_redis_not_configured(self, app, health_service):
        """Test Redis check when Redis is not configured."""
        with app.app_context():
            app.config["REDIS_URL"] = None

            result = health_service._check_redis()

            assert result["status"] == "unknown"
            assert "not configured" in result["message"].lower()

    def test_check_redis_connection_error(self, app, health_service):
        """Test Redis check when connection fails."""
        import redis as redis_lib

        with app.app_context():
            app.config["REDIS_URL"] = "redis://localhost:6379/0"
            with patch(
                "app.services.health_check_service.redis"
            ) as mock_redis_module:
                mock_redis_module.from_url.return_value.ping.side_effect = (
                    redis_lib.ConnectionError("Connection refused")
                )
                mock_redis_module.ConnectionError = redis_lib.ConnectionError

                result = health_service._check_redis()

                assert result["status"] == "unhealthy"
                assert "Cannot connect" in result["message"]

    def test_check_api_service_healthy(self, app, health_service):
        """Test API service check."""
        with app.app_context():
            app.config["APP_VERSION"] = "1.0.0"
            app.config["ENV"] = "test"
            app.config["DEBUG"] = False

            result = health_service._check_api_service()

            assert result["status"] == "healthy"
            assert result["details"]["version"] == "1.0.0"

    def test_check_storage_no_providers(self, app, health_service):
        """Test storage check when no providers are configured."""
        with app.app_context():
            with patch("app.models.get_db") as mock_get_db:
                mock_db = MagicMock()
                # db(expression) returns a Set; .select() returns Rows
                mock_set = MagicMock()
                mock_set.select.return_value = []
                mock_db.return_value = mock_set
                # storage_providers table attribute
                mock_db.storage_providers = MagicMock()
                mock_db.storage_providers.is_active = True
                mock_db.storage_providers.is_system_default = True
                mock_get_db.return_value = mock_db

                result = health_service._check_storage()

                assert result["status"] == "unknown"
                assert "No active storage providers" in result["message"]

    def test_check_system_resources_healthy(self, health_service):
        """Test system resource check when resources are healthy."""
        with patch("psutil.virtual_memory") as mock_vm, \
             patch("psutil.disk_usage") as mock_du, \
             patch("psutil.cpu_percent") as mock_cpu, \
             patch("psutil.cpu_count") as mock_count:
            mock_memory = MagicMock()
            mock_memory.percent = 50
            mock_memory.total = 8 * (1024**3)
            mock_memory.available = 4 * (1024**3)
            mock_memory.used = 4 * (1024**3)
            mock_vm.return_value = mock_memory

            mock_disk = MagicMock()
            mock_disk.percent = 40
            mock_disk.total = 100 * (1024**3)
            mock_disk.used = 40 * (1024**3)
            mock_disk.free = 60 * (1024**3)
            mock_du.return_value = mock_disk

            mock_cpu.return_value = 30
            mock_count.return_value = 4

            result = health_service._check_system_resources()

            assert result["status"] == "healthy"
            assert "details" in result
            assert result["details"]["cpu"]["count"] == 4
            assert result["details"]["memory"]["status"] == "healthy"
            assert result["details"]["disk"]["status"] == "healthy"

    def test_check_system_resources_memory_degraded(self, health_service):
        """Test system resource check when memory usage is high."""
        with patch("psutil.virtual_memory") as mock_vm, \
             patch("psutil.disk_usage") as mock_du, \
             patch("psutil.cpu_percent") as mock_cpu, \
             patch("psutil.cpu_count") as mock_count:
            mock_memory = MagicMock()
            mock_memory.percent = 85
            mock_memory.total = 8 * (1024**3)
            mock_memory.available = 1 * (1024**3)
            mock_memory.used = 7 * (1024**3)
            mock_vm.return_value = mock_memory

            mock_disk = MagicMock()
            mock_disk.percent = 40
            mock_disk.total = 100 * (1024**3)
            mock_disk.used = 40 * (1024**3)
            mock_disk.free = 60 * (1024**3)
            mock_du.return_value = mock_disk

            mock_cpu.return_value = 30
            mock_count.return_value = 4

            result = health_service._check_system_resources()

            assert result["status"] == "degraded"
            assert result["details"]["memory"]["status"] == "degraded"

    def test_check_system_resources_disk_unhealthy(self, health_service):
        """Test system resource check when disk usage is critical."""
        with patch("psutil.virtual_memory") as mock_vm, \
             patch("psutil.disk_usage") as mock_du, \
             patch("psutil.cpu_percent") as mock_cpu, \
             patch("psutil.cpu_count") as mock_count:
            mock_memory = MagicMock()
            mock_memory.percent = 50
            mock_memory.total = 8 * (1024**3)
            mock_memory.available = 4 * (1024**3)
            mock_memory.used = 4 * (1024**3)
            mock_vm.return_value = mock_memory

            mock_disk = MagicMock()
            mock_disk.percent = 97
            mock_disk.total = 100 * (1024**3)
            mock_disk.used = 97 * (1024**3)
            mock_disk.free = 3 * (1024**3)
            mock_du.return_value = mock_disk

            mock_cpu.return_value = 30
            mock_count.return_value = 4

            result = health_service._check_system_resources()

            assert result["status"] == "unhealthy"
            assert result["details"]["disk"]["status"] == "unhealthy"

    def test_check_system_resources_psutil_not_available(self, health_service):
        """Test system resource check when psutil is not available."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "psutil":
                raise ImportError("No module named 'psutil'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = health_service._check_system_resources()

            assert result["status"] == "unknown"
            assert "psutil" in result["message"].lower()
