"""Tests for BashRuntime - Bash 5.2 container execution."""

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
def bash_runtime():
    """Create BashRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.bash_runtime import BashRuntime

        rt = BashRuntime.__new__(BashRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestBashRuntime:
    """Tests for Bash 5.2 runtime."""

    def test_image_name_correct(self, bash_runtime):
        """image_name returns Bash 5.2 image."""
        assert bash_runtime.image_name == "iceruns/bash:5.2"

    def test_prepare_entrypoint_returns_bash_command(self, bash_runtime):
        """prepare_entrypoint returns ['/bin/bash', handler]."""
        cmd = bash_runtime.prepare_entrypoint("script.sh")
        assert cmd == ["/bin/bash", "script.sh"]

    def test_prepare_entrypoint_uses_handler_as_script(self, bash_runtime):
        """prepare_entrypoint uses handler directly as script path."""
        cmd = bash_runtime.prepare_entrypoint("run.sh")
        assert cmd[1] == "run.sh"

    def test_prepare_entrypoint_returns_list(self, bash_runtime):
        """prepare_entrypoint returns a list."""
        result = bash_runtime.prepare_entrypoint("script.sh")
        assert isinstance(result, list)

    def test_prepare_entrypoint_accepts_any_handler(self, bash_runtime):
        """Bash runtime accepts handler without dot (script file)."""
        # Bash doesn't require module.function format
        cmd = bash_runtime.prepare_entrypoint("myscript")
        assert cmd == ["/bin/bash", "myscript"]
