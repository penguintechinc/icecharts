import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add parent directory to path so bare module imports work (e.g., `from worker import IceFlowsWorker`)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_redis():
    """Mock aioredis.Redis client."""
    mock = AsyncMock()
    mock.xread = AsyncMock(return_value=[])
    mock.xack = AsyncMock(return_value=1)
    mock.xgroup_create = AsyncMock()
    mock.hset = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def mock_pipeline_executor():
    """Mock PipelineExecutor with common methods."""
    mock = AsyncMock()
    mock.execute_pipeline = AsyncMock(
        return_value={"status": "completed", "stages": []}
    )
    mock.run_stage_tests = AsyncMock(return_value=True)
    mock.execute_git_merge = AsyncMock(return_value=True)
    mock.execute_calls = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_requests_session():
    """Mock requests.Session for CallHandler/DarwinReviewer."""
    mock = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {}
    response.raise_for_status = MagicMock()
    mock.get.return_value = response
    mock.post.return_value = response
    mock.put.return_value = response
    mock.delete.return_value = response
    return mock


@pytest.fixture
def worker_instance(mock_redis):
    """Create an IceFlowsWorker with mocked Redis."""
    from worker import IceFlowsWorker

    worker = IceFlowsWorker(redis_url="redis://localhost:6379", worker_id="test-worker")
    worker.redis_client = mock_redis
    return worker


@pytest.fixture
def sample_pipeline_config():
    """Sample pipeline configuration for testing."""
    return {
        "flow_id": "flow-123",
        "promotion_id": "promo-456",
        "config": {
            "stages": [
                {
                    "id": "stage-1",
                    "type": "test",
                    "test_configs": [
                        {"test_id": "t1", "name": "Unit Tests", "command": "pytest"}
                    ],
                },
                {
                    "id": "stage-2",
                    "type": "merge",
                    "source_branch": "feature/x",
                    "target_branch": "main",
                },
                {
                    "id": "stage-3",
                    "type": "calls",
                    "call_configs": [
                        {"call_id": "c1", "name": "Notify", "call_type": "icestreams"}
                    ],
                    "context": {},
                },
            ]
        },
    }


@pytest.fixture
def git_operations():
    """Create GitOperations with mocked subprocess and requests."""
    with patch("git_operations.subprocess") as mock_sub, patch(
        "git_operations.requests"
    ) as mock_req:  # noqa: F841
        mock_sub.run.return_value = MagicMock(
            stdout="abc123\n", stderr="", returncode=0
        )
        from git_operations import GitOperations

        ops = GitOperations(
            provider="github",
            api_token="test-token",
            repo_url="https://github.com/org/repo",
        )
        yield ops


@pytest.fixture
def call_handler(mock_requests_session):
    """Create CallHandler with mocked HTTP session."""
    with patch("call_handler.requests.Session", return_value=mock_requests_session):
        from call_handler import CallHandler

        handler = CallHandler(
            api_base_url="http://localhost:5000", api_token="test-token"
        )
        return handler


@pytest.fixture
def sample_call_config():
    """Sample call configuration."""
    return {
        "call_id": "call-1",
        "name": "Run Playbook",
        "call_type": "icestreams",
        "target_id": "playbook-123",
        "input_template": {"key": "value"},
        "timeout_seconds": 30,
        "is_blocking": True,
        "trigger_on": "post_merge",
    }


@pytest.fixture
def tmp_repo(tmp_path):
    """Create temporary directory structure for TestRunner tests."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return {"repo_path": str(repo_dir), "working_dir": str(work_dir)}
