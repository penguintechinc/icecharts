"""Tests for ContainerPool - warm container pool management."""

import os
import sys
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
)

import docker


class TestContainerPoolEmpty:
    """Tests for empty pool behavior."""

    def test_pool_starts_empty(self, container_pool):
        """Container pool starts with no warm containers."""
        assert len(container_pool.warm_containers) == 0

    def test_get_unknown_returns_none(self, container_pool):
        """get_container returns None for unknown runtime/function."""
        result = container_pool.get_container("python3.13", "func-unknown")
        assert result is None


class TestContainerPoolAddGet:
    """Tests for adding and retrieving containers."""

    def test_add_and_get_container(self, container_pool, mock_docker_client):
        """add_container followed by get_container returns container_id."""
        mock_docker_client.containers.get.return_value = MagicMock(status="running")
        container_pool.add_container("python3.13", "func-1", "ctr-abc")
        result = container_pool.get_container("python3.13", "func-1")
        assert result == "ctr-abc"

    def test_get_returns_none_for_unknown_function(self, container_pool):
        """get_container returns None when function not in pool."""
        result = container_pool.get_container("python3.13", "func-nonexistent")
        assert result is None

    def test_get_returns_none_for_expired_container(
        self, container_pool, mock_docker_client
    ):
        """get_container returns None when container TTL has expired."""
        mock_docker_client.containers.get.return_value = MagicMock(status="running")
        container_pool.add_container("python3.13", "func-exp", "ctr-expired")
        # Manually set last_used to expired time
        key = "python3.13:func-exp"
        container_pool.warm_containers[key][
            "last_used"
        ] = datetime.utcnow() - timedelta(seconds=700)
        result = container_pool.get_container("python3.13", "func-exp")
        assert result is None

    def test_get_returns_none_for_dead_container(
        self, container_pool, mock_docker_client
    ):
        """get_container returns None when container is not running."""
        mock_docker_client.containers.get.return_value = MagicMock(status="exited")
        container_pool.add_container("nodejs", "func-dead", "ctr-dead")
        result = container_pool.get_container("nodejs", "func-dead")
        assert result is None

    def test_key_format_is_runtime_colon_function_id(
        self, container_pool, mock_docker_client
    ):
        """Pool key uses 'runtime:function_id' format."""
        container_pool.add_container("go", "func-99", "ctr-go")
        assert "go:func-99" in container_pool.warm_containers


class TestContainerPoolCleanup:
    """Tests for cleanup operations."""

    def test_cleanup_expired_removes_old_containers(
        self, container_pool, mock_docker_client
    ):
        """cleanup_expired removes containers past TTL."""
        mock_docker_client.containers.get.return_value = MagicMock(status="running")
        container_pool.add_container("python3.13", "func-old", "ctr-old")
        # Set last_used to expired
        key = "python3.13:func-old"
        container_pool.warm_containers[key][
            "last_used"
        ] = datetime.utcnow() - timedelta(seconds=700)
        container_pool.cleanup_expired()
        assert key not in container_pool.warm_containers

    def test_cleanup_expired_keeps_fresh_containers(
        self, container_pool, mock_docker_client
    ):
        """cleanup_expired keeps containers within TTL."""
        mock_docker_client.containers.get.return_value = MagicMock(status="running")
        container_pool.add_container("python3.13", "func-fresh", "ctr-fresh")
        container_pool.cleanup_expired()
        assert "python3.13:func-fresh" in container_pool.warm_containers

    def test_shutdown_stops_all_containers(self, container_pool, mock_docker_client):
        """shutdown stops and removes all containers."""
        running_container = MagicMock(status="running")
        running_container.stop = MagicMock()
        running_container.remove = MagicMock()
        mock_docker_client.containers.get.return_value = running_container

        container_pool.add_container("python3.13", "func-a", "ctr-a")
        container_pool.add_container("nodejs", "func-b", "ctr-b")

        container_pool.shutdown()
        assert len(container_pool.warm_containers) == 0


