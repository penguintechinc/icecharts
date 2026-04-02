"""Rust 1.75 runtime implementation."""

from typing import List

from app.action_runtime import BaseRuntime


class RustRuntime(BaseRuntime):
    """Rust 1.75 runtime (Debian 12 slim base)."""

    @property
    def image_name(self) -> str:
        """Docker image for Rust runtime."""
        return "iceruns/rust:1.75"

    def prepare_entrypoint(self, handler: str) -> List[str]:
        """Prepare Rust execution command.

        Handler format: ./target/release/binary

        Args:
            handler: Binary path

        Returns:
            Command list
        """
        # Rust runtime expects pre-compiled binary
        return ["./target/release/main"]
