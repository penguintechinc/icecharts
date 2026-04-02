"""Tests for TestRunner module - test execution and result collection."""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_runner import TestResult, TestRunner, TestRunnerError


class TestTestRunnerInit:
    """Tests for TestRunner initialization."""

    def test_init_valid_paths(self, tmp_repo):
        """TestRunner initializes with valid repo and working directories."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
            timeout_seconds=300,
        )
        assert runner.repo_path == tmp_repo["repo_path"]
        assert runner.working_dir == tmp_repo["working_dir"]
        assert runner.timeout_seconds == 300

    def test_init_invalid_repo_path(self, tmp_path):
        """TestRunner raises TestRunnerError if repo_path doesn't exist."""
        with pytest.raises(TestRunnerError, match="Repository path does not exist"):
            TestRunner(
                repo_path=str(tmp_path / "nonexistent"),
                working_dir=str(tmp_path / "work"),
            )

    def test_init_invalid_working_dir(self, tmp_repo):
        """TestRunner raises TestRunnerError if working_dir doesn't exist."""
        with pytest.raises(TestRunnerError, match="Working directory does not exist"):
            TestRunner(
                repo_path=tmp_repo["repo_path"],
                working_dir="/nonexistent/path",
            )

    def test_init_default_timeout(self, tmp_repo):
        """TestRunner uses default timeout of 300 seconds."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )
        assert runner.timeout_seconds == 300

    def test_init_custom_timeout(self, tmp_repo):
        """TestRunner accepts custom timeout."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
            timeout_seconds=60,
        )
        assert runner.timeout_seconds == 60


class TestTestResultDataclass:
    """Tests for TestResult dataclass."""

    def test_test_result_creation(self):
        """TestResult can be instantiated with all fields."""
        now = datetime.utcnow()
        result = TestResult(
            test_id="test-1",
            name="Unit Tests",
            success=True,
            exit_code=0,
            stdout="All tests passed",
            stderr="",
            duration_seconds=5.2,
            started_at=now,
            finished_at=now,
            is_blocking=True,
            error_message=None,
            test_summary={"passed": 10},
        )
        assert result.test_id == "test-1"
        assert result.name == "Unit Tests"
        assert result.success is True

    def test_test_result_to_dict(self):
        """TestResult.to_dict() serializes to dictionary."""
        now = datetime.utcnow()
        result = TestResult(
            test_id="test-1",
            name="Unit Tests",
            success=True,
            exit_code=0,
            stdout="output",
            stderr="",
            duration_seconds=2.5,
            started_at=now,
            finished_at=now,
            is_blocking=True,
            error_message=None,
            test_summary={"passed": 5},
        )
        d = result.to_dict()
        assert d["test_id"] == "test-1"
        assert d["success"] is True
        assert d["duration_seconds"] == 2.5
        assert d["test_summary"]["passed"] == 5
        assert isinstance(d["started_at"], str)  # ISO format


