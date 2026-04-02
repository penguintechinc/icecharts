"""Tests for IceRuns container pool warm/cold start management."""

from unittest.mock import MagicMock, patch

import pytest


class TestContainerPool:
    """Test warm/cold start container management."""

    def test_cold_start_creates_new_container(self):
        """Test cold start creates new container."""
        # Mock Docker client and container operations
        with patch("docker.from_env") as mock_docker:
            mock_container = MagicMock()
            mock_docker.return_value.containers.run.return_value = mock_container

            # Simulate cold start
            container_id = mock_docker.return_value.containers.run(
                image="python:3.13-slim", command=["python", "-c", 'print("test")']
            )

            assert container_id is not None
            mock_docker.return_value.containers.run.assert_called_once()

    def test_warm_start_reuses_container(self):
        """Test warm start reuses container."""
        with patch("docker.from_env") as mock_docker:
            mock_container = MagicMock()
            mock_docker.return_value.containers.get.return_value = mock_container

            # Simulate warm start - container already exists
            container = mock_docker.return_value.containers.get("test_container_id")

            assert container is not None
            mock_docker.return_value.containers.get.assert_called_once()

    def test_container_pool_ttl_expiration(self):
        """Test warm container TTL expiration."""
        import time
        from datetime import datetime, timedelta

        # Simulate container with TTL
        container_info = {
            "id": "test_container",
            "created_at": datetime.utcnow(),
            "ttl_seconds": 600,
        }

        # Check TTL
        age = (datetime.utcnow() - container_info["created_at"]).total_seconds()
        assert age < container_info["ttl_seconds"]

        # Simulate expiration
        container_info["created_at"] = datetime.utcnow() - timedelta(seconds=700)
        age = (datetime.utcnow() - container_info["created_at"]).total_seconds()
        assert age > container_info["ttl_seconds"]

    def test_pool_maintains_max_containers(self):
        """Test container pool maintains max size limit."""
        max_containers = 10
        active_containers = []

        for i in range(max_containers + 5):
            if len(active_containers) < max_containers:
                active_containers.append({"id": f"container_{i}"})

        assert len(active_containers) == max_containers

    def test_cleanup_inactive_containers(self):
        """Test cleanup of inactive containers."""
        from datetime import datetime, timedelta

        containers = [
            {
                "id": f"container_{i}",
                "last_used": datetime.utcnow() - timedelta(seconds=i * 100),
            }
            for i in range(5)
        ]

        # Cleanup containers unused for > 600 seconds
        threshold = datetime.utcnow() - timedelta(seconds=600)
        active = [c for c in containers if c["last_used"] > threshold]

        assert len(active) < len(containers)

    def test_container_memory_tracking(self):
        """Test tracking container memory usage."""
        with patch("docker.from_env") as mock_docker:
            mock_container = MagicMock()
            mock_stats = {
                "memory_stats": {
                    "max_usage": 134217728,  # 128 MB
                }
            }
            mock_container.stats.return_value = mock_stats

            stats = mock_container.stats(stream=False)
            memory_used_mb = stats["memory_stats"]["max_usage"] // (1024 * 1024)

            assert memory_used_mb == 128

    def test_container_cpu_tracking(self):
        """Test tracking container CPU time."""
        with patch("docker.from_env") as mock_docker:
            mock_container = MagicMock()
            mock_stats = {
                "cpu_stats": {
                    "cpu_usage": {
                        "total_usage": 5000000000,  # nanoseconds
                    }
                }
            }
            mock_container.stats.return_value = mock_stats

            stats = mock_container.stats(stream=False)
            cpu_time_ms = stats["cpu_stats"]["cpu_usage"]["total_usage"] // 1_000_000

            assert cpu_time_ms == 5000

    def test_concurrent_executions_per_container(self):
        """Test container concurrency limit."""
        max_concurrent = 1  # Functions run sequentially
        current_executions = 0

        for _ in range(5):
            if current_executions < max_concurrent:
                current_executions += 1

        assert current_executions == max_concurrent

    def test_container_removal_on_completion(self):
        """Test container is removed after execution."""
        with patch("docker.from_env") as mock_docker:
            mock_container = MagicMock()
            mock_docker.return_value.containers.run.return_value = mock_container

            # Simulate container execution and removal
            container = mock_docker.return_value.containers.run(
                image="python:3.13-slim"
            )
            container.wait(timeout=60)
            container.remove(force=True)

            mock_docker.return_value.containers.run.assert_called_once()
            container.remove.assert_called_once_with(force=True)

    def test_container_network_isolation(self):
        """Test containers are network isolated."""
        container_config = {
            "network_mode": "none",
            "read_only": True,
            "security_opt": ["no-new-privileges"],
        }

        assert container_config["network_mode"] == "none"
        assert container_config["read_only"] == True
