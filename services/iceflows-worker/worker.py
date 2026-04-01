#!/usr/bin/env python3
"""
IceFlows Worker - Redis Streams-based CI/CD pipeline task processor.

This worker service consumes tasks from Redis Streams and processes CI/CD
pipeline operations including test execution, git merges, and IceStreams/IceRuns calls.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import redis
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError, RedisError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IceFlowsWorker:
    """Redis Streams-based task worker for IceCharts CI/CD pipeline automation."""

    STREAM_NAME = "iceflows:tasks"
    CONSUMER_GROUP = "iceflows-workers"
    BLOCK_MS = 1000  # Block for 1 second when reading from stream

    def __init__(
        self,
        redis_url: Optional[str] = None,
        worker_id: Optional[str] = None,
        concurrency: int = 1,
    ):
        """
        Initialize the IceFlows Worker.

        Args:
            redis_url: Redis connection URL (from REDIS_URL env var)
            worker_id: Unique identifier for this worker instance
            concurrency: Number of concurrent tasks to process
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.worker_id = worker_id or os.getenv("WORKER_ID", "iceflows-worker-1")
        self.concurrency = concurrency or int(os.getenv("WORKER_CONCURRENCY", "1"))

        self.redis_client: Optional[aioredis.Redis] = None
        self.running = False

        logger.info(
            f"IceFlows Worker initialized: worker_id={self.worker_id}, "
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
            if task_type == "pipeline_execute":
                await self._handle_pipeline_execute(message_id, task_payload)
            elif task_type == "run_tests":
                await self._handle_run_tests(message_id, task_payload)
            elif task_type == "run_merge":
                await self._handle_run_merge(message_id, task_payload)
            elif task_type == "run_calls":
                await self._handle_run_calls(message_id, task_payload)
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

    async def _handle_pipeline_execute(
        self, message_id: str, payload: Dict[str, Any]
    ) -> None:
        """
        Handle pipeline execution task.

        This executes the full CI/CD pipeline for a promotion flow.

        Args:
            message_id: Redis stream message ID
            payload: Task payload containing pipeline details
        """
        logger.info(f"Executing pipeline from message {message_id}")
        logger.debug(f"Pipeline payload: {payload}")

        flow_id = payload.get("flow_id")
        promotion_id = payload.get("promotion_id")
        config = payload.get("config", {})

        logger.info(
            f"Pipeline execution scheduled for flow_id={flow_id}, "
            f"promotion_id={promotion_id}"
        )

        # Simulate async pipeline work
        await asyncio.sleep(0.1)
        logger.info(f"Pipeline execution completed for promotion_id={promotion_id}")

    async def _handle_run_tests(self, message_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle test execution task.

        Runs tests for a specific stage in the pipeline.

        Args:
            message_id: Redis stream message ID
            payload: Task payload containing test configuration
        """
        logger.info(f"Running tests from message {message_id}")
        logger.debug(f"Test payload: {payload}")

        stage_id = payload.get("stage_id")
        test_configs = payload.get("test_configs", [])

        logger.info(f"Test execution started for stage_id={stage_id}")
        logger.info(f"Running {len(test_configs)} test(s)")

        # Simulate test execution
        await asyncio.sleep(0.15)
        logger.info(f"Test execution completed for stage_id={stage_id}")

    async def _handle_run_merge(self, message_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle git merge task.

        Performs a git merge between branches.

        Args:
            message_id: Redis stream message ID
            payload: Task payload containing merge configuration
        """
        logger.info(f"Running merge from message {message_id}")
        logger.debug(f"Merge payload: {payload}")

        source_branch = payload.get("source_branch")
        target_branch = payload.get("target_branch")
        commit_sha = payload.get("commit_sha")

        logger.info(
            f"Git merge initiated: {source_branch} -> {target_branch} "
            f"(commit: {commit_sha})"
        )

        # Simulate merge operation
        await asyncio.sleep(0.1)
        logger.info(f"Git merge completed successfully")

    async def _handle_run_calls(self, message_id: str, payload: Dict[str, Any]) -> None:
        """
        Handle external service call task.

        Executes IceStreams or IceRuns API calls as part of pipeline.

        Args:
            message_id: Redis stream message ID
            payload: Task payload containing call configuration
        """
        logger.info(f"Running external calls from message {message_id}")
        logger.debug(f"Calls payload: {payload}")

        call_configs = payload.get("call_configs", [])
        context = payload.get("context", {})

        logger.info(f"Executing {len(call_configs)} external call(s)")
        logger.debug(f"Execution context: {context}")

        # Simulate external service calls
        await asyncio.sleep(0.12)
        logger.info(f"External calls completed")

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


async def main():
    """Main entry point for the worker service."""
    worker = IceFlowsWorker()

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
