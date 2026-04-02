"""Tests for BaseRuntime and RuntimeManager - container-based function execution."""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
)


class ConcreteRuntime:
    """Concrete implementation of BaseRuntime for testing."""

    def __init__(self, docker_client):
        self.docker_client = docker_client

    @property
    def image_name(self):
        return "iceruns/test:latest"

    def prepare_entrypoint(self, handler):
        return ["test", handler]

    def _parse_output(self, stdout):
        for line in reversed(stdout.split("\n")):
            if line.startswith("__ICERUN_OUTPUT__:"):
                try:
                    return json.loads(line.split(":", 1)[1])
                except json.JSONDecodeError:
                    return None
        return None

    def execute(
        self,
        code_dir,
        entrypoint,
        handler,
        input_data,
        env_vars,
        secrets,
        memory_limit_mb,
        timeout_seconds,
        cpu_limit,
        execution_id,
    ):
        from app.action_runtime import BaseRuntime

        # Delegate to BaseRuntime.execute by calling it directly
        return BaseRuntime.execute(
            self,
            code_dir=code_dir,
            entrypoint=entrypoint,
            handler=handler,
            input_data=input_data,
            env_vars=env_vars,
            secrets=secrets,
            memory_limit_mb=memory_limit_mb,
            timeout_seconds=timeout_seconds,
            cpu_limit=cpu_limit,
            execution_id=execution_id,
        )


class TestRuntimeManager:
    """Tests for RuntimeManager factory."""

    def test_register_runtime(self, reset_runtime_manager):
        """register_runtime stores runtime class."""
        from app.action_runtime import RuntimeManager

        class FakeRuntime:
            pass

        RuntimeManager.register_runtime("fake", FakeRuntime)
        assert "fake" in RuntimeManager._RUNTIMES

    def test_get_runtime_returns_instance(self, reset_runtime_manager):
        """get_runtime returns instantiated runtime."""
        from app.action_runtime import RuntimeManager

        class FakeRuntime:
            def __init__(self):
                pass

        RuntimeManager.register_runtime("fake", FakeRuntime)
        instance = RuntimeManager.get_runtime("fake")
        assert isinstance(instance, FakeRuntime)

    def test_get_unknown_runtime_raises_value_error(self, reset_runtime_manager):
        """get_runtime raises ValueError for unknown runtime."""
        from app.action_runtime import RuntimeManager

        with pytest.raises(ValueError, match="Unsupported runtime"):
            RuntimeManager.get_runtime("unknown_runtime_xyz")


