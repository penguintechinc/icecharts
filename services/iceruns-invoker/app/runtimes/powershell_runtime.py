"""PowerShell 7.4 runtime implementation."""

from typing import List

from app.action_runtime import BaseRuntime


class PowerShellRuntime(BaseRuntime):
    """PowerShell 7.4 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for PowerShell runtime."""
        return "iceruns/powershell:7.4"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare PowerShell execution command.

        Handler format: script.ps1 (script file)

        Args:
            handler: Script filename

        Returns:
            Command list
        """
        # PowerShell receives input via ICERUN_INPUT environment variable
        # Output should be printed with __ICERUN_OUTPUT__: prefix
        return ["pwsh", "-File", handler]
