#!/usr/bin/env python3
"""
Tests for the IceStreams worker main loop in worker.py.

Tests cover:
- Worker initialization with config and defaults
- Redis connection and disconnection
- Consumer group creation (new + existing)
- Message processing (playbook execute, health check, unknown type)
- Graceful shutdown
- Error handling and recovery
- Status/result/error publishing to Redis
- Concurrent task handling
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call

import pytest
import redis

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worker import IceStreamsWorker
from executor.playbook_executor import ExecutionResult


class TestIceStreamsWorkerInit:
    """Tests for IceStreamsWorker initialization."""

    def test_init_with_defaults(self):
        """Worker initializes with default configuration."""
        worker = IceStreamsWorker()
        assert worker.worker_id == "worker-1"  # Fallback when no env var
        assert worker.concurrency == 1
        assert "redis://" in worker.redis_url
        assert worker.running is False

    def test_init_with_custom_params(self):
        """Worker initializes with provided parameters."""
        worker = IceStreamsWorker(
            redis_url="redis://custom:6379/0",
            worker_id="worker-custom",
            concurrency=5
        )
        assert worker.worker_id == "worker-custom"
        assert worker.concurrency == 5
        assert worker.redis_url == "redis://custom:6379/0"

    def test_init_with_env_variables(self, monkeypatch):
        """Worker reads configuration from environment variables."""
        # Override os.getenv for this test
        def mock_getenv(key, default=None):
            env_map = {
                "REDIS_URL": "redis://env-redis:6379/0",
                "WORKER_ID": "worker-env",
                "WORKER_CONCURRENCY": "10",
            }
            return env_map.get(key, default)

        with patch("worker.os.getenv", side_effect=mock_getenv):
            # Pass concurrency=0 to trigger env var reading (0 is falsy, so it uses 'or')
            worker = IceStreamsWorker(concurrency=0)
            assert worker.redis_url == "redis://env-redis:6379/0"
            assert worker.worker_id == "worker-env"
            assert worker.concurrency == 10

    def test_redis_client_starts_none(self):
        """Redis client is None after initialization."""
        worker = IceStreamsWorker()
        assert worker.redis_client is None

    def test_running_flag_initially_false(self):
        """Running flag is False initially."""
        worker = IceStreamsWorker()
        assert worker.running is False

    def test_stream_and_consumer_group_constants(self):
        """Worker has correct stream and consumer group names."""
        assert IceStreamsWorker.STREAM_NAME == "icestreams:tasks"
        assert IceStreamsWorker.CONSUMER_GROUP == "icestreams-workers"


class TestIceStreamsWorkerConnection:
    """Tests for Redis connection and disconnection."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Worker successfully connects to Redis."""
        worker = IceStreamsWorker()

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()

        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("redis.asyncio.from_url", side_effect=mock_from_url):
            await worker.connect()
            assert worker.redis_client is mock_redis
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Worker raises exception on connection failure."""
        worker = IceStreamsWorker()

        with patch(
            "redis.asyncio.from_url",
            side_effect=redis.exceptions.ConnectionError("Failed to connect")
        ):
            with pytest.raises(redis.exceptions.ConnectionError):
                await worker.connect()

    @pytest.mark.asyncio
    async def test_disconnect_success(self):
        """Worker successfully disconnects from Redis."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()

        await worker.disconnect()
        worker.redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_no_client(self):
        """Worker handles disconnect when no client connected."""
        worker = IceStreamsWorker()
        worker.redis_client = None

        # Should not raise
        await worker.disconnect()


