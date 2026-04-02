import os
import sys
from datetime import datetime  # noqa: F401
from unittest.mock import MagicMock, patch

import pytest

# Add the app directory to path so `from app.invoker import ...` style imports work
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
)


@pytest.fixture
def mock_redis():
    """Mock Redis client for IceRuns."""
    mock = MagicMock()
    mock.xreadgroup.return_value = []
    mock.xack.return_value = 1
    mock.xgroup_create.return_value = True
    mock.hset.return_value = True
    mock.publish.return_value = 1
    mock.expire.return_value = True
    return mock


@pytest.fixture
def mock_docker_client():
    """Mock Docker client."""
    mock = MagicMock()
    container = MagicMock()
    container.id = "test-container-123"
    container.status = "running"
    container.wait.return_value = {"StatusCode": 0}
    container.logs.return_value = b'output line\n__ICERUN_OUTPUT__:{"result": "ok"}\n'
    container.stats.return_value = {
        "memory_stats": {"max_usage": 67108864},
        "cpu_stats": {"cpu_usage": {"total_usage": 500000000}},
    }
    container.stop.return_value = None
    container.remove.return_value = None
    mock.containers.run.return_value = container
    mock.containers.get.return_value = container
    return mock


@pytest.fixture
def mock_db():
    """Mock PyDAL database."""
    mock = MagicMock()
    mock.commit.return_value = None
    mock.rollback.return_value = None
    # Mock table operations
    executions_table = MagicMock()
    executions_table.update_or_insert.return_value = True
    mock.return_value = executions_table
    return mock


@pytest.fixture
def invoker_instance(mock_redis, mock_docker_client, mock_db):
    """Create IceRunsInvoker with all deps mocked."""
    with patch("app.invoker.redis.from_url", return_value=mock_redis), patch(
        "app.invoker.docker.from_env", return_value=mock_docker_client
    ), patch("app.invoker.IceRunsInvoker._get_db_connection", return_value=mock_db):
        from app.invoker import IceRunsInvoker

        invoker = IceRunsInvoker()
        return invoker


@pytest.fixture
def container_pool(mock_docker_client):
    """Create ContainerPool with mock Docker client."""
    from app.container_pool import ContainerPool

    return ContainerPool(docker_client=mock_docker_client, ttl_seconds=60)


@pytest.fixture
def sample_task_data():
    """Sample IceRuns task data from Redis stream."""
    return {
        "execution_id": "exec-123",
        "function_id": "func-456",
        "config": (
            '{"runtime": "python3.13", "package_key": "pkg/test.zip",'
            ' "entrypoint": "main.py", "handler": "main.handler",'
            ' "env_vars": {}, "secrets": {}, "memory_limit_mb": 128,'
            ' "timeout_seconds": 60, "cpu_limit": 0.5}'
        ),
        "input_data": '{"name": "test"}',
        "trigger_type": "manual",
    }


@pytest.fixture
def sample_execution_result():
    """Sample execution result from container."""
    return {
        "exit_code": 0,
        "stdout": 'Processing...\n__ICERUN_OUTPUT__:{"result": "success"}\n',
        "stderr": "",
        "output": {"result": "success"},
        "duration_ms": 1500,
        "memory_used_mb": 64,
        "cpu_time_ms": 800,
        "container_id": "test-container-123",
    }


@pytest.fixture(autouse=True)
def reset_runtime_manager():
    """Reset RuntimeManager state between tests."""
    from app.action_runtime import RuntimeManager

    original = dict(RuntimeManager._RUNTIMES)
    yield
    RuntimeManager._RUNTIMES = original
