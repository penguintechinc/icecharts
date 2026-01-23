"""
Test Runner Module for IceFlows Pipeline Stages.

This module provides the TestRunner class that handles test execution for
IceFlows pipeline stages, supporting multiple test frameworks and parallel execution.

Copyright (c) 2026 Penguin Tech Inc.
License: Limited AGPL3
"""

import asyncio
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Maximum output size (64KB per output stream)
MAX_OUTPUT_SIZE = 64 * 1024

# Test framework patterns for output parsing
TEST_FRAMEWORK_PATTERNS = {
    "pytest": {
        "passed": r"(\d+)\s+passed",
        "failed": r"(\d+)\s+failed",
        "skipped": r"(\d+)\s+skipped",
    },
    "npm": {
        "passed": r"(\d+)\s+(?:passing|passed)",
        "failed": r"(\d+)\s+(?:failing|failed)",
        "skipped": r"(\d+)\s+(?:pending|skipped)",
    },
    "go": {
        "passed": r"ok\s+",
        "failed": r"FAIL\s+",
    },
    "cargo": {
        "passed": r"test\s+result:\s+ok",
        "failed": r"test\s+result:\s+FAILED",
    },
}


class TestRunnerError(Exception):
    """Custom exception for test runner failures."""

    pass


@dataclass
class TestResult:
    """Result of a single test execution."""

    test_id: str
    name: str
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: datetime
    finished_at: datetime
    is_blocking: bool
    error_message: Optional[str] = None
    test_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert TestResult to dictionary for serialization."""
        return {
            "test_id": self.test_id,
            "name": self.name,
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "is_blocking": self.is_blocking,
            "error_message": self.error_message,
            "test_summary": self.test_summary,
        }


class TestRunner:
    """Test runner for IceFlows pipeline stages."""

    def __init__(
        self,
        repo_path: str,
        working_dir: str,
        timeout_seconds: int = 300,
    ):
        """
        Initialize the TestRunner.

        Args:
            repo_path: Path to cloned repository
            working_dir: Working directory for test execution
            timeout_seconds: Default timeout for tests (default 300s)

        Raises:
            TestRunnerError: If repo_path or working_dir don't exist
        """
        self.repo_path = repo_path
        self.working_dir = working_dir
        self.timeout_seconds = timeout_seconds

        # Validate paths
        if not Path(repo_path).exists():
            raise TestRunnerError(f"Repository path does not exist: {repo_path}")
        if not Path(working_dir).exists():
            raise TestRunnerError(f"Working directory does not exist: {working_dir}")

        logger.info(
            f"TestRunner initialized: repo_path={repo_path}, "
            f"working_dir={working_dir}, timeout_seconds={timeout_seconds}"
        )

    def run_test(self, test_config: Dict[str, Any]) -> TestResult:
        """
        Execute a single test.

        Args:
            test_config: Test configuration dictionary containing:
                - test_id: Unique identifier for the test
                - name: Human-readable test name
                - command: Command to execute (e.g., "npm test", "pytest")
                - path: Optional relative path to run from
                - environment: Optional environment variables
                - timeout_seconds: Optional timeout override
                - is_blocking: Whether failure blocks pipeline promotion

        Returns:
            TestResult object with execution details

        Raises:
            TestRunnerError: If test configuration is invalid
        """
        test_id = test_config.get("test_id", "unknown")
        name = test_config.get("name", "Unnamed Test")
        command = test_config.get("command")
        path = test_config.get("path", "")
        environment = test_config.get("environment", {})
        timeout = test_config.get("timeout_seconds", self.timeout_seconds)
        is_blocking = test_config.get("is_blocking", True)

        if not command:
            raise TestRunnerError(f"Test {name} missing required 'command' field")

        logger.info(
            f"Starting test execution: test_id={test_id}, name={name}, "
            f"command={command}, timeout={timeout}s"
        )

        started_at = datetime.utcnow()

        try:
            # Determine working directory for this test
            test_working_dir = self._get_test_working_dir(path)
            logger.debug(f"Test working directory: {test_working_dir}")

            # Execute the command
            exit_code, stdout, stderr = self._execute_command(
                command=command,
                cwd=test_working_dir,
                env=environment,
                timeout=timeout,
            )

            finished_at = datetime.utcnow()
            duration = (finished_at - started_at).total_seconds()

            success = exit_code == 0
            error_message = None

            if not success:
                error_message = f"Test failed with exit code {exit_code}"
                logger.warning(
                    f"Test {name} failed: {error_message}\n"
                    f"stdout: {stdout[:500]}\nstderr: {stderr[:500]}"
                )
            else:
                logger.info(f"Test {name} passed in {duration:.2f}s")

            # Parse test output for summary
            test_summary = self._parse_test_output(stdout, stderr, command)

            result = TestResult(
                test_id=test_id,
                name=name,
                success=success,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                started_at=started_at,
                finished_at=finished_at,
                is_blocking=is_blocking,
                error_message=error_message,
                test_summary=test_summary,
            )

            logger.debug(f"Test result: {result.to_dict()}")
            return result

        except subprocess.TimeoutExpired:
            finished_at = datetime.utcnow()
            duration = (finished_at - started_at).total_seconds()
            error_msg = f"Test timeout after {timeout}s"

            logger.error(f"Test {name}: {error_msg}")

            return TestResult(
                test_id=test_id,
                name=name,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                duration_seconds=duration,
                started_at=started_at,
                finished_at=finished_at,
                is_blocking=is_blocking,
                error_message=error_msg,
            )

        except Exception as e:
            finished_at = datetime.utcnow()
            duration = (finished_at - started_at).total_seconds()
            error_msg = str(e)

            logger.error(f"Test {name} execution error: {e}", exc_info=True)

            return TestResult(
                test_id=test_id,
                name=name,
                success=False,
                exit_code=-1,
                stdout="",
                stderr=error_msg,
                duration_seconds=duration,
                started_at=started_at,
                finished_at=finished_at,
                is_blocking=is_blocking,
                error_message=error_msg,
            )

    def run_tests(self, test_configs: List[Dict[str, Any]]) -> List[TestResult]:
        """
        Execute multiple tests sequentially.

        Args:
            test_configs: List of test configuration dictionaries

        Returns:
            List of TestResult objects
        """
        logger.info(f"Running {len(test_configs)} test(s) sequentially")

        results = []
        for idx, test_config in enumerate(test_configs, 1):
            logger.info(f"Executing test {idx}/{len(test_configs)}")
            result = self.run_test(test_config)
            results.append(result)

            # Log blocking test failures
            if not result.success and result.is_blocking:
                logger.warning(
                    f"Blocking test {result.name} failed, "
                    f"but continuing with remaining tests"
                )

        # Summary
        passed = sum(1 for r in results if r.success)
        total = len(results)
        logger.info(f"Sequential test execution completed: {passed}/{total} passed")

        return results

    def run_tests_parallel(
        self,
        test_configs: List[Dict[str, Any]],
        max_parallel: int = 4,
    ) -> List[TestResult]:
        """
        Execute multiple tests in parallel.

        Args:
            test_configs: List of test configuration dictionaries
            max_parallel: Maximum number of parallel test executions (default 4)

        Returns:
            List of TestResult objects
        """
        logger.info(
            f"Running {len(test_configs)} test(s) in parallel "
            f"(max_parallel={max_parallel})"
        )

        if max_parallel < 1:
            raise TestRunnerError("max_parallel must be at least 1")

        # Use semaphore to limit concurrent tests
        results = []
        semaphore = asyncio.Semaphore(max_parallel)

        async def run_test_async(test_config: Dict[str, Any]) -> TestResult:
            """Run a single test with semaphore limiting."""
            async with semaphore:
                test_name = test_config.get("name", "Unnamed Test")
                logger.debug(f"Starting parallel test: {test_name}")
                result = self.run_test(test_config)
                logger.debug(f"Completed parallel test: {test_name}")
                return result

        async def run_all_tests() -> List[TestResult]:
            """Run all tests concurrently with semaphore limiting."""
            tasks = [run_test_async(cfg) for cfg in test_configs]
            return await asyncio.gather(*tasks)

        try:
            # Run tests concurrently
            results = asyncio.run(run_all_tests())
        except RuntimeError:
            # If asyncio.run() fails (already running event loop),
            # fall back to sequential execution
            logger.warning(
                "Event loop already running, falling back to sequential execution"
            )
            results = self.run_tests(test_configs)

        # Summary
        passed = sum(1 for r in results if r.success)
        total = len(results)
        logger.info(f"Parallel test execution completed: {passed}/{total} passed")

        return results

    def _get_test_working_dir(self, relative_path: str = "") -> str:
        """
        Determine the working directory for test execution.

        Args:
            relative_path: Optional relative path within repo

        Returns:
            Absolute path for test execution
        """
        if not relative_path:
            return self.repo_path

        test_dir = Path(self.repo_path) / relative_path
        if not test_dir.exists():
            logger.warning(
                f"Test path does not exist: {test_dir}, "
                f"using repo root instead"
            )
            return self.repo_path

        return str(test_dir)

    def _execute_command(
        self,
        command: str,
        cwd: str,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 300,
    ) -> Tuple[int, str, str]:
        """
        Execute a command with subprocess.

        Args:
            command: Command to execute (shell string)
            cwd: Working directory for command
            env: Environment variables to merge with os.environ
            timeout: Timeout in seconds

        Returns:
            Tuple of (exit_code, stdout, stderr)

        Raises:
            subprocess.TimeoutExpired: If command exceeds timeout
        """
        logger.debug(f"Executing command: {command}")
        logger.debug(f"Working directory: {cwd}")

        # Merge environment variables
        merged_env = os.environ.copy()
        if env:
            logger.debug(f"Merging environment variables: {list(env.keys())}")
            merged_env.update(env)

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                env=merged_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning(f"Command timeout after {timeout}s, killing process")
                process.kill()
                stdout, stderr = process.communicate()
                raise

            # Truncate output if exceeds max size
            if len(stdout) > MAX_OUTPUT_SIZE:
                logger.warning(
                    f"stdout truncated from {len(stdout)} to {MAX_OUTPUT_SIZE} bytes"
                )
                stdout = stdout[:MAX_OUTPUT_SIZE]

            if len(stderr) > MAX_OUTPUT_SIZE:
                logger.warning(
                    f"stderr truncated from {len(stderr)} to {MAX_OUTPUT_SIZE} bytes"
                )
                stderr = stderr[:MAX_OUTPUT_SIZE]

            exit_code = process.returncode
            logger.debug(
                f"Command completed with exit_code={exit_code}, "
                f"stdout_len={len(stdout)}, stderr_len={len(stderr)}"
            )

            return exit_code, stdout, stderr

        except Exception as e:
            logger.error(f"Command execution error: {e}", exc_info=True)
            raise

    def _parse_test_output(
        self,
        stdout: str,
        stderr: str,
        command: str,
    ) -> Dict[str, Any]:
        """
        Parse test output and extract test summary.

        Attempts to extract test pass/fail counts from common test frameworks.

        Args:
            stdout: Command stdout
            stderr: Command stderr
            command: Original command for framework detection

        Returns:
            Dictionary with parsed test summary (may be empty if unparseable)
        """
        summary = {}

        # Combine output for searching
        combined_output = f"{stdout}\n{stderr}"

        # Detect test framework from command
        framework = None
        if "pytest" in command or "pytest" in stdout or "pytest" in stderr:
            framework = "pytest"
        elif "npm" in command or "jest" in command or "mocha" in command:
            framework = "npm"
        elif "go test" in command or "go test" in stdout:
            framework = "go"
        elif "cargo test" in command or "cargo" in stdout:
            framework = "cargo"

        if framework and framework in TEST_FRAMEWORK_PATTERNS:
            patterns = TEST_FRAMEWORK_PATTERNS[framework]

            for key, pattern in patterns.items():
                match = re.search(pattern, combined_output)
                if match:
                    try:
                        if key == "passed" and framework in ("go", "cargo"):
                            # Go and Cargo use pass/fail indicators, not counts
                            summary[key] = 1 if match else 0
                        else:
                            # Extract numeric value
                            summary[key] = int(match.group(1))
                    except (IndexError, ValueError):
                        pass

        logger.debug(f"Parsed test summary for {framework}: {summary}")
        return summary
