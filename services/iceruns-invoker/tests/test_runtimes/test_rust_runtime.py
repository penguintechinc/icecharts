"""Tests for RustRuntime - Rust 1.75 container execution."""

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
def rust_runtime():
    """Create RustRuntime with mocked docker client."""
    with patch("app.action_runtime.docker.from_env"):
        from app.runtimes.rust_runtime import RustRuntime

        rt = RustRuntime.__new__(RustRuntime)
        rt.docker_client = MagicMock()
        return rt


class TestRustRuntime:
    """Tests for Rust 1.75 runtime."""

    def test_image_name_correct(self, rust_runtime):
        """image_name returns Rust 1.75 image."""
        assert rust_runtime.image_name == "iceruns/rust:1.75"

    def test_prepare_entrypoint_returns_release_binary(self, rust_runtime):
        """prepare_entrypoint returns ['./target/release/main']."""
        cmd = rust_runtime.prepare_entrypoint("main.run")
        assert cmd == ["./target/release/main"]

    def test_prepare_entrypoint_ignores_handler(self, rust_runtime):
        """prepare_entrypoint ignores handler (uses pre-compiled binary)."""
        cmd1 = rust_runtime.prepare_entrypoint("main.run")
        cmd2 = rust_runtime.prepare_entrypoint("anything")
        assert cmd1 == cmd2 == ["./target/release/main"]

    def test_prepare_entrypoint_returns_list(self, rust_runtime):
        """prepare_entrypoint returns a list."""
        result = rust_runtime.prepare_entrypoint("main.fn")
        assert isinstance(result, list)

    def test_entrypoint_path_is_release_binary(self, rust_runtime):
        """Entrypoint points to Rust release build path."""
        cmd = rust_runtime.prepare_entrypoint("handler")
        assert "./target/release/main" in cmd
