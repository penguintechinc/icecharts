"""Bash 5.2 runtime implementation."""

from typing import List
from app.action_runtime import BaseRuntime


class BashRuntime(BaseRuntime):
    """Bash 5.2 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for Bash runtime."""
        return "iceruns/bash:5.2"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare Bash execution command.

        Handler format: script.sh (script file)

        Args:
            handler: Script filename

        Returns:
            Command list
        """
        # Bash receives input via ICERUN_INPUT environment variable
        # Output should be printed to stdout with __ICERUN_OUTPUT__: prefix
        return ['/bin/bash', handler]
