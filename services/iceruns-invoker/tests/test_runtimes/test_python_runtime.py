"""Tests for PythonRuntime - Python 3.13 container execution."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app'
))


@pytest.fixture
def python_runtime():
    """Create PythonRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.python_runtime import PythonRuntime
        rt = PythonRuntime.__new__(PythonRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestPythonRuntime:
    """Tests for Python 3.13 runtime."""

    def test_image_name_correct(self, python_runtime):
        """image_name returns Python 3.13 image."""
        assert python_runtime.image_name == "iceruns/python:3.13"

    def test_prepare_entrypoint_valid_handler(self, python_runtime):
        """prepare_entrypoint returns command list for valid handler."""
        cmd = python_runtime.prepare_entrypoint("main.handler")
        assert isinstance(cmd, list)
        assert cmd[0] == "python3"
        assert cmd[1] == "-c"
        assert len(cmd) == 3

    def test_prepare_entrypoint_invalid_handler_raises(self, python_runtime):
        """prepare_entrypoint raises ValueError when handler has no dot."""
        with pytest.raises(ValueError, match="Invalid handler format"):
            python_runtime.prepare_entrypoint("handlerwithnodot")

    def test_prepare_entrypoint_includes_module_in_script(self, python_runtime):
        """prepare_entrypoint embeds module name in wrapper script."""
        cmd = python_runtime.prepare_entrypoint("mymodule.myfunction")
        script = cmd[2]
        assert "mymodule" in script
        assert "myfunction" in script

    def test_prepare_entrypoint_includes_icerun_output_sentinel(self, python_runtime):
        """prepare_entrypoint includes __ICERUN_OUTPUT__ sentinel in script."""
        cmd = python_runtime.prepare_entrypoint("main.process")
        script = cmd[2]
        assert "__ICERUN_OUTPUT__" in script