class TestRunTest:
    """Tests for run_test execution."""

    def test_run_test_success(self, tmp_repo):
        """run_test executes command successfully and returns TestResult."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_config = {
            "test_id": "test-1",
            "name": "Echo Test",
            "command": "echo 'test passed'",
            "is_blocking": True,
        }

        result = runner.run_test(test_config)

        assert result.test_id == "test-1"
        assert result.name == "Echo Test"
        assert result.success is True
        assert result.exit_code == 0
        assert "test passed" in result.stdout

    def test_run_test_failure(self, tmp_repo):
        """run_test handles failed command (non-zero exit code)."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_config = {
            "test_id": "test-fail",
            "name": "Failing Test",
            "command": "exit 1",
            "is_blocking": True,
        }

        result = runner.run_test(test_config)

        assert result.success is False
        assert result.exit_code == 1
        assert result.error_message is not None

    def test_run_test_missing_command_raises_error(self, tmp_repo):
        """run_test raises TestRunnerError if command is missing."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_config = {
            "test_id": "test-missing",
            "name": "No Command Test",
            # Missing 'command' field
            "is_blocking": True,
        }

        with pytest.raises(TestRunnerError, match="missing required 'command' field"):
            runner.run_test(test_config)

    def test_run_test_timeout(self, tmp_repo):
        """run_test handles subprocess timeout gracefully."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
            timeout_seconds=1,
        )

        test_config = {
            "test_id": "test-timeout",
            "name": "Timeout Test",
            "command": "sleep 10",
            "timeout_seconds": 1,
            "is_blocking": True,
        }

        result = runner.run_test(test_config)

        assert result.success is False
        assert result.exit_code == -1
        assert "timeout" in result.error_message.lower()

    def test_run_test_custom_working_dir(self, tmp_repo):
        """run_test uses custom path if provided."""
        # Create a subdirectory in repo
        subdir = Path(tmp_repo["repo_path"]) / "subdir"
        subdir.mkdir()

        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_config = {
            "test_id": "test-subdir",
            "name": "Subdir Test",
            "command": "pwd",
            "path": "subdir",
            "is_blocking": True,
        }

        result = runner.run_test(test_config)
        assert result.success is True

    def test_run_test_custom_environment(self, tmp_repo):
        """run_test merges custom environment variables."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_config = {
            "test_id": "test-env",
            "name": "Env Test",
            "command": "echo $TEST_VAR",
            "environment": {"TEST_VAR": "hello"},
            "is_blocking": True,
        }

        result = runner.run_test(test_config)

        assert result.success is True
        assert "hello" in result.stdout

    def test_run_test_custom_timeout(self, tmp_repo):
        """run_test respects timeout_seconds override."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
            timeout_seconds=300,
        )

        test_config = {
            "test_id": "test-timeout-override",
            "name": "Custom Timeout Test",
            "command": "sleep 10",
            "timeout_seconds": 1,  # Override default
            "is_blocking": True,
        }

        result = runner.run_test(test_config)
        assert result.success is False

    def test_run_test_defaults_missing_fields(self, tmp_repo):
        """run_test uses defaults for optional fields."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_config = {
            "command": "echo test",
            # Missing test_id, name, path, environment, timeout_seconds, is_blocking
        }

        result = runner.run_test(test_config)

        assert result.test_id == "unknown"
        assert result.name == "Unnamed Test"
        assert result.is_blocking is True


class TestRunTests:
    """Tests for run_tests (sequential execution)."""

    def test_run_tests_sequential(self, tmp_repo):
        """run_tests executes multiple tests sequentially."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_configs = [
            {
                "test_id": "test-1",
                "name": "Test 1",
                "command": "echo test1",
                "is_blocking": True,
            },
            {
                "test_id": "test-2",
                "name": "Test 2",
                "command": "echo test2",
                "is_blocking": True,
            },
        ]

        results = runner.run_tests(test_configs)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True

    def test_run_tests_mixed_pass_fail(self, tmp_repo):
        """run_tests collects results from both passing and failing tests."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_configs = [
            {
                "test_id": "test-pass",
                "name": "Pass Test",
                "command": "echo pass",
                "is_blocking": True,
            },
            {
                "test_id": "test-fail",
                "name": "Fail Test",
                "command": "exit 1",
                "is_blocking": True,
            },
        ]

        results = runner.run_tests(test_configs)

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    def test_run_tests_empty_list(self, tmp_repo):
        """run_tests handles empty test list."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        results = runner.run_tests([])

        assert results == []