class TestBaseRuntimeExecute:
    """Tests for BaseRuntime.execute container management."""

    def test_execute_creates_container_with_correct_image(self, mock_docker_client):
        """execute creates container using runtime's image_name."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test", handler]

        runtime = TestRuntime()
        runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main.py",
            handler="main.handler",
            input_data={"key": "val"},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        mock_docker_client.containers.run.assert_called_once()
        call_kwargs = mock_docker_client.containers.run.call_args
        assert call_kwargs[1]["image"] == "iceruns/test:latest"

    def test_execute_sets_memory_limit(self, mock_docker_client):
        """execute passes memory limit to Docker."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main",
            handler="main.h",
            input_data={},
            env_vars={},
            secrets={},
            memory_limit_mb=256,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        call_kwargs = mock_docker_client.containers.run.call_args[1]
        assert call_kwargs["mem_limit"] == "256m"

    def test_execute_sets_cpu_quota(self, mock_docker_client):
        """execute converts cpu_limit to cpu_quota."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main",
            handler="main.h",
            input_data={},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=1.0,
            execution_id="exec-1",
        )
        call_kwargs = mock_docker_client.containers.run.call_args[1]
        assert call_kwargs["cpu_quota"] == 100000

    def test_execute_sets_readonly_mount(self, mock_docker_client):
        """execute mounts code directory as read-only."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        runtime.execute(
            code_dir="/tmp/mycode",
            entrypoint="main",
            handler="main.h",
            input_data={},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        call_kwargs = mock_docker_client.containers.run.call_args[1]
        volumes = call_kwargs["volumes"]
        assert "/tmp/mycode" in volumes
        assert volumes["/tmp/mycode"]["mode"] == "ro"

    def test_execute_sets_icerun_input_env(self, mock_docker_client):
        """execute sets ICERUN_INPUT environment variable."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main",
            handler="main.h",
            input_data={"name": "test"},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        call_kwargs = mock_docker_client.containers.run.call_args[1]
        environment = call_kwargs["environment"]
        assert "ICERUN_INPUT" in environment
        assert json.loads(environment["ICERUN_INPUT"]) == {"name": "test"}

    def test_execute_sets_network_none(self, mock_docker_client):
        """execute disables network access."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main",
            handler="main.h",
            input_data={},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        call_kwargs = mock_docker_client.containers.run.call_args[1]
        assert call_kwargs["network_mode"] == "none"

    def test_execute_returns_exit_code_stdout_stderr(self, mock_docker_client):
        """execute returns dict with exit_code, stdout, stderr."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        result = runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main",
            handler="main.h",
            input_data={},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        assert "exit_code" in result
        assert "stdout" in result
        assert "stderr" in result

    def test_execute_collects_memory_cpu_stats(self, mock_docker_client):
        """execute collects memory and CPU usage from container stats."""
        from app.action_runtime import BaseRuntime

        class TestRuntime(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, handler):
                return ["./test"]

        runtime = TestRuntime()
        result = runtime.execute(
            code_dir="/tmp/code",
            entrypoint="main",
            handler="main.h",
            input_data={},
            env_vars={},
            secrets={},
            memory_limit_mb=128,
            timeout_seconds=30,
            cpu_limit=0.5,
            execution_id="exec-1",
        )
        assert "memory_used_mb" in result
        assert "cpu_time_ms" in result
        # Values from conftest: max_usage=67108864 => 64 MB
        assert result["memory_used_mb"] == 64


class TestParseOutput:
    """Tests for _parse_output sentinel detection."""

    def _make_runtime(self, mock_docker_client):
        """Create a concrete runtime for parse_output testing."""
        from app.action_runtime import BaseRuntime

        class TestRT(BaseRuntime):
            def __init__(self):
                self.docker_client = mock_docker_client

            @property
            def image_name(self):
                return "iceruns/test:latest"

            def prepare_entrypoint(self, h):
                return ["./test"]

        return TestRT()

    def test_parse_output_finds_sentinel(self, mock_docker_client):
        """_parse_output finds __ICERUN_OUTPUT__: marker."""
        rt = self._make_runtime(mock_docker_client)
        stdout = 'some output\n__ICERUN_OUTPUT__:{"result": "ok"}\n'
        result = rt._parse_output(stdout)
        assert result == {"result": "ok"}

    def test_parse_output_returns_none_when_missing(self, mock_docker_client):
        """_parse_output returns None when sentinel is absent."""
        rt = self._make_runtime(mock_docker_client)
        stdout = "just regular output\nno sentinel here\n"
        result = rt._parse_output(stdout)
        assert result is None

    def test_parse_output_last_line_wins(self, mock_docker_client):
        """_parse_output uses last occurrence of sentinel."""
        rt = self._make_runtime(mock_docker_client)
        stdout = '__ICERUN_OUTPUT__:{"first": 1}\nmore output\n__ICERUN_OUTPUT__:{"last": 2}\n'
        result = rt._parse_output(stdout)
        assert result == {"last": 2}

    def test_parse_output_invalid_json_returns_none(self, mock_docker_client):
        """_parse_output returns None for invalid JSON after sentinel."""
        rt = self._make_runtime(mock_docker_client)
        stdout = "__ICERUN_OUTPUT__:not valid json\n"
        result = rt._parse_output(stdout)
        assert result is None
