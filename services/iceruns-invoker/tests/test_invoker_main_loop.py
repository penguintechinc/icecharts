"""Tests for IceRunsInvoker main loop - Redis stream consumption and worker lifecycle."""

import json
import os
import sys
from unittest.mock import ANY, MagicMock, call, patch

import pytest
import redis

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
)


class TestIceRunsInvokerMainLoop:
    """Tests for the main worker loop consuming from Redis streams."""

    def test_run_creates_consumer_group_on_first_run(self, invoker_instance):
        """run() creates consumer group if not exists."""

        # Setup: first call raises BUSYGROUP, then return empty messages
        def side_effect_xgroup(*args, **kwargs):
            if invoker_instance.redis_client.xgroup_create.call_count == 1:
                raise redis.exceptions.ResponseError("BUSYGROUP")
            return True

        # After group creation, return empty messages to break loop
        invoker_instance.redis_client.xgroup_create.side_effect = side_effect_xgroup
        invoker_instance.redis_client.xreadgroup.return_value = []

        with patch.object(invoker_instance, "process_task"):
            # Break on second iteration
            call_count = [0]
            original_xreadgroup = invoker_instance.redis_client.xreadgroup

            def xreadgroup_side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] > 1:
                    raise KeyboardInterrupt()
                return []

            invoker_instance.redis_client.xreadgroup = xreadgroup_side_effect
            invoker_instance.run()

        # Group creation should have been attempted
        invoker_instance.redis_client.xgroup_create.assert_called()

    def test_run_ignores_busygroup_error(self, invoker_instance):
        """run() ignores BUSYGROUP error from xgroup_create."""

        def xgroup_side_effect(*args, **kwargs):
            error = redis.exceptions.ResponseError(
                "BUSYGROUP Consumer Group name already exists"
            )
            raise error

        invoker_instance.redis_client.xgroup_create.side_effect = xgroup_side_effect
        invoker_instance.redis_client.xreadgroup.return_value = []

        with patch.object(invoker_instance, "process_task"):
            # Should not raise; should continue
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

    def test_run_raises_other_redis_errors(self, invoker_instance):
        """run() raises non-BUSYGROUP xgroup_create errors."""
        error = redis.exceptions.ResponseError("Some other error")
        invoker_instance.redis_client.xgroup_create.side_effect = error
        invoker_instance.redis_client.xreadgroup.return_value = []

        with patch.object(invoker_instance, "process_task"):
            with pytest.raises(redis.exceptions.ResponseError):
                invoker_instance.run()

    def test_run_updates_queue_size_metric(self, invoker_instance):
        """run() updates queue size metric from Redis stream length."""
        invoker_instance.redis_client.xlen.return_value = 42
        invoker_instance.redis_client.xreadgroup.return_value = []

        from app.metrics import QUEUE_SIZE

        with patch.object(QUEUE_SIZE, "set") as mock_set:
            with patch.object(invoker_instance, "process_task"):
                try:
                    with patch("builtins.input", side_effect=KeyboardInterrupt):
                        invoker_instance.run()
                except KeyboardInterrupt:
                    pass

        mock_set.assert_called_with(42)

    def test_run_processes_single_message(self, invoker_instance, sample_task_data):
        """run() processes a single message from Redis stream."""
        message_id = b"1234567890-0"
        message_data = {
            b"execution_id": b"exec-123",
            b"function_id": b"func-456",
            b"config": b'{"runtime": "python3.13", "package_key": "pkg/test.zip", "entrypoint": "main.py", "handler": "main.handler", "env_vars": {}, "secrets": {}, "memory_limit_mb": 128, "timeout_seconds": 60, "cpu_limit": 0.5}',
            b"input_data": b'{"name": "test"}',
        }
        stream_response = [(b"iceruns:tasks", [(message_id, message_data)])]
        invoker_instance.redis_client.xreadgroup.return_value = stream_response
        invoker_instance.redis_client.xlen.return_value = 1

        with patch.object(invoker_instance, "process_task") as mock_process:
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        # process_task should be called with decoded data
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0][0]
        assert call_args["execution_id"] == "exec-123"
        assert call_args["function_id"] == "func-456"

    def test_run_acknowledges_processed_message(self, invoker_instance):
        """run() acknowledges processed message via xack."""
        message_id = b"1234567890-0"
        message_data = {
            b"execution_id": b"exec-123",
            b"function_id": b"func-456",
            b"config": b'{"runtime": "python3.13", "package_key": "pkg/test.zip", "entrypoint": "main.py", "handler": "main.handler", "env_vars": {}, "secrets": {}, "memory_limit_mb": 128, "timeout_seconds": 60, "cpu_limit": 0.5}',
            b"input_data": b"{}",
        }
        stream_response = [(b"iceruns:tasks", [(message_id, message_data)])]
        invoker_instance.redis_client.xreadgroup.return_value = stream_response
        invoker_instance.redis_client.xlen.return_value = 1

        with patch.object(invoker_instance, "process_task"):
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        invoker_instance.redis_client.xack.assert_called_once()
        call_args = invoker_instance.redis_client.xack.call_args
        assert "iceruns:tasks" in call_args[0]
        assert message_id in call_args[0]

    def test_run_continues_on_process_task_error(self, invoker_instance):
        """run() logs error but continues loop when process_task fails."""
        message_id = b"1234567890-0"
        message_data = {
            b"execution_id": b"exec-123",
            b"function_id": b"func-456",
            b"config": b'{"runtime": "python3.13", "package_key": "pkg/test.zip", "entrypoint": "main.py", "handler": "main.handler", "env_vars": {}, "secrets": {}, "memory_limit_mb": 128, "timeout_seconds": 60, "cpu_limit": 0.5}',
            b"input_data": b"{}",
        }
        stream_response = [(b"iceruns:tasks", [(message_id, message_data)])]
        invoker_instance.redis_client.xreadgroup.side_effect = [
            stream_response,
            KeyboardInterrupt(),
        ]
        invoker_instance.redis_client.xlen.return_value = 1

        def process_task_error(data):
            raise ValueError("Task processing failed")

        with patch.object(
            invoker_instance, "process_task", side_effect=process_task_error
        ):
            invoker_instance.run()

        # Should continue without raising
        invoker_instance.redis_client.xreadgroup.assert_called()

    def test_run_handles_keyboard_interrupt(self, invoker_instance):
        """run() gracefully shuts down on KeyboardInterrupt."""
        invoker_instance.redis_client.xreadgroup.side_effect = KeyboardInterrupt()
        invoker_instance.redis_client.xlen.return_value = 0

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            # Should exit gracefully
            invoker_instance.run()

    def test_run_handles_redis_connection_error(self, invoker_instance):
        """run() continues loop on Redis connection errors."""
        error = redis.exceptions.ConnectionError("Connection lost")
        invoker_instance.redis_client.xreadgroup.side_effect = [
            error,
            KeyboardInterrupt(),
        ]
        invoker_instance.redis_client.xlen.return_value = 0

        # Should log error and continue
        invoker_instance.run()

    def test_run_with_blocking_xreadgroup(self, invoker_instance):
        """run() uses blocking xreadgroup with 5s timeout."""
        invoker_instance.redis_client.xreadgroup.return_value = []
        invoker_instance.redis_client.xlen.return_value = 0

        with patch.object(invoker_instance, "process_task"):
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        call_args = invoker_instance.redis_client.xreadgroup.call_args
        # Check for block parameter (5000 milliseconds = 5s)
        assert call_args[1]["block"] == 5000

    def test_run_with_consumer_count_1(self, invoker_instance):
        """run() reads one message at a time (count=1)."""
        invoker_instance.redis_client.xreadgroup.return_value = []
        invoker_instance.redis_client.xlen.return_value = 0

        with patch.object(invoker_instance, "process_task"):
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        call_args = invoker_instance.redis_client.xreadgroup.call_args
        # Check for count parameter
        assert call_args[1]["count"] == 1

    def test_run_with_worker_id_in_group(self, invoker_instance):
        """run() uses worker_id as consumer name in group."""
        invoker_instance.redis_client.xreadgroup.return_value = []
        invoker_instance.redis_client.xlen.return_value = 0

        with patch.object(invoker_instance, "process_task"):
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        call_args = invoker_instance.redis_client.xreadgroup.call_args
        # Worker ID should be used as consumer name
        assert invoker_instance.worker_id in str(call_args)


