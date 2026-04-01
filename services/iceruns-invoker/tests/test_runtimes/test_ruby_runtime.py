"""Tests for RubyRuntime - Ruby 3.3 container execution."""

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
def ruby_runtime():
    """Create RubyRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.ruby_runtime import RubyRuntime

        rt = RubyRuntime.__new__(RubyRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestRubyRuntime:
    """Tests for Ruby 3.3 runtime."""

    def test_image_name_correct(self, ruby_runtime):
        """image_name returns Ruby 3.3 image."""
        assert ruby_runtime.image_name == "iceruns/ruby:3.3"

    def test_prepare_entrypoint_valid_handler(self, ruby_runtime):
        """prepare_entrypoint returns ruby -e command for valid handler."""
        cmd = ruby_runtime.prepare_entrypoint("main.handler")
        assert isinstance(cmd, list)
        assert cmd[0] == "ruby"
        assert cmd[1] == "-e"
        assert len(cmd) == 3

    def test_prepare_entrypoint_invalid_handler_raises(self, ruby_runtime):
        """prepare_entrypoint raises ValueError when handler has no dot."""
        with pytest.raises(ValueError, match="Invalid handler format"):
            ruby_runtime.prepare_entrypoint("handleronly")

    def test_prepare_entrypoint_includes_module_and_method(self, ruby_runtime):
        """prepare_entrypoint embeds module and method in wrapper script."""
        cmd = ruby_runtime.prepare_entrypoint("myfile.my_method")
        script = cmd[2]
        assert "myfile" in script
        assert "my_method" in script

    def test_prepare_entrypoint_includes_icerun_output_sentinel(self, ruby_runtime):
        """prepare_entrypoint includes __ICERUN_OUTPUT__ in wrapper script."""
        cmd = ruby_runtime.prepare_entrypoint("main.process")
        script = cmd[2]
        assert "__ICERUN_OUTPUT__" in script
