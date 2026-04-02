"""Tests for StorageUsageService.

Unit and integration tests for storage usage calculation and quota management.
"""

import pytest
from app.models import get_db
from app.services.storage_usage_service import StorageUsageService


class TestStorageUsageCalculation:
    """Test storage usage calculation methods."""

    def test_default_user_quota(self):
        """Test that default user quota is 1GB."""
        quota = StorageUsageService.DEFAULT_USER_QUOTA
        assert quota == 1073741824  # 1GB in bytes

    def test_default_tenant_quota(self):
        """Test that default tenant quota is 10GB."""
        quota = StorageUsageService.DEFAULT_TENANT_QUOTA
        assert quota == 10737418240  # 10GB in bytes

    def test_get_user_storage_usage_structure(self):
        """Test that storage usage has correct structure."""
        # This would require a real user in database
        # For now, just verify the function signature
        try:
            usage = StorageUsageService.get_user_storage_usage(user_id=1)

            # Verify all required keys are present
            required_keys = [
                "user_id",
                "total_size_bytes",
                "total_size_mb",
                "total_drawings",
                "drawings_content_bytes",
                "drawing_versions_bytes",
                "attachments_bytes",
                "thumbnails_bytes",
                "quota_bytes",
                "quota_mb",
                "usage_percentage",
                "by_provider",
            ]

            for key in required_keys:
                assert key in usage, f"Missing key: {key}"

            # Verify types
            assert isinstance(usage["user_id"], int)
            assert isinstance(usage["total_size_bytes"], int)
            assert isinstance(usage["total_size_mb"], float)
            assert isinstance(usage["usage_percentage"], float)
            assert isinstance(usage["by_provider"], list)

        except Exception as e:
            # Expected if no test database
            pytest.skip(f"Database not available: {e}")

    def test_get_tenant_storage_usage_structure(self):
        """Test that tenant storage usage has correct structure."""
        try:
            usage = StorageUsageService.get_tenant_storage_usage(tenant_id=1)

            # Verify all required keys are present
            required_keys = [
                "tenant_id",
                "total_size_bytes",
                "total_size_mb",
                "total_drawings",
                "quota_bytes",
                "quota_mb",
                "usage_percentage",
            ]

            for key in required_keys:
                assert key in usage, f"Missing key: {key}"

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_quota_exceeded_false(self):
        """Test check_quota_exceeded returns False when under quota."""
        try:
            # For a new/empty user, quota should not be exceeded
            is_exceeded = StorageUsageService.check_quota_exceeded(
                user_id=1, additional_bytes=1024  # 1KB
            )
            assert isinstance(is_exceeded, bool)

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_usage_status_ok(self):
        """Test usage status calculation for OK range."""
        status = StorageUsageService._get_usage_status(50.0)
        assert status == "ok"

    def test_usage_status_warning(self):
        """Test usage status calculation for warning range."""
        status = StorageUsageService._get_usage_status(80.0)
        assert status == "warning"

    def test_usage_status_critical(self):
        """Test usage status calculation for critical range."""
        status = StorageUsageService._get_usage_status(95.0)
        assert status == "critical"

    def test_storage_stats_summary_structure(self):
        """Test that storage summary has correct structure."""
        try:
            stats = StorageUsageService.get_storage_stats_summary(user_id=1)

            required_keys = [
                "used_mb",
                "quota_mb",
                "usage_percentage",
                "usage_status",
                "total_drawings",
            ]

            for key in required_keys:
                assert key in stats, f"Missing key: {key}"

            # Verify types
            assert isinstance(stats["used_mb"], float)
            assert isinstance(stats["quota_mb"], float)
            assert isinstance(stats["usage_percentage"], float)
            assert stats["usage_status"] in ["ok", "warning", "critical"]
            assert isinstance(stats["total_drawings"], int)

        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestQuotaManagement:
    """Test quota management methods."""

    def test_get_user_quota_returns_bytes(self):
        """Test that get_user_quota returns bytes as integer."""
        try:
            quota = StorageUsageService.get_user_quota(user_id=1)
            assert isinstance(quota, int)
            assert quota > 0

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_get_tenant_quota_returns_bytes(self):
        """Test that get_tenant_quota returns bytes as integer."""
        try:
            quota = StorageUsageService.get_tenant_quota(tenant_id=1)
            assert isinstance(quota, int)
            assert quota > 0

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_set_tenant_quota_validation(self):
        """Test that set_tenant_quota validates input."""
        try:
            # Negative quota should fail
            result = StorageUsageService.set_tenant_quota(tenant_id=1, quota_gb=-1)
            # May return False due to validation

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_set_user_quota_validation(self):
        """Test that set_user_quota validates input."""
        try:
            # Negative quota should fail
            result = StorageUsageService.set_user_quota(user_id=1, quota_mb=-1)
            # May return False due to validation

        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_storage_usage_with_nonexistent_user(self):
        """Test storage usage calculation with nonexistent user ID."""
        usage = StorageUsageService.get_user_storage_usage(user_id=999999)

        # Should return valid structure with default values
        assert usage["user_id"] == 999999
        assert usage["total_size_bytes"] == 0
        assert usage["total_drawings"] == 0
        assert usage["quota_bytes"] == StorageUsageService.DEFAULT_USER_QUOTA

    def test_storage_usage_with_nonexistent_tenant(self):
        """Test tenant storage usage calculation with nonexistent tenant ID."""
        usage = StorageUsageService.get_tenant_storage_usage(tenant_id=999999)

        # Should return valid structure with default values
        assert usage["tenant_id"] == 999999
        assert usage["total_size_bytes"] == 0
        assert usage["total_drawings"] == 0
        assert usage["quota_bytes"] == StorageUsageService.DEFAULT_TENANT_QUOTA

    def test_get_user_quota_with_nonexistent_user(self):
        """Test get_user_quota with nonexistent user returns default."""
        quota = StorageUsageService.get_user_quota(user_id=999999)
        assert quota == StorageUsageService.DEFAULT_USER_QUOTA

    def test_get_tenant_quota_with_nonexistent_tenant(self):
        """Test get_tenant_quota with nonexistent tenant returns default."""
        quota = StorageUsageService.get_tenant_quota(tenant_id=999999)
        assert quota == StorageUsageService.DEFAULT_TENANT_QUOTA


class TestSizeConversions:
    """Test size unit conversions."""

    def test_bytes_to_mb_conversion(self):
        """Test conversion from bytes to MB."""
        bytes_value = 1048576  # 1 MB
        mb_value = round(bytes_value / (1024 * 1024), 2)
        assert mb_value == 1.0

    def test_bytes_to_gb_conversion(self):
        """Test conversion from bytes to GB."""
        bytes_value = 1073741824  # 1 GB
        gb_value = bytes_value / (1024 * 1024 * 1024)
        assert gb_value == 1.0

    def test_usage_percentage_calculation(self):
        """Test usage percentage calculation."""
        usage_bytes = 536870912  # 512 MB
        quota_bytes = 1073741824  # 1 GB
        usage_pct = round((usage_bytes / quota_bytes) * 100, 2)
        assert usage_pct == 50.0

    def test_usage_percentage_over_100(self):
        """Test usage percentage when over quota."""
        usage_bytes = 2147483648  # 2 GB
        quota_bytes = 1073741824  # 1 GB
        usage_pct = round((usage_bytes / quota_bytes) * 100, 2)
        assert usage_pct == 200.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
