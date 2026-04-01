#!/usr/bin/env python3
"""
IceStreams Worker - Redis Streams-based task processor.

This worker service consumes tasks from Redis Streams and processes them
asynchronously. It handles infrastructure automation playbook execution.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Any, Dict, Optional

import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError

from executor.playbook_executor import PlaybookExecutor, ExecutionResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IceStreamsWorker:
    """Redis Streams-based task worker for IceCharts infrastructure automation."""

    STREAM_NAME = "icestreams:tasks"
    CONSUMER_GROUP = "icestreams-workers"
    BLOCK_MS = 1000  # Block for 1 second when reading from stream

    def __init__(
        self,
        redis_url: Optional[str] = None,
        worker_id: Optional[str] = None,
        concurrency: int = 1,
    ):
        """
        Initialize the IceStreams Worker.

        Args:
            redis_url: Redis connection URL (from REDIS_URL env var)
            worker_id: Unique identifier for this worker instance
            concurrency: Number of concurrent tasks to process
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.worker_id = worker_id or os.getenv("WORKER_ID", "worker-1")
        self.concurrency = concurrency or int(os.getenv("WORKER_CONCURRENCY", "1"))

        self.redis_client: Optional[aioredis.Redis] = None
        self.running = False

        logger.info(
            f"IceStreams Worker initialized: worker_id={self.worker_id}, "
            f"concurrency={self.concurrency}, redis_url={self.redis_url}"
        )

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test the connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis: {self.redis_url}")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection to Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def ensure_consumer_group(self) -> None:
        """Create consumer group if it doesn't exist."""
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")

        try:
            await self.redis_client.xgroup_create(
                self.STREAM_NAME,
                self.CONSUMER_GROUP,
                id="0",
                mkstream=True,
            )
            logger.info(
                f"Consumer group '{self.CONSUMER_GROUP}' created for stream '{self.STREAM_NAME}'"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{self.CONSUMER_GROUP}' already exists")
            else:
                raise

    async def process_message(self, message_id: str, data: Dict[str, Any]) -> bool:
        """
        Process a single task message from the stream.

        Args:
            message_id: Redis stream message ID
            data: Message data containing task information

        Returns:
            True if processing was successful, False otherwise
        """
        try:
            logger.info(f"Processing message {message_id}: {data}")

            # Extract task information
            task_type = data.get("type", "unknown")
            task_payload = data.get("payload", {})

            # Route to appropriate handler
            if task_type == "playbook_execute":
                await self._handle_playbook_execute(message_id, task_payload)
            elif task_type == "health_check":
                await self._handle_health_check(message_id, task_payload)
            else:
                logger.warning(f"Unknown task type: {task_type}")

            # Acknowledge message (mark as processed)
            if self.redis_client:
                await self.redis_client.xack(
                    self.STREAM_NAME,
                    self.CONSUMER_GROUP,
                    message_id,
                )
            logger.info(f"Message {message_id} acknowledged")
            return True

        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
            return False

    async def _handle_playbook_execute(
        self, message_id: str, payload: Dict[str, Any]
    ) -> None:
        """
        Handle playbook execution task.

        Args:
            message_id: Redis stream message ID
            payload: Task payload containing playbook details
        """
        logger.info(f"Executing playbook from message {message_id}")
        logger.debug(f"Playbook payload: {payload}")

        playbook_id = payload.get("playbook_id")
        if not playbook_id:
            logger.error("Missing playbook_id in payload")
            await self._publish_error(message_id, "Missing playbook_id")
            return

        # Generate unique execution ID
        execution_id = payload.get("execution_id") or str(uuid.uuid4())

        try:
            # Extract playbook data from payload
            playbook_data = payload.get("playbook_data", {})
            if not playbook_data:
                logger.error("Missing playbook_data in payload")
                await self._publish_error(message_id, "Missing playbook_data")
                return

            # Create executor instance
            if not self.redis_client:
                raise RuntimeError("Redis client not initialized")

            executor = PlaybookExecutor(
                redis_client=self.redis_client,
                execution_id=execution_id,
                playbook_id=playbook_id,
                node_timeout_seconds=float(payload.get("node_timeout_seconds", 30.0)),
            )

            # Publish execution started status
            await self._publish_status(
                execution_id,
                {
                    "status": "running",
                    "playbook_id": playbook_id,
                    "message_id": message_id,
                    "started_at": asyncio.get_event_loop().time(),
                },
            )

            # Execute the playbook
            result: ExecutionResult = await executor.execute(playbook_data)

            # Publish execution result
            await self._publish_result(execution_id, result)

            logger.info(
                f"Playbook execution completed: execution_id={execution_id}, "
                f"success={result.success}, "
                f"completed_nodes={len(result.completed_nodes)}, "
                f"failed_nodes={len(result.failed_nodes)}"
            )

        except Exception as e:
            logger.error(f"Error executing playbook {playbook_id}: {e}", exc_info=True)
            await self._publish_error(
                execution_id, f"Playbook execution error: {str(e)}"
            )

    async def _handle_health_check(
        self, message_id: str, payload: Dict[str, Any]
    ) -> None:
        """
        Handle health check task.

        Args:
            message_id: Redis stream message ID
            payload: Task payload containing health check details
        """
        logger.info(f"Performing health check from message {message_id}")
        logger.debug(f"Health check payload: {payload}")

        # Simulate health check
        await asyncio.sleep(0.05)
        logger.info("Health check completed")

    async def consumer_loop(self) -> None:
        """Main message processing loop."""
        if not self.redis_client:
            raise RuntimeError("Redis client not initialized")

        logger.info(
            f"Starting consumer loop for worker '{self.worker_id}' "
            f"on stream '{self.STREAM_NAME}' with concurrency {self.concurrency}"
        )
        self.running = True

        pending_tasks = set()

        try:
            while self.running:
                try:
                    # Read messages from stream
                    messages = await self.redis_client.xreadgroup(
                        {self.STREAM_NAME: ">"},
                        self.CONSUMER_GROUP,
                        self.worker_id,
                        count=self.concurrency,
                        block=self.BLOCK_MS,
                    )

                    if messages:
                        for stream_name, stream_messages in messages:
                            for message_id, message_data in stream_messages:
                                # Create async task for processing
                                task = asyncio.create_task(
                                    self.process_message(message_id, message_data)
                                )
                                pending_tasks.add(task)

                                # Remove completed tasks from the set
                                pending_tasks = {
                                    t for t in pending_tasks if not t.done()
                                }

                                # Limit concurrent tasks
                                while len(pending_tasks) >= self.concurrency:
                                    _, pending_tasks = await asyncio.wait(
                                        pending_tasks,
                                        return_when=asyncio.FIRST_COMPLETED,
                                    )

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error in consumer loop: {e}", exc_info=True)
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Consumer loop interrupted")
        finally:
            self.running = False
            # Wait for all pending tasks to complete
            if pending_tasks:
                logger.info(
                    f"Waiting for {len(pending_tasks)} pending tasks to complete..."
                )
                await asyncio.gather(*pending_tasks, return_exceptions=True)

    async def run(self) -> None:
        """Run the worker service."""
        try:
            await self.connect()
            await self.ensure_consumer_group()
            await self.consumer_loop()
        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            sys.exit(1)
        finally:
            await self.disconnect()

    async def shutdown(self) -> None:
        """Gracefully shutdown the worker."""
        logger.info("Shutting down worker...")
        self.running = False

    async def _publish_status(
        self, execution_id: str, status_data: Dict[str, Any]
    ) -> None:
        """
        Publish execution status update to Redis Stream.

        Args:
            execution_id: Unique execution identifier
            status_data: Status information to publish
        """
        if not self.redis_client:
            return

        try:
            stream_name = f"icestreams:executions:{execution_id}:status"
            await self.redis_client.xadd(
                stream_name,
                {
                    "event": "status_update",
                    "data": json.dumps(status_data),
                },
                maxlen=100,
            )
            logger.debug(f"Published status for execution {execution_id}")
        except Exception as e:
            logger.error(f"Failed to publish status: {e}")

    async def _publish_result(self, execution_id: str, result: ExecutionResult) -> None:
        """
        Publish execution result to Redis Stream.

        Args:
            execution_id: Unique execution identifier
            result: Execution result to publish
        """
        if not self.redis_client:
            return

        try:
            stream_name = f"icestreams:executions:{execution_id}:result"
            await self.redis_client.xadd(
                stream_name,
                {
                    "event": "execution_complete",
                    "data": json.dumps(result.to_dict()),
                },
                maxlen=10,
            )
            logger.info(f"Published result for execution {execution_id}")
        except Exception as e:
            logger.error(f"Failed to publish result: {e}")

    async def _publish_error(self, execution_id: str, error_message: str) -> None:
        """
        Publish execution error to Redis Stream.

        Args:
            execution_id: Unique execution identifier
            error_message: Error message to publish
        """
        if not self.redis_client:
            return

        try:
            stream_name = f"icestreams:executions:{execution_id}:status"
            await self.redis_client.xadd(
                stream_name,
                {
                    "event": "execution_error",
                    "data": json.dumps(
                        {
                            "status": "failed",
                            "error": error_message,
                        }
                    ),
                },
                maxlen=100,
            )
            logger.debug(f"Published error for execution {execution_id}")
        except Exception as e:
            logger.error(f"Failed to publish error: {e}")


async def main():
    """Main entry point for the worker service."""
    worker = IceStreamsWorker()

    # Handle signals for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler():
        asyncio.create_task(worker.shutdown())

    for sig in ("SIGTERM", "SIGINT"):
        loop.add_signal_handler(
            getattr(__import__("signal"), sig),
            signal_handler,
        )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