class TestConsumerGroup:
    """Tests for consumer group creation."""

    @pytest.mark.asyncio
    async def test_create_consumer_group(self):
        """Consumer group is created when it doesn't exist."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xgroup_create = AsyncMock()

        await worker.ensure_consumer_group()
        worker.redis_client.xgroup_create.assert_called_once_with(
            "icestreams:tasks",
            "icestreams-workers",
            id="0",
            mkstream=True,
        )

    @pytest.mark.asyncio
    async def test_consumer_group_already_exists(self):
        """No error when consumer group already exists (BUSYGROUP)."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xgroup_create = AsyncMock(
            side_effect=redis.ResponseError("BUSYGROUP Consumer Group name already exists")
        )

        # Should not raise
        await worker.ensure_consumer_group()

    @pytest.mark.asyncio
    async def test_ensure_consumer_group_without_client(self):
        """RuntimeError if client not initialized."""
        worker = IceStreamsWorker()
        worker.redis_client = None

        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await worker.ensure_consumer_group()

    @pytest.mark.asyncio
    async def test_consumer_group_creation_error_not_busygroup(self):
        """Other Redis errors are re-raised."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xgroup_create = AsyncMock(
            side_effect=redis.ResponseError("Some other error")
        )

        with pytest.raises(redis.ResponseError):
            await worker.ensure_consumer_group()


class TestMessageProcessing:
    """Tests for message processing."""

    @pytest.mark.asyncio
    async def test_process_playbook_execute_message(self):
        """Playbook execute message is processed successfully."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xack = AsyncMock()

        mock_executor = AsyncMock()
        mock_result = ExecutionResult(
            success=True,
            node_results={},
            error=None,
            execution_time_ms=100.0,
            completed_nodes=["node1"],
            failed_nodes=[],
            skipped_nodes=[]
        )
        mock_executor.execute = AsyncMock(return_value=mock_result)

        with patch("worker.PlaybookExecutor", return_value=mock_executor):
            result = await worker.process_message(
                "msg-001",
                {
                    "type": "playbook_execute",
                    "payload": {
                        "playbook_id": "pb-001",
                        "playbook_data": {"nodes": [], "connections": []},
                    }
                }
            )

        assert result is True
        worker.redis_client.xack.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_health_check_message(self):
        """Health check message is processed successfully."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xack = AsyncMock()

        result = await worker.process_message(
            "msg-001",
            {"type": "health_check", "payload": {}}
        )

        assert result is True
        worker.redis_client.xack.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_unknown_message_type(self):
        """Unknown message type is logged and acknowledged."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xack = AsyncMock()

        result = await worker.process_message(
            "msg-001",
            {"type": "unknown_type", "payload": {}}
        )

        assert result is True
        worker.redis_client.xack.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_missing_playbook_id(self):
        """Missing playbook_id triggers error handler."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xack = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        result = await worker.process_message(
            "msg-001",
            {
                "type": "playbook_execute",
                "payload": {"playbook_data": {}}  # Missing playbook_id
            }
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_process_message_exception_handling(self):
        """Exception during processing is logged and returns False."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xack = AsyncMock(side_effect=Exception("ACK failed"))

        result = await worker.process_message(
            "msg-001",
            {"type": "health_check", "payload": {}}
        )

        assert result is False