class TestIceRunsInvokerMessageDecoding:
    """Tests for proper message decoding from Redis streams."""

    def test_run_decodes_byte_string_keys(self, invoker_instance):
        """run() decodes message keys from bytes to strings."""
        message_id = b"1234567890-0"
        message_data = {
            b"execution_id": b"exec-123",
            b"function_id": b"func-456",
            b"config": b'{"runtime": "python3.13", "package_key": "pkg/test.zip", "entrypoint": "main.py", "handler": "main.handler", "env_vars": {}, "secrets": {}, "memory_limit_mb": 128, "timeout_seconds": 60, "cpu_limit": 0.5}',
            b"input_data": b"{}",
        }
        stream_response = [(b"iceruns:tasks", [(message_id, message_data)])]
        invoker_instance.redis_client.xreadgroup.return_value = stream_response
        invoker_instance.redis_client.xlen.return_value = 1

        with patch.object(invoker_instance, "process_task") as mock_process:
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        # Data passed to process_task should have string keys
        task_data = mock_process.call_args[0][0]
        assert isinstance(task_data["execution_id"], str)
        assert isinstance(task_data["function_id"], str)

    def test_run_decodes_byte_string_values(self, invoker_instance):
        """run() decodes message values from bytes to strings."""
        message_id = b"1234567890-0"
        message_data = {
            b"execution_id": b"exec-123",
            b"function_id": b"func-456",
            b"config": b'{"runtime": "python3.13", "package_key": "pkg/test.zip", "entrypoint": "main.py", "handler": "main.handler", "env_vars": {}, "secrets": {}, "memory_limit_mb": 128, "timeout_seconds": 60, "cpu_limit": 0.5}',
            b"input_data": b"{}",
        }
        stream_response = [(b"iceruns:tasks", [(message_id, message_data)])]
        invoker_instance.redis_client.xreadgroup.return_value = stream_response
        invoker_instance.redis_client.xlen.return_value = 1

        with patch.object(invoker_instance, "process_task") as mock_process:
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        task_data = mock_process.call_args[0][0]
        assert isinstance(task_data["execution_id"], str)
        assert task_data["execution_id"] == "exec-123"

    def test_run_handles_string_keys_in_message(self, invoker_instance):
        """run() handles message data that already has string keys."""
        message_id = b"1234567890-0"
        # Already strings, not bytes
        message_data = {
            "execution_id": "exec-123",
            "function_id": "func-456",
            "config": '{"runtime": "python3.13", "package_key": "pkg/test.zip", "entrypoint": "main.py", "handler": "main.handler", "env_vars": {}, "secrets": {}, "memory_limit_mb": 128, "timeout_seconds": 60, "cpu_limit": 0.5}',
            "input_data": "{}",
        }
        stream_response = [(b"iceruns:tasks", [(message_id, message_data)])]
        invoker_instance.redis_client.xreadgroup.return_value = stream_response
        invoker_instance.redis_client.xlen.return_value = 1

        with patch.object(invoker_instance, "process_task") as mock_process:
            try:
                with patch("builtins.input", side_effect=KeyboardInterrupt):
                    invoker_instance.run()
            except KeyboardInterrupt:
                pass

        mock_process.assert_called_once()


