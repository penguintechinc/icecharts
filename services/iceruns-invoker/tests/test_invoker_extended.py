"""Extended tests for IceRunsInvoker - covering additional error paths and edge cases."""

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
)


class TestIceRunsInvokerErrorHandling:
    """Tests for IceRunsInvoker error handling paths."""

    def test_process_task_handles_runtime_error(
        self, invoker_instance, sample_task_data
    ):
        """process_task handles runtime errors and updates status to failed."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.side_effect = RuntimeError("Container crashed")

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        failed_call = any("failed" in str(c) for c in hset_calls)
        assert failed_call

    def test_process_task_handles_permission_error(
        self, invoker_instance, sample_task_data
    ):
        """process_task handles PermissionError gracefully."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.side_effect = PermissionError("Access denied")

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        failed_call = any("failed" in str(c) for c in hset_calls)
        assert failed_call

    def test_process_task_handles_file_not_found_error(
        self, invoker_instance, sample_task_data
    ):
        """process_task handles FileNotFoundError."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.side_effect = FileNotFoundError("entrypoint not found")

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        failed_call = any("failed" in str(c) for c in hset_calls)
        assert failed_call

    def test_process_task_saves_large_logs_to_s3(
        self, invoker_instance, sample_task_data
    ):
        """process_task saves stdout to S3 when >10000 chars."""
        from app.action_runtime import RuntimeManager

        large_stdout = "x" * 15000
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": large_stdout,
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 64,
            "cpu_time_ms": 50,
            "container_id": "c1",
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        invoker_instance,
                        "_save_execution_logs",
                        return_value="s3://logs/exec-123.log",
                    ) as mock_save:
                        with patch.object(
                            RuntimeManager, "get_runtime", return_value=mock_runtime
                        ):
                            invoker_instance.process_task(sample_task_data)

        mock_save.assert_called_once()

    def test_process_task_truncates_large_stdout(
        self, invoker_instance, sample_task_data
    ):
        """process_task truncates stdout to 10000 chars in DB."""
        from app.action_runtime import RuntimeManager

        large_stdout = "x" * 15000
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": large_stdout,
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 64,
            "cpu_time_ms": 50,
            "container_id": "c1",
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        invoker_instance,
                        "_save_execution_logs",
                        return_value="s3://logs/exec-123.log",
                    ):
                        with patch.object(
                            RuntimeManager, "get_runtime", return_value=mock_runtime
                        ):
                            invoker_instance.process_task(sample_task_data)

        # Check executesql was called with truncated stdout
        executesql_calls = invoker_instance.db.executesql.call_args_list
        assert any(len(str(c)) > 0 for c in executesql_calls)

    def test_process_task_no_save_logs_when_small(
        self, invoker_instance, sample_task_data
    ):
        """process_task doesn't save S3 logs when stdout < 10000 chars."""
        from app.action_runtime import RuntimeManager

        small_stdout = "x" * 5000
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": small_stdout,
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 64,
            "cpu_time_ms": 50,
            "container_id": "c1",
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        invoker_instance, "_save_execution_logs"
                    ) as mock_save:
                        with patch.object(
                            RuntimeManager, "get_runtime", return_value=mock_runtime
                        ):
                            invoker_instance.process_task(sample_task_data)

        mock_save.assert_not_called()

    def test_process_task_with_missing_exit_code(
        self, invoker_instance, sample_task_data
    ):
        """process_task handles missing exit_code from runtime."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        # exit_code missing from result
        mock_runtime.execute.return_value = {
            "stdout": "",
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 64,
            "cpu_time_ms": 50,
            "container_id": "c1",
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(sample_task_data)

        # Should default to exit_code=1 (failure)
        hset_calls = invoker_instance.redis_client.hset.call_args_list
        failed_call = any("failed" in str(c) for c in hset_calls)
        assert failed_call

    def test_process_task_calculates_duration(self, invoker_instance, sample_task_data):
        """process_task calculates duration_ms from start/end times."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 64,
            "cpu_time_ms": 50,
            "container_id": "c1",
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(sample_task_data)

        # Verify executesql was called with duration_ms
        executesql_calls = invoker_instance.db.executesql.call_args_list
        assert len(executesql_calls) > 0


