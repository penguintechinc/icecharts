"""Tests for IceRunsInvoker - main worker process for executing IceRuns functions."""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))


class TestIceRunsInvokerInit:
    """Tests for IceRunsInvoker initialization."""

    def test_init_with_mocked_deps(self, invoker_instance, mock_redis, mock_docker_client, mock_db):
        """Invoker initializes with mocked Redis, Docker, and DB."""
        assert invoker_instance.redis_client is mock_redis
        assert invoker_instance.docker_client is mock_docker_client
        assert invoker_instance.db is mock_db

    def test_init_worker_id_format(self, invoker_instance):
        """worker_id includes hostname and PID."""
        assert "worker-" in invoker_instance.worker_id

    def test_init_concurrency_default(self, invoker_instance):
        """Default concurrency is 5."""
        assert invoker_instance.concurrency == 5


class TestProcessTask:
    """Tests for process_task execution."""

    def test_process_task_reads_fields(self, invoker_instance, sample_task_data):
        """process_task reads execution_id, function_id, config, input_data."""
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/test"):
                with patch.object(invoker_instance, '_cleanup'):
                    from app.action_runtime import RuntimeManager

                    mock_runtime = MagicMock()
                    mock_runtime.execute.return_value = {
                        'exit_code': 0,
                        'stdout': '',
                        'stderr': '',
                        'output': None,
                        'duration_ms': 100,
                        'memory_used_mb': 64,
                        'cpu_time_ms': 50,
                        'container_id': 'ctr-1',
                    }
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        # Verify status was updated (running and then completed)
        assert invoker_instance.redis_client.hset.called

    def test_process_task_dispatches_runtime(self, invoker_instance, sample_task_data):
        """process_task dispatches to correct runtime based on config."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0,
            'stdout': '',
            'stderr': '',
            'output': None,
            'duration_ms': 100,
            'memory_used_mb': 0,
            'cpu_time_ms': 0,
            'container_id': 'ctr-1',
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime) as mock_get:
                        invoker_instance.process_task(sample_task_data)
        mock_get.assert_called_once_with("python3.13")

    def test_process_task_updates_status_running(self, invoker_instance, sample_task_data):
        """process_task sets status to 'running' before execution."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0, 'stdout': '', 'stderr': '', 'output': None,
            'duration_ms': 100, 'memory_used_mb': 0, 'cpu_time_ms': 0, 'container_id': 'c1'
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        running_call = any("running" in str(c) for c in hset_calls)
        assert running_call

    def test_process_task_updates_status_completed_on_success(self, invoker_instance, sample_task_data):
        """process_task sets status to 'completed' when exit_code=0."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0, 'stdout': '', 'stderr': '', 'output': {'result': 'ok'},
            'duration_ms': 200, 'memory_used_mb': 64, 'cpu_time_ms': 100, 'container_id': 'c1'
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        completed_call = any("completed" in str(c) for c in hset_calls)
        assert completed_call

    def test_process_task_updates_status_failed_on_nonzero_exit(self, invoker_instance, sample_task_data):
        """process_task sets status to 'failed' when exit_code != 0."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 1, 'stdout': '', 'stderr': 'error output', 'output': None,
            'duration_ms': 100, 'memory_used_mb': 0, 'cpu_time_ms': 0, 'container_id': 'c1'
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        failed_call = any("failed" in str(c) for c in hset_calls)
        assert failed_call

    def test_process_task_handles_timeout(self, invoker_instance, sample_task_data):
        """process_task handles TimeoutError and updates status to 'timeout'."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.side_effect = TimeoutError("Execution timed out after 60s")

        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        hset_calls = invoker_instance.redis_client.hset.call_args_list
        timeout_call = any("timeout" in str(c) for c in hset_calls)
        assert timeout_call

    def test_process_task_records_metrics(self, invoker_instance, sample_task_data):
        """process_task records start and end metrics."""
        from app.action_runtime import RuntimeManager
        from app.metrics import MetricsRecorder
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0, 'stdout': '', 'stderr': '', 'output': None,
            'duration_ms': 150, 'memory_used_mb': 64, 'cpu_time_ms': 50, 'container_id': 'c1'
        }
        with patch.object(MetricsRecorder, 'record_execution_start') as mock_start:
            with patch.object(MetricsRecorder, 'record_execution_end') as mock_end:
                with patch.object(MetricsRecorder, 'record_execution_complete'):
                    with patch.object(invoker_instance, '_load_package', return_value=b""):
                        with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                            with patch.object(invoker_instance, '_cleanup'):
                                with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                                    invoker_instance.process_task(sample_task_data)

        mock_start.assert_called_once()
        mock_end.assert_called_once()

    def test_process_task_publishes_redis_events(self, invoker_instance, sample_task_data):
        """process_task publishes events to Redis pub/sub."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0, 'stdout': '', 'stderr': '', 'output': None,
            'duration_ms': 100, 'memory_used_mb': 0, 'cpu_time_ms': 0, 'container_id': 'c1'
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        assert invoker_instance.redis_client.publish.called

    def test_process_task_cleans_temp_dir(self, invoker_instance, sample_task_data):
        """process_task cleans up temp directory after execution."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0, 'stdout': '', 'stderr': '', 'output': None,
            'duration_ms': 100, 'memory_used_mb': 0, 'cpu_time_ms': 0, 'container_id': 'c1'
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/testdir"):
                with patch.object(invoker_instance, '_cleanup') as mock_cleanup:
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime):
                        invoker_instance.process_task(sample_task_data)

        mock_cleanup.assert_called_once_with("/tmp/testdir")

    def test_process_task_handles_missing_runtime(self, invoker_instance, sample_task_data):
        """process_task handles ValueError for unsupported runtime gracefully."""
        from app.action_runtime import RuntimeManager
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', side_effect=ValueError("Unsupported")):
                        # Should not raise; handles gracefully
                        invoker_instance.process_task(sample_task_data)

    def test_process_task_parses_json_config(self, invoker_instance):
        """process_task parses JSON string config correctly."""
        from app.action_runtime import RuntimeManager
        mock_runtime = MagicMock()
        mock_runtime.execute.return_value = {
            'exit_code': 0, 'stdout': '', 'stderr': '', 'output': None,
            'duration_ms': 100, 'memory_used_mb': 0, 'cpu_time_ms': 0, 'container_id': 'c1'
        }
        task_with_json_config = {
            "execution_id": "exec-json",
            "function_id": "func-json",
            "config": '{"runtime": "python3.13", "package_key": "pkg/test.zip", '
                      '"entrypoint": "main.py", "handler": "main.handler", '
                      '"env_vars": {}, "secrets": {}, "memory_limit_mb": 128, '
                      '"timeout_seconds": 30, "cpu_limit": 0.5}',
            "input_data": '{"x": 1}',
        }
        with patch.object(invoker_instance, '_load_package', return_value=b""):
            with patch.object(invoker_instance, '_extract_package', return_value="/tmp/t"):
                with patch.object(invoker_instance, '_cleanup'):
                    with patch.object(RuntimeManager, 'get_runtime', return_value=mock_runtime) as mock_get:
                        invoker_instance.process_task(task_with_json_config)

        mock_get.assert_called_once_with("python3.13")
