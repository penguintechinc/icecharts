"""Tests for PipelineExecutor - CI/CD pipeline orchestration."""

import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def executor():
    """Create a PipelineExecutor instance."""
    from executor import PipelineExecutor
    return PipelineExecutor()


class TestExecutePipeline:
    """Tests for execute_pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_empty_stages_returns_completed(self, executor):
        """Pipeline with no stages completes with 'completed' status."""
        result = await executor.execute_pipeline("flow-1", "promo-1", {"stages": []})
        assert result["status"] == "completed"
        assert result["flow_id"] == "flow-1"
        assert result["promotion_id"] == "promo-1"

    @pytest.mark.asyncio
    async def test_single_test_stage_completes(self, executor):
        """Pipeline with single test stage runs and completes."""
        config = {
            "stages": [
                {
                    "id": "stage-1",
                    "type": "test",
                    "test_configs": [{"name": "unit-tests"}],
                }
            ]
        }
        result = await executor.execute_pipeline("flow-1", "promo-1", config)
        assert result["status"] == "completed"
        assert len(result["stages"]) == 1
        assert result["stages"][0]["success"] is True

    @pytest.mark.asyncio
    async def test_multi_stage_pipeline_completes(self, executor):
        """Pipeline with multiple stages all complete."""
        config = {
            "stages": [
                {"id": "stage-1", "type": "test", "test_configs": []},
                {
                    "id": "stage-2",
                    "type": "merge",
                    "source_branch": "feature",
                    "target_branch": "main",
                },
                {"id": "stage-3", "type": "calls", "call_configs": [], "context": {}},
            ]
        }
        result = await executor.execute_pipeline("flow-1", "promo-1", config)
        assert result["status"] == "completed"
        assert len(result["stages"]) == 3

    @pytest.mark.asyncio
    async def test_stage_failure_halts_pipeline(self, executor):
        """A failing stage sets status to 'failed' and halts remaining stages."""
        config = {
            "stages": [
                {
                    "id": "stage-1",
                    "type": "test",
                    "test_configs": [{"name": "failing-test"}],
                },
                {"id": "stage-2", "type": "test", "test_configs": []},
            ]
        }
        # Patch run_stage_tests to fail on first call
        call_count = 0

        async def failing_tests(stage_id, test_configs):
            nonlocal call_count
            call_count += 1
            return False  # All calls fail

        with patch.object(executor, "run_stage_tests", side_effect=failing_tests):
            result = await executor.execute_pipeline("flow-1", "promo-1", config)

        assert result["status"] == "failed"
        # Only first stage should have run
        assert call_count == 1
        assert len(result["stages"]) == 1

    @pytest.mark.asyncio
    async def test_status_tracking_in_progress_to_completed(self, executor):
        """Pipeline result contains proper status tracking."""
        result = await executor.execute_pipeline("flow-1", "promo-1", {"stages": []})
        assert "status" in result
        assert "stages" in result
        assert "errors" in result

    @pytest.mark.asyncio
    async def test_exception_in_pipeline_returns_error_status(self, executor):
        """Unexpected exception during pipeline returns 'error' status."""
        config = {"stages": [{"id": "s1", "type": "test", "test_configs": []}]}
        with patch.object(executor, "_execute_stage", side_effect=RuntimeError("crash")):
            result = await executor.execute_pipeline("flow-1", "promo-1", config)
        assert result["status"] == "error"
        assert len(result["errors"]) == 1


class TestRunStageTests:
    """Tests for run_stage_tests execution."""

    @pytest.mark.asyncio
    async def test_empty_test_configs_returns_true(self, executor):
        """No test configs returns True (vacuously passed)."""
        result = await executor.run_stage_tests("stage-1", [])
        assert result is True

    @pytest.mark.asyncio
    async def test_single_test_config_runs(self, executor):
        """Single test config executes and returns True."""
        result = await executor.run_stage_tests(
            "stage-1", [{"name": "my-test", "command": "pytest"}]
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_test_configs_all_pass(self, executor):
        """Multiple test configs all pass returns True."""
        configs = [
            {"name": "test-1"},
            {"name": "test-2"},
            {"name": "test-3"},
        ]
        result = await executor.run_stage_tests("stage-1", configs)
        assert result is True


class TestExecuteGitMerge:
    """Tests for execute_git_merge."""

    @pytest.mark.asyncio
    async def test_merge_without_commit_sha(self, executor):
        """Git merge succeeds without specific commit SHA."""
        result = await executor.execute_git_merge("feature/x", "main")
        assert result is True

    @pytest.mark.asyncio
    async def test_merge_with_commit_sha(self, executor):
        """Git merge succeeds with specific commit SHA."""
        result = await executor.execute_git_merge("feature/x", "main", "abc123")
        assert result is True


class TestExecuteCalls:
    """Tests for execute_calls external service orchestration."""

    @pytest.mark.asyncio
    async def test_empty_call_configs_returns_true(self, executor):
        """No call configs returns True."""
        result = await executor.execute_calls([], {})
        assert result is True

    @pytest.mark.asyncio
    async def test_single_call_executes(self, executor):
        """Single call config executes and returns True."""
        calls = [
            {"service": "icestreams", "endpoint": "/api/v1/playbooks/p1/execute"}
        ]
        result = await executor.execute_calls(calls, {"flow_id": "f1"})
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_calls_all_succeed(self, executor):
        """Multiple calls all succeed returns True."""
        calls = [
            {"service": "icestreams", "endpoint": "/api/v1/playbooks/p1/execute"},
            {"service": "iceruns", "endpoint": "/api/v1/iceruns/functions/f1/invoke"},
        ]
        result = await executor.execute_calls(calls, {})
        assert result is True
