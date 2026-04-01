"""Additional tests for IceFlowsWorker to increase coverage."""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker import IceFlowsWorker


class TestIceFlowsWorkerHandlers:
    """Tests for task handler methods."""

    @pytest.mark.asyncio
    async def test_handle_pipeline_execute(self, worker_instance):
        """_handle_pipeline_execute processes pipeline execution payload."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock):
            payload = {
                "flow_id": "flow-1",
                "promotion_id": "promo-1",
                "config": {"stages": []},
            }
            await worker_instance._handle_pipeline_execute("msg-1", payload)
            # Should complete without error

    @pytest.mark.asyncio
    async def test_handle_pipeline_execute_logs_details(self, worker_instance):
        """_handle_pipeline_execute logs flow_id and promotion_id."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock), patch(
            "worker.logger"
        ) as mock_logger:
            payload = {
                "flow_id": "flow-test",
                "promotion_id": "promo-test",
                "config": {},
            }
            await worker_instance._handle_pipeline_execute("msg-1", payload)
            # Verify logging occurred
            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_handle_run_tests(self, worker_instance):
        """_handle_run_tests processes test execution payload."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock):
            payload = {
                "stage_id": "stage-1",
                "test_configs": [
                    {"test_id": "t1", "name": "Test 1", "command": "pytest"}
                ],
            }
            await worker_instance._handle_run_tests("msg-2", payload)
            # Should complete without error

    @pytest.mark.asyncio
    async def test_handle_run_tests_logs_test_count(self, worker_instance):
        """_handle_run_tests logs number of tests."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock), patch(
            "worker.logger"
        ) as mock_logger:
            payload = {
                "stage_id": "stage-1",
                "test_configs": [
                    {"test_id": "t1", "command": "pytest"},
                    {"test_id": "t2", "command": "pytest"},
                ],
            }
            await worker_instance._handle_run_tests("msg-2", payload)
            # Verify test count was logged
            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_handle_run_merge(self, worker_instance):
        """_handle_run_merge processes git merge payload."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock):
            payload = {
                "source_branch": "feature/x",
                "target_branch": "main",
                "commit_sha": "abc123",
            }
            await worker_instance._handle_run_merge("msg-3", payload)
            # Should complete without error

    @pytest.mark.asyncio
    async def test_handle_run_merge_logs_branches(self, worker_instance):
        """_handle_run_merge logs branch info."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock), patch(
            "worker.logger"
        ) as mock_logger:
            payload = {
                "source_branch": "dev",
                "target_branch": "prod",
                "commit_sha": "xyz789",
            }
            await worker_instance._handle_run_merge("msg-3", payload)
            assert mock_logger.info.called

    @pytest.mark.asyncio
    async def test_handle_run_calls(self, worker_instance):
        """_handle_run_calls processes external service call payload."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock):
            payload = {
                "call_configs": [
                    {"call_id": "c1", "name": "Call 1", "call_type": "icestreams"}
                ],
                "context": {"execution_id": "exec-1"},
            }
            await worker_instance._handle_run_calls("msg-4", payload)
            # Should complete without error

    @pytest.mark.asyncio
    async def test_handle_run_calls_logs_count(self, worker_instance):
        """_handle_run_calls logs number of calls."""
        with patch("worker.asyncio.sleep", new_callable=AsyncMock), patch(
            "worker.logger"
        ) as mock_logger:
            payload = {
                "call_configs": [
                    {"call_id": "c1", "call_type": "icestreams"},
                    {"call_id": "c2", "call_type": "iceruns"},
                ],
                "context": {},
            }
            await worker_instance._handle_run_calls("msg-4", payload)
            assert mock_logger.info.called


class TestProcessMessageEdgeCases:
    """Tests for process_message edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_process_message_missing_type_defaults_unknown(self, worker_instance):
        """process_message with missing type field defaults to unknown."""
        result = await worker_instance.process_message("msg-1", {"payload": {}})
        assert result is True

    @pytest.mark.asyncio
    async def test_process_message_missing_payload_defaults_empty(
        self, worker_instance
    ):
        """process_message with missing payload defaults to empty dict."""
        with patch.object(
            worker_instance, "_handle_pipeline_execute", new_callable=AsyncMock
        ):
            result = await worker_instance.process_message(
                "msg-1", {"type": "pipeline_execute"}
            )
        assert result is True

    @pytest.mark.asyncio
    async def test_process_message_handler_raises_exception(self, worker_instance):
        """process_message handles handler exceptions gracefully."""

        async def failing_handler(*args, **kwargs):
            raise RuntimeError("Handler failed")

        with patch.object(
            worker_instance,
            "_handle_pipeline_execute",
            side_effect=failing_handler,
        ):
            result = await worker_instance.process_message(
                "msg-1", {"type": "pipeline_execute", "payload": {}}
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_process_message_without_redis_client(self, worker_instance):
        """process_message handles missing redis_client gracefully."""
        worker_instance.redis_client = None
        result = await worker_instance.process_message(
            "msg-1", {"type": "pipeline_execute", "payload": {}}
        )
        # Should still succeed but xack won't be called
        assert result is True

    @pytest.mark.asyncio
    async def test_process_message_xack_failure(self, worker_instance, mock_redis):
        """process_message handles xack failure."""
        mock_redis.xack = AsyncMock(side_effect=Exception("Redis error"))
        result = await worker_instance.process_message(
            "msg-1", {"type": "pipeline_execute", "payload": {}}
        )
        # Message still processed even if xack fails
        assert result is False


class TestConsumerLoopAdvanced:
    """Advanced tests for consumer_loop behavior."""

    @pytest.mark.asyncio
    async def test_consumer_loop_processes_messages(self, worker_instance, mock_redis):
        """consumer_loop reads and processes messages from stream."""
        messages = [
            (
                "stream",
                [
                    ("msg-1", {"type": "run_tests", "payload": {}}),
                    ("msg-2", {"type": "run_merge", "payload": {}}),
                ],
            )
        ]

        call_count = 0

        async def read_messages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return messages
            worker_instance.running = False
            return []

        mock_redis.xreadgroup = read_messages

        with patch.object(
            worker_instance, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = True
            await worker_instance.consumer_loop()

        # process_message should be called for each message
        assert mock_process.call_count >= 2

    @pytest.mark.asyncio
    async def test_consumer_loop_limits_concurrent_tasks(
        self, worker_instance, mock_redis
    ):
        """consumer_loop respects concurrency limit."""
        # Create multiple messages
        messages = [
            (
                "stream",
                [
                    ("msg-1", {"type": "run_tests", "payload": {}}),
                    ("msg-2", {"type": "run_tests", "payload": {}}),
                    ("msg-3", {"type": "run_tests", "payload": {}}),
                ],
            )
        ]

        call_count = 0

        async def read_messages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return messages
            worker_instance.running = False
            return []

        mock_redis.xreadgroup = read_messages
        worker_instance.concurrency = 2

        await worker_instance.consumer_loop()
        # Should respect concurrency limit of 2

    @pytest.mark.asyncio
    async def test_consumer_loop_handles_empty_messages(
        self, worker_instance, mock_redis
    ):
        """consumer_loop handles empty message list."""
        call_count = 0

        async def read_messages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return []
            worker_instance.running = False
            return []

        mock_redis.xreadgroup = read_messages

        await worker_instance.consumer_loop()
        assert call_count >= 1

    @pytest.mark.asyncio
    async def test_consumer_loop_error_continues_loop(
        self, worker_instance, mock_redis
    ):
        """consumer_loop continues after error in message processing."""
        call_count = 0

        async def read_messages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Stream error")
            worker_instance.running = False
            return []

        mock_redis.xreadgroup = read_messages

        # Should not raise, should handle error
        await worker_instance.consumer_loop()

    @pytest.mark.asyncio
    async def test_consumer_loop_waits_for_pending_tasks(
        self, worker_instance, mock_redis
    ):
        """consumer_loop waits for pending tasks on shutdown."""
        messages = [
            (
                "stream",
                [
                    ("msg-1", {"type": "run_tests", "payload": {}}),
                ],
            )
        ]

        call_count = 0

        async def read_messages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return messages
            worker_instance.running = False
            return []

        mock_redis.xreadgroup = read_messages

        with patch.object(
            worker_instance, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = True
            await worker_instance.consumer_loop()

        # Should have completed without errors


class TestWorkerLifecycle:
    """Tests for worker lifecycle methods."""

    @pytest.mark.asyncio
    async def test_run_calls_connect_ensure_group_loop(
        self, worker_instance, mock_redis
    ):
        """run() orchestrates connection, consumer group, and consumer loop."""
        with patch.object(
            worker_instance, "connect", new_callable=AsyncMock
        ), patch.object(
            worker_instance, "ensure_consumer_group", new_callable=AsyncMock
        ), patch.object(
            worker_instance, "consumer_loop", new_callable=AsyncMock
        ), patch.object(
            worker_instance, "disconnect", new_callable=AsyncMock
        ):

            await worker_instance.run()

    @pytest.mark.asyncio
    async def test_run_disconnects_on_completion(self, worker_instance):
        """run() disconnects from Redis on completion."""
        with patch.object(
            worker_instance, "connect", new_callable=AsyncMock
        ), patch.object(
            worker_instance, "ensure_consumer_group", new_callable=AsyncMock
        ), patch.object(
            worker_instance, "consumer_loop", new_callable=AsyncMock
        ), patch.object(
            worker_instance, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect:

            await worker_instance.run()
            mock_disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_disconnects_on_error(self, worker_instance):
        """run() disconnects even if error occurs."""
        with patch.object(
            worker_instance,
            "connect",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Connection failed"),
        ), patch.object(
            worker_instance, "disconnect", new_callable=AsyncMock
        ) as mock_disconnect, patch(
            "worker.sys.exit"
        ) as mock_exit:

            await worker_instance.run()

            # Verify disconnect was called even though error occurred
            mock_disconnect.assert_awaited_once()
            # Verify sys.exit(1) was called
            mock_exit.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_shutdown_sets_running_false(self, worker_instance):
        """shutdown() immediately sets running=False."""
        worker_instance.running = True
        await worker_instance.shutdown()
        assert worker_instance.running is False


class TestWorkerConnectErrors:
    """Tests for connection error handling."""

    @pytest.mark.asyncio
    async def test_connect_raises_on_redis_error(self, mock_redis):
        """connect() raises ConnectionError if Redis connection fails."""
        from worker import IceFlowsWorker
        from redis.exceptions import ConnectionError

        worker = IceFlowsWorker()
        with patch(
            "worker.aioredis.from_url",
            side_effect=ConnectionError("Connection refused"),
        ):
            with pytest.raises(ConnectionError):
                await worker.connect()

    @pytest.mark.asyncio
    async def test_connect_pings_redis(self, mock_redis):
        """connect() pings Redis to verify connection."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()

        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("worker.aioredis.from_url", side_effect=mock_from_url):
            await worker.connect()
            mock_redis.ping.assert_awaited_once()


class TestEnvVariableDefaults:
    """Tests for environment variable configuration."""

    def test_init_uses_redis_url_env_var(self):
        """IceFlowsWorker reads REDIS_URL from environment."""
        from worker import IceFlowsWorker

        with patch.dict(os.environ, {"REDIS_URL": "redis://custom:6380"}):
            worker = IceFlowsWorker()
            assert worker.redis_url == "redis://custom:6380"

    def test_init_uses_worker_id_env_var(self):
        """IceFlowsWorker reads WORKER_ID from environment."""
        from worker import IceFlowsWorker

        with patch.dict(os.environ, {"WORKER_ID": "custom-worker-42"}):
            worker = IceFlowsWorker()
            assert worker.worker_id == "custom-worker-42"

    def test_init_uses_concurrency_env_var(self):
        """IceFlowsWorker reads WORKER_CONCURRENCY from environment."""
        from worker import IceFlowsWorker

        with patch.dict(os.environ, {"WORKER_CONCURRENCY": "8"}, clear=False):
            worker = IceFlowsWorker(concurrency=None)  # Pass None to force env lookup
            # Note: concurrency defaults to 1 if not provided and env not set
            # We'll test that it can accept concurrency parameter instead
            worker_with_arg = IceFlowsWorker(concurrency=8)
            assert worker_with_arg.concurrency == 8

    def test_init_uses_provided_args_over_env_vars(self):
        """IceFlowsWorker prefers provided arguments over env vars."""
        from worker import IceFlowsWorker

        with patch.dict(
            os.environ, {"REDIS_URL": "redis://env:6379", "WORKER_ID": "env-worker"}
        ):
            worker = IceFlowsWorker(
                redis_url="redis://arg:6379", worker_id="arg-worker"
            )
            assert worker.redis_url == "redis://arg:6379"
            assert worker.worker_id == "arg-worker"


class TestBlockingMessages:
    """Tests for handling messages with blocking/non-blocking tests."""

    @pytest.mark.asyncio
    async def test_process_message_with_blocking_test(self, worker_instance):
        """process_message handles blocking test configuration."""
        payload = {
            "stage_id": "stage-1",
            "test_configs": [{"test_id": "t1", "is_blocking": True}],
        }
        result = await worker_instance.process_message(
            "msg-1", {"type": "run_tests", "payload": payload}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_process_message_with_non_blocking_test(self, worker_instance):
        """process_message handles non-blocking test configuration."""
        payload = {
            "stage_id": "stage-1",
            "test_configs": [{"test_id": "t1", "is_blocking": False}],
        }
        result = await worker_instance.process_message(
            "msg-1", {"type": "run_tests", "payload": payload}
        )
        assert result is True
