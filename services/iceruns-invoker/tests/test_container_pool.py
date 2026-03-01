"""Tests for ContainerPool - warm container pool management."""

import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))

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

    def test_get_returns_none_for_expired_container(self, container_pool, mock_docker_client):
        """get_container returns None when container TTL has expired."""
        mock_docker_client.containers.get.return_value = MagicMock(status="running")
        container_pool.add_container("python3.13", "func-exp", "ctr-expired")
        # Manually set last_used to expired time
        key = "python3.13:func-exp"
        container_pool.warm_containers[key]["last_used"] = (
            datetime.utcnow() - timedelta(seconds=700)
        )
        result = container_pool.get_container("python3.13", "func-exp")
        assert result is None

    def test_get_returns_none_for_dead_container(self, container_pool, mock_docker_client):
        """get_container returns None when container is not running."""
        mock_docker_client.containers.get.return_value = MagicMock(status="exited")
        container_pool.add_container("nodejs", "func-dead", "ctr-dead")
        result = container_pool.get_container("nodejs", "func-dead")
        assert result is None

    def test_key_format_is_runtime_colon_function_id(self, container_pool, mock_docker_client):
        """Pool key uses 'runtime:function_id' format."""
        container_pool.add_container("go", "func-99", "ctr-go")
        assert "go:func-99" in container_pool.warm_containers


class TestContainerPoolCleanup:
    """Tests for cleanup operations."""

    def test_cleanup_expired_removes_old_containers(self, container_pool, mock_docker_client):
        """cleanup_expired removes containers past TTL."""
        mock_docker_client.containers.get.return_value = MagicMock(status="running")
        container_pool.add_container("python3.13", "func-old", "ctr-old")
        # Set last_used to expired
        key = "python3.13:func-old"
        container_pool.warm_containers[key]["last_used"] = (
            datetime.utcnow() - timedelta(seconds=700)
        )
        container_pool.cleanup_expired()
        assert key not in container_pool.warm_containers

    def test_cleanup_expired_keeps_fresh_containers(self, container_pool, mock_docker_client):
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
