"""Action runtime abstraction following OpenWhisk /init and /run pattern."""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import docker

logger = logging.getLogger(__name__)


class BaseRuntime(ABC):
    """Abstract base class for all runtimes following OpenWhisk pattern."""

    def __init__(self):
        """Initialize runtime."""
        self.docker_client = docker.from_env()

    @property
    @abstractmethod
    def image_name(self) -> str:
        """Docker image to use (e.g., iceruns/python:3.13)."""
        pass

    @abstractmethod
    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare command to execute handler function.

        Args:
            handler: Handler function name (e.g., main.process)

        Returns:
            Command list for Docker container
        """
        pass

    def execute(
        self,
        code_dir: str,
        entrypoint: str,
        handler: str,
        input_data: Dict[str, Any],
        env_vars: Dict[str, str],
        secrets: Dict[str, str],
        memory_limit_mb: int,
        timeout_seconds: int,
        cpu_limit: float,
        execution_id: str,
    ) -> Dict[str, Any]:
        """Execute function in Docker container.

        Args:
            code_dir: Directory containing function code
            entrypoint: Main file (e.g., main.py)
            handler: Handler function (e.g., main.process)
            input_data: Input payload
            env_vars: Environment variables
            secrets: Secrets (encrypted)
            memory_limit_mb: Memory limit in MB
            timeout_seconds: Execution timeout in seconds
            cpu_limit: CPU limit (0.1-4.0)
            execution_id: Execution ID

        Returns:
            Execution result dictionary
        """
        start_time = time.time()

        # Merge env vars and secrets
        environment = {**env_vars, **secrets}
        environment["ICERUN_INPUT"] = json.dumps(input_data)
        environment["ICERUN_EXECUTION_ID"] = execution_id

        # Create container with resource limits
        try:
            container = self.docker_client.containers.run(
                image=self.image_name,
                command=self.prepare_entrypoint(handler),
                volumes={code_dir: {"bind": "/function", "mode": "ro"}},
                working_dir="/function",
                environment=environment,
                mem_limit=f"{memory_limit_mb}m",
                memswap_limit=f"{memory_limit_mb}m",  # No swap
                cpu_quota=int(cpu_limit * 100000),  # CPU shares
                network_mode="none",  # No network access by default
                security_opt=["no-new-privileges"],
                read_only=True,  # Read-only filesystem
                tmpfs={"/tmp": "size=100M,mode=1777"},  # Writable /tmp
                detach=True,
                remove=False,  # Keep for inspection
            )

            # Wait for completion with timeout
            try:
                result = container.wait(timeout=timeout_seconds)
                exit_code = result["StatusCode"]

                # Collect logs
                stdout = container.logs(stdout=True, stderr=False).decode(
                    "utf-8", errors="replace"
                )
                stderr = container.logs(stdout=False, stderr=True).decode(
                    "utf-8", errors="replace"
                )

                # Get resource usage
                stats = container.stats(stream=False)
                memory_used_mb = stats["memory_stats"].get("max_usage", 0) // (
                    1024 * 1024
                )
                cpu_time_ms = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"] // 1_000_000
                )

                # Parse output JSON from stdout
                output = self._parse_output(stdout)

                duration_ms = int((time.time() - start_time) * 1000)

                return {
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "output": output,
                    "duration_ms": duration_ms,
                    "memory_used_mb": memory_used_mb,
                    "cpu_time_ms": cpu_time_ms,
                    "container_id": container.id,
                }

            except Exception as e:
                # Timeout or error
                container.stop(timeout=5)
                raise TimeoutError(
                    f"Execution timed out after {timeout_seconds}s"
                ) from e

        except docker.errors.ContainerError as e:
            # Container exited with error
            return {
                "exit_code": e.exit_status,
                "stdout": (
                    e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
                ),
                "stderr": (
                    e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
                ),
                "output": None,
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000),
            }
        finally:
            try:
                container.remove(force=True)
            except Exception as e:
                logger.warning(f"Failed to remove container: {e}")

    def _parse_output(self, stdout: str) -> Any:
        """Extract JSON output from stdout.

        Args:
            stdout: Standard output

        Returns:
            Parsed JSON output or None
        """
        for line in reversed(stdout.split("\n")):
            if line.startswith("__ICERUN_OUTPUT__:"):
                try:
                    return json.loads(line.split(":", 1)[1])
                except json.JSONDecodeError:
                    return None
        return None


class RuntimeManager:
    """Factory for runtime-specific executors."""

    _RUNTIMES = {}

    @classmethod
    def register_runtime(cls, runtime_name: str, runtime_class):
        """Register a runtime class.

        Args:
            runtime_name: Runtime identifier
            runtime_class: Runtime class
        """
        cls._RUNTIMES[runtime_name] = runtime_class

    @classmethod
    def get_runtime(cls, runtime_name: str) -> BaseRuntime:
        """Get runtime instance by name.

        Args:
            runtime_name: Runtime identifier

        Returns:
            Runtime instance

        Raises:
            ValueError: If runtime not supported
        """
        if runtime_name not in cls._RUNTIMES:
            raise ValueError(
                f"Unsupported runtime: {runtime_name}. "
                f"Available: {', '.join(cls._RUNTIMES.keys())}"
            )
        return cls._RUNTIMES[runtime_name]()