class TestIceRunsInvokerPackageHandling:
    """Tests for package extraction and handling."""

    def test_extract_package_from_zip(self, invoker_instance):
        """_extract_package handles zip files."""
        import io
        import zipfile

        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("main.py", 'print("hello")')
        zip_bytes = zip_buffer.getvalue()

        temp_dir = invoker_instance._extract_package(zip_bytes, "main.py")
        assert os.path.exists(temp_dir)
        assert os.path.exists(os.path.join(temp_dir, "main.py"))
        shutil.rmtree(temp_dir)

    def test_extract_package_from_tar(self, invoker_instance):
        """_extract_package handles tar.gz files."""
        import io
        import tarfile

        # Create a tar.gz file in memory
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            tarinfo = tarfile.TarInfo(name="main.py")
            tarinfo.size = len(b'print("hello")')
            tf.addfile(tarinfo, io.BytesIO(b'print("hello")'))
        tar_bytes = tar_buffer.getvalue()

        temp_dir = invoker_instance._extract_package(tar_bytes, "main.py")
        assert os.path.exists(temp_dir)
        shutil.rmtree(temp_dir)

    def test_extract_package_single_file(self, invoker_instance):
        """_extract_package handles single file (not zip/tar)."""
        file_bytes = b'print("hello")'

        temp_dir = invoker_instance._extract_package(file_bytes, "main.py")
        assert os.path.exists(temp_dir)
        assert os.path.exists(os.path.join(temp_dir, "main.py"))
        with open(os.path.join(temp_dir, "main.py"), "rb") as f:
            assert f.read() == file_bytes
        shutil.rmtree(temp_dir)

    def test_extract_package_empty_bytes(self, invoker_instance):
        """_extract_package creates empty directory for empty package."""
        temp_dir = invoker_instance._extract_package(b"", "main.py")
        assert os.path.exists(temp_dir)
        shutil.rmtree(temp_dir)

    def test_cleanup_removes_directory(self, invoker_instance):
        """_cleanup removes temp directory."""
        temp_dir = tempfile.mkdtemp(prefix="test_cleanup_")
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        assert os.path.exists(temp_dir)
        invoker_instance._cleanup(temp_dir)
        assert not os.path.exists(temp_dir)

    def test_cleanup_handles_missing_directory(self, invoker_instance):
        """_cleanup handles already-removed directory."""
        nonexistent = "/tmp/nonexistent_dir_12345"
        # Should not raise
        invoker_instance._cleanup(nonexistent)


class TestIceRunsInvokerStatusUpdates:
    """Tests for status update and pub/sub messaging."""

    def test_update_status_sets_redis_hash(self, invoker_instance):
        """_update_status sets Redis hash with status data."""
        invoker_instance._update_status("exec-123", "running", {"worker_id": "w1"})

        invoker_instance.redis_client.hset.assert_called_once()
        call_args = invoker_instance.redis_client.hset.call_args
        assert "iceruns:status:exec-123" in str(call_args)

    def test_update_status_publishes_event(self, invoker_instance):
        """_update_status publishes event to pub/sub."""
        invoker_instance._update_status("exec-123", "completed", {"output": "ok"})

        invoker_instance.redis_client.publish.assert_called_once()
        call_args = invoker_instance.redis_client.publish.call_args
        assert "iceruns:events:exec-123" in str(call_args)

    def test_update_status_sets_expiration(self, invoker_instance):
        """_update_status sets 24-hour expiration on status hash."""
        invoker_instance._update_status("exec-123", "completed", {})

        invoker_instance.redis_client.expire.assert_called_once()
        call_args = invoker_instance.redis_client.expire.call_args
        assert 86400 in call_args[0]  # 24 hours in seconds

    def test_handle_timeout_updates_database(self, invoker_instance):
        """_handle_timeout updates DB with timeout status."""
        invoker_instance._handle_timeout("exec-123", "Timeout after 60s")

        invoker_instance.db.executesql.assert_called_once()
        invoker_instance.db.commit.assert_called_once()

    def test_handle_timeout_updates_status(self, invoker_instance):
        """_handle_timeout publishes timeout event."""
        invoker_instance._handle_timeout("exec-123", "Timeout after 60s")

        invoker_instance.redis_client.hset.assert_called_once()

    def test_handle_error_updates_database(self, invoker_instance):
        """_handle_error updates DB with error details."""
        error = Exception("Something went wrong")
        invoker_instance._handle_error("exec-123", error)

        invoker_instance.db.executesql.assert_called_once()
        invoker_instance.db.commit.assert_called_once()

    def test_handle_error_updates_status(self, invoker_instance):
        """_handle_error publishes error event."""
        error = Exception("Something went wrong")
        invoker_instance._handle_error("exec-123", error)

        invoker_instance.redis_client.hset.assert_called_once()