class TestRunTestsParallel:
    """Tests for run_tests_parallel (concurrent execution)."""

    def test_run_tests_parallel_multiple(self, tmp_repo):
        """run_tests_parallel executes tests concurrently."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_configs = [
            {
                "test_id": f"test-{i}",
                "name": f"Test {i}",
                "command": "echo test",
                "is_blocking": True,
            }
            for i in range(3)
        ]

        results = runner.run_tests_parallel(test_configs, max_parallel=2)

        assert len(results) == 3
        assert all(r.success for r in results)

    def test_run_tests_parallel_invalid_max_parallel(self, tmp_repo):
        """run_tests_parallel raises error if max_parallel < 1."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        with pytest.raises(TestRunnerError, match="max_parallel must be at least 1"):
            runner.run_tests_parallel([], max_parallel=0)

    def test_run_tests_parallel_falls_back_to_sequential(self, tmp_repo):
        """run_tests_parallel falls back to sequential on RuntimeError."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        test_configs = [
            {
                "test_id": "test-1",
                "name": "Test 1",
                "command": "echo test",
                "is_blocking": True,
            },
        ]

        # Mock asyncio.run to raise RuntimeError
        with patch(
            "test_runner.asyncio.run", side_effect=RuntimeError("Event loop running")
        ):
            results = runner.run_tests_parallel(test_configs)

        assert len(results) == 1
        assert results[0].success is True


class TestGetTestWorkingDir:
    """Tests for _get_test_working_dir method."""

    def test_get_test_working_dir_default(self, tmp_repo):
        """_get_test_working_dir returns repo_path when no path specified."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        result = runner._get_test_working_dir("")
        assert result == tmp_repo["repo_path"]

    def test_get_test_working_dir_valid_subpath(self, tmp_repo):
        """_get_test_working_dir returns full path for valid subdir."""
        # Create subdir
        subdir = Path(tmp_repo["repo_path"]) / "subdir"
        subdir.mkdir()

        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        result = runner._get_test_working_dir("subdir")
        assert result == str(subdir)

    def test_get_test_working_dir_nonexistent_path_fallback(self, tmp_repo):
        """_get_test_working_dir falls back to repo_path for nonexistent path."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        result = runner._get_test_working_dir("nonexistent")
        assert result == tmp_repo["repo_path"]


class TestExecuteCommand:
    """Tests for _execute_command method."""

    def test_execute_command_success(self, tmp_repo):
        """_execute_command executes command and returns output."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        exit_code, stdout, stderr = runner._execute_command(
            command="echo 'hello world'",
            cwd=tmp_repo["repo_path"],
        )

        assert exit_code == 0
        assert "hello world" in stdout

    def test_execute_command_failure(self, tmp_repo):
        """_execute_command captures non-zero exit codes."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        exit_code, stdout, stderr = runner._execute_command(
            command="exit 42",
            cwd=tmp_repo["repo_path"],
        )

        assert exit_code == 42

    def test_execute_command_custom_env(self, tmp_repo):
        """_execute_command merges custom environment variables."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        exit_code, stdout, stderr = runner._execute_command(
            command="echo $MY_VAR",
            cwd=tmp_repo["repo_path"],
            env={"MY_VAR": "custom_value"},
        )

        assert exit_code == 0
        assert "custom_value" in stdout

    def test_execute_command_timeout_raises_error(self, tmp_repo):
        """_execute_command raises TimeoutExpired on timeout."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        with pytest.raises(subprocess.TimeoutExpired):
            runner._execute_command(
                command="sleep 10",
                cwd=tmp_repo["repo_path"],
                timeout=1,
            )

    def test_execute_command_truncates_large_output(self, tmp_repo):
        """_execute_command truncates stdout/stderr exceeding MAX_OUTPUT_SIZE."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        # Generate output larger than MAX_OUTPUT_SIZE (64KB)
        large_string = "x" * (70 * 1024)
        exit_code, stdout, stderr = runner._execute_command(
            command=f"python3 -c \"print('{large_string}')\"",
            cwd=tmp_repo["repo_path"],
        )

        # Output should be truncated
        assert len(stdout) <= 64 * 1024


class TestParseTestOutput:
    """Tests for _parse_test_output method."""

    def test_parse_pytest_output(self, tmp_repo):
        """_parse_test_output extracts pytest summary."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        stdout = "5 passed, 2 skipped in 1.23s"

        summary = runner._parse_test_output(stdout, "", "pytest")

        assert summary["passed"] == 5
        assert summary["skipped"] == 2

    def test_parse_npm_output(self, tmp_repo):
        """_parse_test_output extracts npm/jest summary."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        stdout = "12 passing, 1 failing"

        summary = runner._parse_test_output(stdout, "", "npm test")

        assert summary["passed"] == 12
        assert summary["failed"] == 1

    def test_parse_go_output(self, tmp_repo):
        """_parse_test_output detects go test result."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        stdout = "ok\t./mypackage\t1.234s"

        summary = runner._parse_test_output(stdout, "", "go test")

        assert summary.get("passed") == 1

    def test_parse_cargo_output(self, tmp_repo):
        """_parse_test_output detects cargo test result."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        stdout = "test result: ok"

        summary = runner._parse_test_output(stdout, "", "cargo test")

        # Cargo sets passed to 1 if pattern matches (not counting actual test count)
        assert summary.get("passed") == 1

    def test_parse_unknown_framework(self, tmp_repo):
        """_parse_test_output returns empty dict for unknown framework."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        summary = runner._parse_test_output("some output", "", "unknown command")

        assert summary == {}

    def test_parse_extracts_from_stderr(self, tmp_repo):
        """_parse_test_output searches both stdout and stderr."""
        runner = TestRunner(
            repo_path=tmp_repo["repo_path"],
            working_dir=tmp_repo["working_dir"],
        )

        stderr = "3 passed, 1 failed"

        summary = runner._parse_test_output("", stderr, "pytest")

        assert summary["passed"] == 3
        assert summary["failed"] == 1
