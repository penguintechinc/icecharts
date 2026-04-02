"""Go 1.23 runtime implementation."""

from typing import List

from app.action_runtime import BaseRuntime


class GoRuntime(BaseRuntime):
    """Go 1.23 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for Go runtime."""
        return "iceruns/go:1.23"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare Go execution command.

        Handler format: package.Function (e.g., main.Handler)

        Args:
            handler: Handler function

        Returns:
            Command list
        """
        # Go runtime expects pre-compiled binary
        # Handler is the function to call in main package
        return ["./main"]
