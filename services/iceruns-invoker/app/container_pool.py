"""Container pool management for warm/cold start optimization."""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import docker

logger = logging.getLogger(__name__)


class ContainerPool:
    """Manage warm container pool for fast execution."""

    def __init__(self, docker_client: docker.DockerClient, ttl_seconds: int = 600):
        """Initialize container pool.

        Args:
            docker_client: Docker client instance
            ttl_seconds: Time-to-live for warm containers (default 10 minutes)
        """
        self.docker_client = docker_client
        self.ttl_seconds = ttl_seconds
        self.warm_containers: Dict[str, Dict] = {}

    def get_container(self, runtime: str, function_id: str) -> Optional[str]:
        """Get warm container for function if available.

        Args:
            runtime: Runtime type (python3.13, nodejs, etc.)
            function_id: Function ID

        Returns:
            Container ID if warm container available, None otherwise
        """
        key = f"{runtime}:{function_id}"

        if key in self.warm_containers:
            container_info = self.warm_containers[key]

            # Check if container is still alive and not expired
            if self._is_container_alive(container_info["container_id"]):
                if datetime.utcnow() - container_info["last_used"] < timedelta(
                    seconds=self.ttl_seconds
                ):
                    container_info["last_used"] = datetime.utcnow()
                    logger.info(
                        f"Reusing warm container {container_info['container_id'][:12]} for {key}"
                    )
                    return container_info["container_id"]
                else:
                    # Expired - remove
                    self._remove_container(key)
            else:
                # Dead - remove from pool
                self.warm_containers.pop(key, None)

        return None

    def add_container(self, runtime: str, function_id: str, container_id: str):
        """Add container to warm pool.

        Args:
            runtime: Runtime type
            function_id: Function ID
            container_id: Container ID
        """
        key = f"{runtime}:{function_id}"
        self.warm_containers[key] = {
            "container_id": container_id,
            "last_used": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        logger.info(f"Added container {container_id[:12]} to warm pool for {key}")

    def cleanup_expired(self):
        """Remove expired containers from pool."""
        now = datetime.utcnow()
        expired_keys = []

        for key, info in self.warm_containers.items():
            if now - info["last_used"] > timedelta(seconds=self.ttl_seconds):
                expired_keys.append(key)

        for key in expired_keys:
            self._remove_container(key)
            logger.info(f"Removed expired container for {key}")

    def _is_container_alive(self, container_id: str) -> bool:
        """Check if container is still running.

        Args:
            container_id: Container ID

        Returns:
            True if container is running, False otherwise
        """
        try:
            container = self.docker_client.containers.get(container_id)
            return container.status == "running"
        except docker.errors.NotFound:
            return False
        except Exception as e:
            logger.error(f"Error checking container {container_id}: {e}")
            return False

    def _remove_container(self, key: str):
        """Remove container from pool and stop it.

        Args:
            key: Pool key (runtime:function_id)
        """
        if key not in self.warm_containers:
            return

        container_id = self.warm_containers[key]["container_id"]
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove(force=True)
        except docker.errors.NotFound:
            pass
        except Exception as e:
            logger.error(f"Error removing container {container_id}: {e}")
        finally:
            self.warm_containers.pop(key, None)

    def shutdown(self):
        """Shutdown pool and cleanup all containers."""
        logger.info(
            f"Shutting down container pool ({len(self.warm_containers)} containers)"
        )
        for key in list(self.warm_containers.keys()):
            self._remove_container(key)