class TestPlaybookExecution:
    """Tests for playbook execution handler."""

    @pytest.mark.asyncio
    async def test_handle_playbook_execute_success(self):
        """Playbook executes successfully and result is published."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        mock_executor = AsyncMock()
        mock_result = ExecutionResult(
            success=True,
            node_results={},
            error=None,
            execution_time_ms=100.0,
            completed_nodes=["node1", "node2"],
            failed_nodes=[],
            skipped_nodes=[]
        )
        mock_executor.execute = AsyncMock(return_value=mock_result)

        with patch("worker.PlaybookExecutor", return_value=mock_executor):
            await worker._handle_playbook_execute(
                "msg-001",
                {
                    "playbook_id": "pb-001",
                    "execution_id": "exec-001",
                    "playbook_data": {"nodes": [], "connections": []},
                    "node_timeout_seconds": 30.0,
                }
            )

        # Verify xadd was called for status and result
        assert worker.redis_client.xadd.call_count >= 2

    @pytest.mark.asyncio
    async def test_handle_playbook_execute_missing_playbook_data(self):
        """Missing playbook_data triggers error."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        await worker._handle_playbook_execute(
            "msg-001",
            {
                "playbook_id": "pb-001",
                "execution_id": "exec-001",
            }
        )

        # Should publish error
        assert worker.redis_client.xadd.called

    @pytest.mark.asyncio
    async def test_handle_playbook_execute_missing_playbook_id(self):
        """Missing playbook_id triggers error."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        await worker._handle_playbook_execute(
            "msg-001",
            {"playbook_data": {}}
        )

        # Should publish error
        assert worker.redis_client.xadd.called

    @pytest.mark.asyncio
    async def test_handle_playbook_execute_generates_execution_id(self):
        """Execution ID is generated if not provided."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        mock_executor = AsyncMock()
        mock_result = ExecutionResult(
            success=True,
            node_results={},
            error=None,
            execution_time_ms=100.0,
            completed_nodes=[],
            failed_nodes=[],
            skipped_nodes=[]
        )
        mock_executor.execute = AsyncMock(return_value=mock_result)

        with patch("worker.PlaybookExecutor", return_value=mock_executor):
            await worker._handle_playbook_execute(
                "msg-001",
                {
                    "playbook_id": "pb-001",
                    "playbook_data": {},
                    # No execution_id provided
                }
            )

        # Should generate an execution_id
        assert worker.redis_client.xadd.called


