"""Tests for PowerShellRuntime - PowerShell 7.4 container execution."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app'
))


@pytest.fixture
def powershell_runtime():
    """Create PowerShellRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.powershell_runtime import PowerShellRuntime
        rt = PowerShellRuntime.__new__(PowerShellRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestPowerShellRuntime:
    """Tests for PowerShell 7.4 runtime."""

    def test_image_name_correct(self, powershell_runtime):
        """image_name returns PowerShell 7.4 image."""
        assert powershell_runtime.image_name == "iceruns/powershell:7.4"

    def test_prepare_entrypoint_returns_pwsh_command(self, powershell_runtime):
        """prepare_entrypoint returns ['pwsh', '-File', handler]."""
        cmd = powershell_runtime.prepare_entrypoint("script.ps1")
        assert cmd == ["pwsh", "-File", "script.ps1"]

    def test_prepare_entrypoint_uses_handler_as_file(self, powershell_runtime):
        """prepare_entrypoint uses handler as -File argument."""
        cmd = powershell_runtime.prepare_entrypoint("run.ps1")
        assert cmd[1] == "-File"
        assert cmd[2] == "run.ps1"

    def test_prepare_entrypoint_returns_list(self, powershell_runtime):
        """prepare_entrypoint returns a list."""
        result = powershell_runtime.prepare_entrypoint("script.ps1")
        assert isinstance(result, list)

    def test_prepare_entrypoint_accepts_any_handler(self, powershell_runtime):
        """PowerShell runtime accepts any handler string."""
        cmd = powershell_runtime.prepare_entrypoint("Invoke-Handler.ps1")
        assert cmd[0] == "pwsh"
        assert "Invoke-Handler.ps1" in cmd