class TestGetDbConnection:
    """Tests for database connection initialization."""

    @patch("app.invoker.DAL")
    def test_get_db_connection_default_postgres(self, mock_dal):
        """_get_db_connection defaults to PostgreSQL."""
        with patch.dict(os.environ, {"DB_TYPE": "postgres"}, clear=False):
            from app.invoker import IceRunsInvoker

            with patch("app.invoker.redis.from_url"):
                with patch("app.invoker.docker.from_env"):
                    invoker = IceRunsInvoker()

        # Should have called DAL with postgres URI
        call_args_str = str(mock_dal.call_args)
        assert "postgres://" in call_args_str

    @patch("app.invoker.DAL")
    def test_get_db_connection_with_env_vars(self, mock_dal):
        """_get_db_connection uses environment variables."""
        env = {
            "DB_TYPE": "mysql",
            "DB_HOST": "db.example.com",
            "DB_PORT": "3306",
            "DB_NAME": "testdb",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
        }
        with patch.dict(os.environ, env, clear=False):
            from app.invoker import IceRunsInvoker

            with patch("app.invoker.redis.from_url"):
                with patch("app.invoker.docker.from_env"):
                    invoker = IceRunsInvoker()

        # Should have called DAL with custom config
        call_args_str = str(mock_dal.call_args)
        assert "testuser" in call_args_str or "db.example.com" in call_args_str

    @patch("app.invoker.DAL")
    def test_get_db_connection_pool_size(self, mock_dal):
        """_get_db_connection uses DB_POOL_SIZE env var."""
        with patch.dict(os.environ, {"DB_POOL_SIZE": "20"}, clear=False):
            from app.invoker import IceRunsInvoker

            with patch("app.invoker.redis.from_url"):
                with patch("app.invoker.docker.from_env"):
                    invoker = IceRunsInvoker()

        # pool_size should be 20
        call_kwargs = mock_dal.call_args[1]
        assert call_kwargs["pool_size"] == 20

    @patch("app.invoker.DAL")
    def test_get_db_connection_disables_migration(self, mock_dal):
        """_get_db_connection disables auto-migration."""
        from app.invoker import IceRunsInvoker

        with patch("app.invoker.redis.from_url"):
            with patch("app.invoker.docker.from_env"):
                invoker = IceRunsInvoker()

        call_kwargs = mock_dal.call_args[1]
        assert call_kwargs["migrate_enabled"] is False