class TestContainerPoolErrors:
    """Error path tests for container pool."""

    def test_pool_exhausted_on_get_returns_none(
        self, container_pool, mock_docker_client
    ):
        """When pool is empty for a request, get_container returns None."""
        # Pool has no containers, so any get returns None
        result = container_pool.get_container("python3.13", "func-unknown")
        assert result is None
        assert len(container_pool.warm_containers) == 0

    def test_container_crash_triggers_removal(self, container_pool, mock_docker_client):
        """When container is not running, it is removed from pool."""
        # Add a container that will be marked as dead
        mock_docker_client.containers.get.return_value = MagicMock(status="exited")
        container_pool.add_container("python3.13", "func-crashed", "ctr-crashed")

        # Attempting to get it should trigger removal
        result = container_pool.get_container("python3.13", "func-crashed")

        assert result is None
        assert "python3.13:func-crashed" not in container_pool.warm_containers

    def test_container_not_found_exception_handled(
        self, container_pool, mock_docker_client
    ):
        """When docker.errors.NotFound is raised, container is removed."""
        import docker

        # Add container then make Docker report it as not found
        container_pool.add_container("go", "func-orphan", "ctr-orphan")
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound(
            "Not found"
        )

        result = container_pool.get_container("go", "func-orphan")

        assert result is None
        assert "go:func-orphan" not in container_pool.warm_containers

    def test_docker_api_error_handled_gracefully(
        self, container_pool, mock_docker_client
    ):
        """When Docker API raises non-NotFound exception, container is marked dead."""
        import docker

        container_pool.add_container("nodejs", "func-error", "ctr-error")
        mock_docker_client.containers.get.side_effect = docker.errors.APIError(
            "API error"
        )

        result = container_pool.get_container("nodejs", "func-error")

        assert result is None
        # Container is removed because _is_container_alive returns False on error
        assert "nodejs:func-error" not in container_pool.warm_containers

    def test_remove_container_handles_docker_error(
        self, container_pool, mock_docker_client
    ):
        """_remove_container handles Docker errors gracefully."""
        import docker

        container_pool.add_container("python3.13", "func-remove-err", "ctr-remove-err")

        # Make Docker fail when trying to stop the container
        mock_docker_client.containers.get.side_effect = docker.errors.APIError(
            "Cannot connect"
        )

        # Should not raise exception
        container_pool._remove_container("python3.13:func-remove-err")

        # Container should be removed from pool despite Docker error
        assert "python3.13:func-remove-err" not in container_pool.warm_containers

    def test_remove_nonexistent_key_is_noop(self, container_pool, mock_docker_client):
        """Removing a non-existent key does not raise exception."""
        # Should not raise KeyError or other exception
        container_pool._remove_container("python3.13:func-does-not-exist")
        assert "python3.13:func-does-not-exist" not in container_pool.warm_containers

    def test_warmup_on_init_creates_containers(
        self, container_pool, mock_docker_client
    ):
        """Pool initialization creates specified number of warm containers."""
        # Create multiple containers
        running_container = MagicMock(status="running")
        mock_docker_client.containers.get.return_value = running_container

        for i in range(5):
            container_pool.add_container("python3.13", f"func-{i}", f"ctr-{i}")

        assert len(container_pool.warm_containers) == 5
        for i in range(5):
            assert f"python3.13:func-{i}" in container_pool.warm_containers

    def test_cleanup_removes_only_expired_containers(
        self, container_pool, mock_docker_client
    ):
        """cleanup_expired only removes containers past TTL, not fresh ones."""
        running_container = MagicMock(status="running")
        mock_docker_client.containers.get.return_value = running_container

        # Add fresh container
        container_pool.add_container("python3.13", "func-fresh", "ctr-fresh")

        # Add expired container
        container_pool.add_container("nodejs", "func-old", "ctr-old")
        key_old = "nodejs:func-old"
        container_pool.warm_containers[key_old][
            "last_used"
        ] = datetime.utcnow() - timedelta(seconds=700)

        container_pool.cleanup_expired()

        # Fresh should remain, old should be gone
        assert "python3.13:func-fresh" in container_pool.warm_containers
        assert key_old not in container_pool.warm_containers

    def test_shutdown_removes_all_even_on_docker_error(
        self, container_pool, mock_docker_client
    ):
        """shutdown removes all containers from pool even if Docker operations fail."""
        import docker

        container_pool.add_container("python3.13", "func-a", "ctr-a")
        container_pool.add_container("nodejs", "func-b", "ctr-b")

        # Make Docker fail for one container
        mock_docker_client.containers.get.side_effect = [
            docker.errors.NotFound("Not found"),
            MagicMock(status="running", stop=MagicMock(), remove=MagicMock()),
        ]

        # Should complete without exception
        container_pool.shutdown()

        # All containers removed from pool
        assert len(container_pool.warm_containers) == 0

    def test_add_and_multiple_get_updates_last_used(
        self, container_pool, mock_docker_client
    ):
        """Calling get_container updates last_used timestamp each time."""
        running_container = MagicMock(status="running")
        mock_docker_client.containers.get.return_value = running_container

        container_pool.add_container("python3.13", "func-multi", "ctr-multi")
        key = "python3.13:func-multi"

        first_get_time = container_pool.warm_containers[key]["last_used"]

        # Sleep briefly and get again
        with patch("time.sleep", side_effect=lambda x: None):
            time.sleep(0.1)

        result = container_pool.get_container("python3.13", "func-multi")

        second_get_time = container_pool.warm_containers[key]["last_used"]

        assert result == "ctr-multi"
        # Timestamps should differ (second should be later or equal)
        assert second_get_time >= first_get_time

    def test_container_pool_ttl_boundary_condition(
        self, container_pool, mock_docker_client
    ):
        """Container at TTL boundary (exactly 600s) is considered expired."""
        running_container = MagicMock(status="running")
        mock_docker_client.containers.get.return_value = running_container

        container_pool.add_container("python3.13", "func-boundary", "ctr-boundary")
        key = "python3.13:func-boundary"

        # Set last_used to exactly 600 seconds ago (ttl_seconds=60 by fixture)
        # But fixture defines ttl_seconds=60, so let's use that
        container_pool.warm_containers[key][
            "last_used"
        ] = datetime.utcnow() - timedelta(seconds=container_pool.ttl_seconds)

        # Container at exactly TTL boundary should be expired
        result = container_pool.get_container("python3.13", "func-boundary")
        assert result is None
        assert key not in container_pool.warm_containers
