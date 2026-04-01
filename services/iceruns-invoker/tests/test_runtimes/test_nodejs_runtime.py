"""Tests for NodeJSRuntime - Node.js 20 container execution."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "app",
    ),
)


@pytest.fixture
def nodejs_runtime():
    """Create NodeJSRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.nodejs_runtime import NodeJSRuntime

        rt = NodeJSRuntime.__new__(NodeJSRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestNodeJSRuntime:
    """Tests for Node.js 20 runtime."""

    def test_image_name_correct(self, nodejs_runtime):
        """image_name returns Node.js 20 image."""
        assert nodejs_runtime.image_name == "iceruns/nodejs:20"

    def test_prepare_entrypoint_valid_handler(self, nodejs_runtime):
        """prepare_entrypoint returns node -e command for valid handler."""
        cmd = nodejs_runtime.prepare_entrypoint("index.handler")
        assert isinstance(cmd, list)
        assert cmd[0] == "node"
        assert cmd[1] == "-e"
        assert len(cmd) == 3

    def test_prepare_entrypoint_invalid_handler_raises(self, nodejs_runtime):
        """prepare_entrypoint raises ValueError when handler has no dot."""
        with pytest.raises(ValueError, match="Invalid handler format"):
            nodejs_runtime.prepare_entrypoint("handleronly")

    def test_prepare_entrypoint_includes_function_in_script(self, nodejs_runtime):
        """prepare_entrypoint embeds handler function name in wrapper script."""
        cmd = nodejs_runtime.prepare_entrypoint("app.myHandler")
        script = cmd[2]
        assert "myHandler" in script
        assert "app" in script

    def test_prepare_entrypoint_includes_icerun_output_sentinel(self, nodejs_runtime):
        """prepare_entrypoint includes __ICERUN_OUTPUT__ sentinel in script."""
        cmd = nodejs_runtime.prepare_entrypoint("index.handler")
        script = cmd[2]
        assert "__ICERUN_OUTPUT__" in script
