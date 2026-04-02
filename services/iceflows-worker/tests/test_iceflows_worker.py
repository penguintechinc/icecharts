"""Tests for IceFlowsWorker - Redis Streams-based CI/CD pipeline task processor."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis


class TestIceFlowsWorkerInit:
    """Tests for IceFlowsWorker initialization."""

    def test_init_defaults(self):
        """Worker initializes with default stream/group names."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker(redis_url="redis://localhost:6379", worker_id="w1")
        assert worker.STREAM_NAME == "iceflows:tasks"
        assert worker.CONSUMER_GROUP == "iceflows-workers"

    def test_init_custom_worker_id(self):
        """Worker stores custom worker_id."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker(worker_id="my-worker-42")
        assert worker.worker_id == "my-worker-42"

    def test_init_custom_redis_url(self):
        """Worker stores custom redis_url."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker(redis_url="redis://myhost:6380/1")
        assert worker.redis_url == "redis://myhost:6380/1"

    def test_init_concurrency(self):
        """Worker stores concurrency setting."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker(concurrency=4)
        assert worker.concurrency == 4

    def test_init_running_false(self):
        """Worker starts with running=False."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()
        assert worker.running is False

    def test_init_redis_client_none(self):
        """Worker starts with no redis_client."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()
        assert worker.redis_client is None


class TestIceFlowsWorkerConnect:
    """Tests for Redis connection management."""

    @pytest.mark.asyncio
    async def test_connect_creates_redis_client(self, mock_redis):
        """connect() creates and pings Redis client."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker(redis_url="redis://localhost:6379")
        with patch(
            "worker.aioredis.from_url", new_callable=AsyncMock, return_value=mock_redis
        ):
            await worker.connect()
        assert worker.redis_client == mock_redis
        mock_redis.ping.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_closes_redis(self, mock_redis):
        """disconnect() closes the Redis client."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()
        worker.redis_client = mock_redis
        await worker.disconnect()
        mock_redis.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_noop_when_no_client(self):
        """disconnect() does nothing when redis_client is None."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()
        worker.redis_client = None
        await worker.disconnect()  # Should not raise


class TestEnsureConsumerGroup:
    """Tests for consumer group management."""

    @pytest.mark.asyncio
    async def test_ensure_consumer_group_creates_group(
        self, worker_instance, mock_redis
    ):
        """ensure_consumer_group creates stream group successfully."""
        mock_redis.xgroup_create = AsyncMock(return_value=True)
        await worker_instance.ensure_consumer_group()
        mock_redis.xgroup_create.assert_awaited_once_with(
            "iceflows:tasks",
            "iceflows-workers",
            id="0",
            mkstream=True,
        )

    @pytest.mark.asyncio
    async def test_ensure_consumer_group_handles_busygroup(
        self, worker_instance, mock_redis
    ):
        """ensure_consumer_group ignores BUSYGROUP error gracefully."""
        mock_redis.xgroup_create = AsyncMock(
            side_effect=redis.ResponseError(
                "BUSYGROUP Consumer Group name already exists"
            )
        )
        await worker_instance.ensure_consumer_group()  # Should not raise

    @pytest.mark.asyncio
    async def test_ensure_consumer_group_raises_other_errors(
        self, worker_instance, mock_redis
    ):
        """ensure_consumer_group re-raises non-BUSYGROUP errors."""
        mock_redis.xgroup_create = AsyncMock(
            side_effect=redis.ResponseError("ERR some other error")
        )
        with pytest.raises(redis.ResponseError):
            await worker_instance.ensure_consumer_group()

    @pytest.mark.asyncio
    async def test_ensure_consumer_group_requires_client(self):
        """ensure_consumer_group raises RuntimeError if client not initialized."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()
        worker.redis_client = None
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await worker.ensure_consumer_group()


class TestProcessMessage:
    """Tests for process_message routing."""

    @pytest.mark.asyncio
    async def test_process_pipeline_execute(self, worker_instance):
        """process_message routes pipeline_execute to handler."""
        with patch.object(
            worker_instance, "_handle_pipeline_execute", new_callable=AsyncMock
        ) as mock_handler:
            result = await worker_instance.process_message(
                "msg-1", {"type": "pipeline_execute", "payload": {"flow_id": "f1"}}
            )
        mock_handler.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_process_run_tests(self, worker_instance):
        """process_message routes run_tests to handler."""
        with patch.object(
            worker_instance, "_handle_run_tests", new_callable=AsyncMock
        ) as mock_handler:
            result = await worker_instance.process_message(
                "msg-2", {"type": "run_tests", "payload": {}}
            )
        mock_handler.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_process_run_merge(self, worker_instance):
        """process_message routes run_merge to handler."""
        with patch.object(
            worker_instance, "_handle_run_merge", new_callable=AsyncMock
        ) as mock_handler:
            result = await worker_instance.process_message(
                "msg-3", {"type": "run_merge", "payload": {}}
            )
        mock_handler.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_process_run_calls(self, worker_instance):
        """process_message routes run_calls to handler."""
        with patch.object(
            worker_instance, "_handle_run_calls", new_callable=AsyncMock
        ) as mock_handler:
            result = await worker_instance.process_message(
                "msg-4", {"type": "run_calls", "payload": {}}
            )
        mock_handler.assert_awaited_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_process_unknown_type_returns_true(self, worker_instance):
        """process_message with unknown type still returns True (acked)."""
        result = await worker_instance.process_message(
            "msg-5", {"type": "unknown_type", "payload": {}}
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_process_acks_after_success(self, worker_instance, mock_redis):
        """process_message calls xack after successful processing."""
        await worker_instance.process_message(
            "msg-6", {"type": "run_tests", "payload": {}}
        )
        mock_redis.xack.assert_awaited_once_with(
            "iceflows:tasks", "iceflows-workers", "msg-6"
        )

    @pytest.mark.asyncio
    async def test_process_returns_false_on_handler_exception(self, worker_instance):
        """process_message returns False when handler raises."""
        with patch.object(
            worker_instance,
            "_handle_pipeline_execute",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            result = await worker_instance.process_message(
                "msg-err", {"type": "pipeline_execute", "payload": {}}
            )
        assert result is False


class TestConsumerLoop:
    """Tests for consumer loop behavior."""

    @pytest.mark.asyncio
    async def test_consumer_loop_sets_running_true(self, worker_instance, mock_redis):
        """consumer_loop sets running=True on start."""
        mock_redis.xreadgroup = AsyncMock(return_value=[])
        # Simulate loop stopping after first iteration
        call_count = 0

        async def stop_after_one(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            worker_instance.running = False
            return []

        mock_redis.xreadgroup = stop_after_one
        await worker_instance.consumer_loop()
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_consumer_loop_requires_client(self):
        """consumer_loop raises RuntimeError if client not initialized."""
        from worker import IceFlowsWorker

        worker = IceFlowsWorker()
        worker.redis_client = None
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await worker.consumer_loop()

    @pytest.mark.asyncio
    async def test_shutdown_sets_running_false(self, worker_instance):
        """shutdown() sets running=False."""
        worker_instance.running = True
        await worker_instance.shutdown()
        assert worker_instance.running is False