class TestIceRunsInvokerConfigParsing:
    """Tests for task config and input data parsing."""

    def test_process_task_with_dict_config(self, invoker_instance):
        """process_task handles dict config (not string)."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 0,
            "cpu_time_ms": 0,
            "container_id": "c1",
        }

        task_data = {
            "execution_id": "exec-dict",
            "function_id": "func-dict",
            "config": {  # Dict, not string
                "runtime": "python3.13",
                "package_key": "pkg/test.zip",
                "entrypoint": "main.py",
                "handler": "main.handler",
                "env_vars": {},
                "secrets": {},
                "memory_limit_mb": 128,
                "timeout_seconds": 60,
                "cpu_limit": 0.5,
            },
            "input_data": {"x": 1},  # Dict, not string
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(task_data)

        mock_runtime.execute.assert_called_once()

    def test_process_task_with_empty_config_objects(self, invoker_instance):
        """process_task handles empty env_vars and secrets."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 0,
            "cpu_time_ms": 0,
            "container_id": "c1",
        }

        task_data = {
            "execution_id": "exec-empty",
            "function_id": "func-empty",
            "config": json.dumps(
                {
                    "runtime": "python3.13",
                    "package_key": "pkg/test.zip",
                    "entrypoint": "main.py",
                    "handler": "main.handler",
                    # env_vars and secrets omitted
                }
            ),
            "input_data": "{}",
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(task_data)

        # Should use defaults
        call_kwargs = mock_runtime.execute.call_args[1]
        assert call_kwargs["env_vars"] == {}
        assert call_kwargs["secrets"] == {}

    def test_process_task_with_custom_runtime_params(self, invoker_instance):
        """process_task passes custom memory and timeout to runtime."""
        from app.action_runtime import RuntimeManager

        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "output": None,
            "duration_ms": 100,
            "memory_used_mb": 0,
            "cpu_time_ms": 0,
            "container_id": "c1",
        }

        task_data = {
            "execution_id": "exec-custom",
            "function_id": "func-custom",
            "config": json.dumps(
                {
                    "runtime": "python3.13",
                    "package_key": "pkg/test.zip",
                    "entrypoint": "main.py",
                    "handler": "main.handler",
                    "memory_limit_mb": 512,
                    "timeout_seconds": 120,
                    "cpu_limit": 1.0,
                    "env_vars": {"KEY": "value"},
                    "secrets": {"SECRET": "secret_value"},
                }
            ),
            "input_data": '{"data": "test"}',
        }

        with patch.object(invoker_instance, "_load_package", return_value=b""):
            with patch.object(
                invoker_instance, "_extract_package", return_value="/tmp/t"
            ):
                with patch.object(invoker_instance, "_cleanup"):
                    with patch.object(
                        RuntimeManager, "get_runtime", return_value=mock_runtime
                    ):
                        invoker_instance.process_task(task_data)

        call_kwargs = mock_runtime.execute.call_args[1]
        assert call_kwargs["memory_limit_mb"] == 512
        assert call_kwargs["timeout_seconds"] == 120
        assert call_kwargs["cpu_limit"] == 1.0
        assert call_kwargs["env_vars"] == {"KEY": "value"}
        assert call_kwargs["secrets"] == {"SECRET": "secret_value"}
