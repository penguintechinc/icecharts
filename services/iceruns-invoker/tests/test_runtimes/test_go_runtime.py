"""Tests for GoRuntime - Go 1.23 container execution."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app'
))


@pytest.fixture
def go_runtime():
    """Create GoRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.go_runtime import GoRuntime
        rt = GoRuntime.__new__(GoRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestGoRuntime:
    """Tests for Go 1.23 runtime."""

    def test_image_name_correct(self, go_runtime):
        """image_name returns Go 1.23 image."""
        assert go_runtime.image_name == "iceruns/go:1.23"

    def test_prepare_entrypoint_returns_main_binary(self, go_runtime):
        """prepare_entrypoint returns ['./main'] for pre-compiled binary."""
        cmd = go_runtime.prepare_entrypoint("main.Handler")
        assert cmd == ["./main"]

    def test_prepare_entrypoint_ignores_handler(self, go_runtime):
        """prepare_entrypoint ignores handler argument (uses pre-compiled binary)."""
        cmd1 = go_runtime.prepare_entrypoint("main.Handler")
        cmd2 = go_runtime.prepare_entrypoint("anything.Goes")
        assert cmd1 == cmd2 == ["./main"]

    def test_prepare_entrypoint_returns_list(self, go_runtime):
        """prepare_entrypoint always returns a list."""
        result = go_runtime.prepare_entrypoint("main.Func")
        assert isinstance(result, list)

    def test_entrypoint_command_structure(self, go_runtime):
        """Entrypoint command starts with ./main."""
        cmd = go_runtime.prepare_entrypoint("main.Run")
        assert cmd[0] == "./main"