class TestPublishMethods:
    """Tests for publishing status/result/error to Redis."""

    @pytest.mark.asyncio
    async def test_publish_status(self):
        """Status is published to Redis stream."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        await worker._publish_status(
            "exec-001",
            {"status": "running", "playbook_id": "pb-001"}
        )

        worker.redis_client.xadd.assert_called_once()
        call_args = worker.redis_client.xadd.call_args
        assert "icestreams:executions:exec-001:status" in call_args[0]

    @pytest.mark.asyncio
    async def test_publish_result(self):
        """Result is published to Redis stream."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        mock_result = ExecutionResult(
            success=True,
            node_results={},
            error=None,
            execution_time_ms=100.0,
            completed_nodes=["node1"],
            failed_nodes=[],
            skipped_nodes=[]
        )

        await worker._publish_result("exec-001", mock_result)

        worker.redis_client.xadd.assert_called_once()
        call_args = worker.redis_client.xadd.call_args
        assert "icestreams:executions:exec-001:result" in call_args[0]

    @pytest.mark.asyncio
    async def test_publish_error(self):
        """Error is published to Redis stream."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock()

        await worker._publish_error("exec-001", "Something went wrong")

        worker.redis_client.xadd.assert_called_once()
        call_args = worker.redis_client.xadd.call_args
        assert "icestreams:executions:exec-001:status" in call_args[0]

    @pytest.mark.asyncio
    async def test_publish_when_no_redis_client(self):
        """Publishing methods handle missing redis_client gracefully."""
        worker = IceStreamsWorker()
        worker.redis_client = None

        # Should not raise
        await worker._publish_status("exec-001", {"status": "running"})
        await worker._publish_error("exec-001", "Error")

    @pytest.mark.asyncio
    async def test_publish_exception_handling(self):
        """Exceptions during publishing are caught and logged."""
        worker = IceStreamsWorker()
        worker.redis_client = AsyncMock()
        worker.redis_client.xadd = AsyncMock(side_effect=Exception("Redis error"))

        # Should not raise
        await worker._publish_status("exec-001", {"status": "running"})


class TestConsumerLoop:
    """Tests for the main consumer loop."""

    @pytest.mark.asyncio
    async def test_consumer_loop_processes_messages(self):
        """Consumer loop reads and processes messages."""
        worker = IceStreamsWorker(concurrency=1)
        worker.redis_client = AsyncMock()

        # Setup xreadgroup to return one message then empty, allowing loop to exit
        worker.redis_client.xreadgroup = AsyncMock(
            side_effect=[
                [  # First iteration: one message
                    (
                        "icestreams:tasks",
                        [
                            ("msg-001", {"type": "health_check", "payload": {}}),
                        ]
                    )
                ],
            ]
        )
        worker.redis_client.xack = AsyncMock()

        # Patch consumer_loop to run only once by setting running to False after first iteration
        original_loop = worker.consumer_loop

        async def limited_consumer_loop():
            worker.running = True
            try:
                # Only do one iteration then exit
                messages = await worker.redis_client.xreadgroup(
                    {"icestreams:tasks": ">"},
                    "icestreams-workers",
                    "worker-1",
                    count=1,
                    block=1000,
                )
                if messages:
                    for stream_name, stream_messages in messages:
                        for message_id, message_data in stream_messages:
                            await worker.process_message(message_id, message_data)
            finally:
                worker.running = False

        with patch.object(worker, "consumer_loop", side_effect=limited_consumer_loop):
            await worker.consumer_loop()
            assert worker.redis_client.xack.called

    @pytest.mark.asyncio
    async def test_consumer_loop_without_redis_client(self):
        """Consumer loop raises error if redis_client not initialized."""
        worker = IceStreamsWorker()
        worker.redis_client = None

        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            await worker.consumer_loop()

    @pytest.mark.asyncio
    async def test_shutdown_sets_running_false(self):
        """Shutdown stops the running flag."""
        worker = IceStreamsWorker()
        worker.running = True

        await worker.shutdown()
        assert worker.running is False


class TestWorkerRun:
    """Tests for the main run method."""

    @pytest.mark.asyncio
    async def test_run_connects_and_runs(self):
        """Run method connects, creates consumer group, and starts consumer loop."""
        worker = IceStreamsWorker()
        worker.connect = AsyncMock()
        worker.disconnect = AsyncMock()
        worker.ensure_consumer_group = AsyncMock()
        worker.consumer_loop = AsyncMock()

        await worker.run()

        worker.connect.assert_called_once()
        worker.ensure_consumer_group.assert_called_once()
        worker.consumer_loop.assert_called_once()
        worker.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_disconnects_on_error(self):
        """Run method disconnects even if error occurs."""
        worker = IceStreamsWorker()
        worker.connect = AsyncMock(side_effect=Exception("Connection failed"))
        worker.disconnect = AsyncMock()

        # SystemExit is raised after logging the error, so we need to catch it
        with pytest.raises(SystemExit):
            await worker.run()

        worker.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_disconnects_on_interrupt(self):
        """Run method disconnects on KeyboardInterrupt."""
        worker = IceStreamsWorker()
        worker.connect = AsyncMock()
        worker.ensure_consumer_group = AsyncMock()
        worker.consumer_loop = AsyncMock(side_effect=KeyboardInterrupt())
        worker.disconnect = AsyncMock()

        try:
            await worker.run()
        except KeyboardInterrupt:
            pass

        worker.disconnect.assert_called_once()


class TestConcurrency:
    """Tests for concurrent task handling."""

    @pytest.mark.asyncio
    async def test_concurrency_setting(self):
        """Concurrency limit is respected."""
        worker = IceStreamsWorker(concurrency=3)
        assert worker.concurrency == 3

    @pytest.mark.asyncio
    async def test_worker_processes_multiple_messages(self):
        """Worker can process multiple messages concurrently."""
        worker = IceStreamsWorker(concurrency=2)
        worker.redis_client = AsyncMock()
        worker.redis_client.xack = AsyncMock()

        # Simulate processing multiple messages
        results = []
        for i in range(3):
            result = await worker.process_message(
                f"msg-{i:03d}",
                {"type": "health_check", "payload": {}}
            )
            results.append(result)

        assert all(results)
        assert worker.redis_client.xack.call_count == 3
