"""Redis Streams client service for task queue management.

This module provides a client for publishing and consuming tasks via Redis Streams.
It handles task distribution between the Flask backend and worker services.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)

# Stream name for task queue
STREAM_NAME = "icestreams:tasks"
STREAM_STATUS_PREFIX = "icestreams:status:"


class RedisStreamsClient:
    """Client for interacting with Redis Streams for task queuing."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis Streams client.

        Args:
            redis_url: Redis connection URL. If not provided, will use app config.
        """
        self.redis_url = redis_url
        self._redis_conn: Optional[redis.Redis] = None

    def _get_redis_connection(self) -> redis.Redis:
        """Get or create Redis connection.

        Returns:
            Redis connection instance
        """
        if self._redis_conn is None:
            url = self.redis_url
            if url is None:
                # Try to get from Flask app config
                try:
                    from flask import current_app

                    url = current_app.config.get(
                        "REDIS_URL", "redis://localhost:6379/0"
                    )
                except RuntimeError:
                    # Flask app context not available
                    url = "redis://localhost:6379/0"

            self._redis_conn = redis.from_url(url, decode_responses=True)

        return self._redis_conn

    def publish_task(
        self,
        execution_id: str,
        playbook_id: str,
        input_data: Dict[str, Any],
    ) -> str:
        """Publish a task to the Redis Stream.

        This function queues a new task for the worker service to process.

        Args:
            execution_id: Unique identifier for this execution instance
            playbook_id: Identifier for the playbook to execute
            input_data: Dictionary of input data for the task

        Returns:
            Message ID from Redis Stream (format: timestamp-sequence)

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            # Prepare task payload
            task_payload = {
                "execution_id": execution_id,
                "playbook_id": playbook_id,
                "input_data": json.dumps(input_data),
                "created_at": datetime.utcnow().isoformat(),
                "status": "queued",
            }

            # Add to stream - Redis will auto-generate message ID if not provided
            message_id = conn.xadd(STREAM_NAME, task_payload)

            logger.info(
                f"Task published: execution_id={execution_id}, "
                f"playbook_id={playbook_id}, message_id={message_id}"
            )

            return message_id

        except redis.RedisError as e:
            logger.error(f"Failed to publish task to Redis Stream: {str(e)}")
            raise

    def get_task_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a task execution.

        Args:
            execution_id: Unique identifier for the execution instance

        Returns:
            Dictionary containing status information, or None if not found

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            # Get status from Redis hash
            status_key = f"{STREAM_STATUS_PREFIX}{execution_id}"
            status_data = conn.hgetall(status_key)

            if not status_data:
                logger.debug(f"No status found for execution_id={execution_id}")
                return None

            # Parse the stored data
            result = {
                "execution_id": execution_id,
                "status": status_data.get("status", "unknown"),
                "updated_at": status_data.get("updated_at"),
                "current_node": status_data.get("current_node"),
                "progress_percent": int(status_data.get("progress_percent", 0)),
                "error": status_data.get("error"),
                "result": None,
            }

            # Parse result if available
            if status_data.get("result"):
                try:
                    result["result"] = json.loads(status_data.get("result"))
                except (json.JSONDecodeError, TypeError):
                    result["result"] = status_data.get("result")

            logger.debug(f"Status retrieved for execution_id={execution_id}")
            return result

        except redis.RedisError as e:
            logger.error(
                f"Failed to get task status for execution_id={execution_id}: {str(e)}"
            )
            raise

    def publish_status_update(
        self,
        execution_id: str,
        node_id: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish a status update for an executing task.

        This function is typically called by worker services to report progress.

        Args:
            execution_id: Unique identifier for the execution instance
            node_id: Identifier for the current node being executed
            status: Current status (e.g., 'running', 'completed', 'failed')
            data: Optional dictionary with additional status data (progress, error, result)

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            if data is None:
                data = {}

            # Prepare status update
            status_key = f"{STREAM_STATUS_PREFIX}{execution_id}"
            update_data = {
                "execution_id": execution_id,
                "status": status,
                "current_node": node_id,
                "updated_at": datetime.utcnow().isoformat(),
                "progress_percent": data.get("progress_percent", 0),
            }

            # Add optional fields if present
            if "error" in data:
                update_data["error"] = str(data["error"])

            if "result" in data:
                update_data["result"] = (
                    json.dumps(data["result"])
                    if isinstance(data["result"], dict)
                    else str(data["result"])
                )

            # Update the hash
            conn.hset(status_key, mapping=update_data)

            # Set expiration (default 24 hours) to prevent unbounded storage
            conn.expire(status_key, 24 * 3600)

            logger.debug(
                f"Status updated: execution_id={execution_id}, "
                f"node_id={node_id}, status={status}"
            )

            # Also publish to a pub/sub channel for real-time updates
            self._publish_status_event(execution_id, status, node_id, data)

        except redis.RedisError as e:
            logger.error(
                f"Failed to publish status update for execution_id={execution_id}: {str(e)}"
            )
            raise

    def _publish_status_event(
        self,
        execution_id: str,
        status: str,
        node_id: str,
        data: Dict[str, Any],
    ) -> None:
        """Publish a status event to a pub/sub channel for real-time updates.

        Args:
            execution_id: Unique identifier for the execution instance
            status: Current status
            node_id: Current node identifier
            data: Additional status data
        """
        try:
            conn = self._get_redis_connection()

            channel = f"icestreams:events:{execution_id}"
            event_payload = {
                "execution_id": execution_id,
                "status": status,
                "node_id": node_id,
                "timestamp": datetime.utcnow().isoformat(),
                **data,
            }

            conn.publish(channel, json.dumps(event_payload))

        except redis.RedisError as e:
            logger.warning(f"Failed to publish status event: {str(e)}")

    def get_execution_events(
        self, execution_id: str, last_event_id: Optional[str] = None
    ) -> list:
        """Get recent events for an execution from the event stream.

        Args:
            execution_id: Unique identifier for the execution instance
            last_event_id: Optional message ID to start from (for pagination)

        Returns:
            List of event dictionaries
        """
        try:
            conn = self._get_redis_connection()

            # Read from execution-specific stream
            # This is for future use if we store events in a separate stream
            # For now, we rely on the status hash
            status = self.get_task_status(execution_id)

            if status:
                return [status]
            else:
                return []

        except redis.RedisError as e:
            logger.error(f"Failed to get execution events: {str(e)}")
            raise

    def delete_task_status(self, execution_id: str) -> None:
        """Delete status information for a completed task.

        Args:
            execution_id: Unique identifier for the execution instance

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            status_key = f"{STREAM_STATUS_PREFIX}{execution_id}"
            conn.delete(status_key)

            logger.debug(f"Status deleted for execution_id={execution_id}")

        except redis.RedisError as e:
            logger.error(
                f"Failed to delete task status for execution_id={execution_id}: {str(e)}"
            )
            raise

    def acknowledge_message(self, consumer_group: str, message_id: str) -> None:
        """Acknowledge a message in the stream (consumer group mode).

        Args:
            consumer_group: Name of the consumer group
            message_id: Message ID to acknowledge

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()
            conn.xack(STREAM_NAME, consumer_group, message_id)

            logger.debug(
                f"Message acknowledged: consumer_group={consumer_group}, id={message_id}"
            )

        except redis.RedisError as e:
            logger.error(f"Failed to acknowledge message: {str(e)}")
            raise

    def get_stream_info(self) -> Dict[str, Any]:
        """Get information about the task stream.

        Returns:
            Dictionary containing stream statistics

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            info = conn.xinfo_stream(STREAM_NAME)

            return {
                "stream_name": STREAM_NAME,
                "length": info.get("length", 0),
                "radix_tree_keys": info.get("radix_tree_keys", 0),
                "radix_tree_nodes": info.get("radix_tree_nodes", 0),
                "groups": info.get("groups", 0),
                "last_generated_id": info.get("last_generated_id"),
                "first_entry": info.get("first_entry"),
                "last_entry": info.get("last_entry"),
            }

        except redis.RedisError as e:
            logger.error(f"Failed to get stream info: {str(e)}")
            raise


# Global client instance
_redis_streams_client: Optional[RedisStreamsClient] = None


def get_redis_streams_client(redis_url: Optional[str] = None) -> RedisStreamsClient:
    """Get or create the global Redis Streams client.

    Args:
        redis_url: Optional Redis URL (uses app config if not provided)

    Returns:
        RedisStreamsClient instance
    """
    global _redis_streams_client

    if _redis_streams_client is None:
        _redis_streams_client = RedisStreamsClient(redis_url=redis_url)

    return _redis_streams_client


# Convenience functions for direct access
def publish_task(
    execution_id: str,
    playbook_id: str,
    input_data: Dict[str, Any],
) -> str:
    """Publish a task to Redis Streams.

    Args:
        execution_id: Unique identifier for this execution
        playbook_id: Identifier for the playbook to execute
        input_data: Dictionary of input data

    Returns:
        Message ID from Redis Stream
    """
    client = get_redis_streams_client()
    return client.publish_task(execution_id, playbook_id, input_data)


def get_task_status(execution_id: str) -> Optional[Dict[str, Any]]:
    """Get the current status of a task execution.

    Args:
        execution_id: Unique identifier for the execution

    Returns:
        Status dictionary or None if not found
    """
    client = get_redis_streams_client()
    return client.get_task_status(execution_id)


def publish_status_update(
    execution_id: str,
    node_id: str,
    status: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """Publish a status update for an executing task.

    Args:
        execution_id: Unique identifier for the execution
        node_id: Current node identifier
        status: Current status
        data: Optional additional status data
    """
    client = get_redis_streams_client()
    client.publish_status_update(execution_id, node_id, status, data)


# IceRuns-specific constants
ICERUNS_TASKS_STREAM = "iceruns:tasks"
ICERUNS_STATUS_PREFIX = "iceruns:status:"
ICERUNS_EVENTS_PREFIX = "iceruns:events:"

# IceFlows-specific constants
ICEFLOWS_TASKS_STREAM = "iceflows:tasks"
ICEFLOWS_STATUS_PREFIX = "iceflows:status:"
ICEFLOWS_EVENTS_PREFIX = "iceflows:events:"


class RedisStreams:
    """IceRuns-specific Redis Streams integration."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize RedisStreams for IceRuns.

        Args:
            redis_url: Redis connection URL. If not provided, uses app config.
        """
        self.redis_url = redis_url
        self._redis_conn: Optional[redis.Redis] = None

    def _get_redis_connection(self) -> redis.Redis:
        """Get or create Redis connection.

        Returns:
            Redis connection instance
        """
        if self._redis_conn is None:
            url = self.redis_url
            if url is None:
                try:
                    from flask import current_app

                    url = current_app.config.get(
                        "REDIS_URL", "redis://localhost:6379/0"
                    )
                except RuntimeError:
                    url = "redis://localhost:6379/0"

            self._redis_conn = redis.from_url(url, decode_responses=True)

        return self._redis_conn

    def publish_icerun_task(
        self,
        execution_id: str,
        function_id: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any],
    ) -> str:
        """Publish IceRun execution task to queue.

        Adds a task to the iceruns:tasks stream for worker consumption.

        Args:
            execution_id: Unique identifier for this execution
            function_id: Identifier for the IceRun function
            input_data: Input payload for the function
            config: Function configuration containing runtime, entrypoint, handler,
                   memory_limit_mb, timeout_seconds, cpu_limit, env_vars,
                   secrets, and package_key

        Returns:
            Message ID from Redis Stream (format: timestamp-sequence)

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            # Prepare task payload
            message = {
                "execution_id": execution_id,
                "function_id": function_id,
                "input_data": json.dumps(input_data),
                "config": json.dumps(
                    {
                        "runtime": config.get("runtime"),
                        "entrypoint": config.get("entrypoint"),
                        "handler": config.get("handler"),
                        "memory_limit_mb": config.get("memory_limit_mb"),
                        "timeout_seconds": config.get("timeout_seconds"),
                        "cpu_limit": config.get("cpu_limit"),
                        "env_vars": config.get("env_vars", {}),
                        "secrets": config.get("secrets", {}),
                        "package_key": config.get("package_key"),
                    }
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add to stream
            message_id = conn.xadd(ICERUNS_TASKS_STREAM, message)

            logger.info(
                f"IceRun task published: execution_id={execution_id}, "
                f"function_id={function_id}, message_id={message_id}"
            )

            return message_id

        except redis.RedisError as e:
            logger.error(f"Failed to publish IceRun task to Redis Stream: {str(e)}")
            raise

    def get_icerun_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get IceRun execution status from Redis hash.

        Retrieves the current status of an IceRun execution including status,
        started_at, progress, stdout, stderr, and error information.

        Args:
            execution_id: Unique identifier for the execution

        Returns:
            Dictionary containing status information, or None if not found.
            Keys: status, started_at, progress_percent, stdout, stderr, error,
                  worker_id

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            # Get status from Redis hash
            status_key = f"{ICERUNS_STATUS_PREFIX}{execution_id}"
            status_data = conn.hgetall(status_key)

            if not status_data:
                logger.debug(f"No status found for execution_id={execution_id}")
                return None

            # Parse the stored data
            result = {
                "execution_id": execution_id,
                "status": status_data.get("status", "unknown"),
                "started_at": status_data.get("started_at"),
                "progress_percent": int(status_data.get("progress_percent", 0)),
                "stdout": status_data.get("stdout", ""),
                "stderr": status_data.get("stderr", ""),
                "error": status_data.get("error"),
                "worker_id": status_data.get("worker_id"),
            }

            logger.debug(f"Status retrieved for execution_id={execution_id}")
            return result

        except redis.RedisError as e:
            logger.error(
                f"Failed to get IceRun status for execution_id={execution_id}: {str(e)}"
            )
            raise

    def publish_icerun_status_update(
        self,
        execution_id: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update IceRun execution status and publish to pub/sub.

        Updates the iceruns:status:{execution_id} hash and publishes an event
        to iceruns:events:{execution_id} channel for real-time updates.

        Args:
            execution_id: Unique identifier for the execution
            status: Current status (queued, running, completed, failed, timeout, cancelled)
            data: Optional dictionary with additional status data containing keys like:
                  progress_percent, stdout, stderr, error, worker_id, result

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            if data is None:
                data = {}

            # Prepare status update
            status_key = f"{ICERUNS_STATUS_PREFIX}{execution_id}"
            update_data = {
                "execution_id": execution_id,
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Add optional fields if present
            if "progress_percent" in data:
                update_data["progress_percent"] = str(data["progress_percent"])

            if "started_at" in data:
                update_data["started_at"] = data["started_at"]

            if "stdout" in data:
                update_data["stdout"] = data["stdout"]

            if "stderr" in data:
                update_data["stderr"] = data["stderr"]

            if "error" in data:
                update_data["error"] = str(data["error"])

            if "worker_id" in data:
                update_data["worker_id"] = data["worker_id"]

            if "result" in data:
                update_data["result"] = (
                    json.dumps(data["result"])
                    if isinstance(data["result"], dict)
                    else str(data["result"])
                )

            # Update the hash
            conn.hset(status_key, mapping=update_data)

            # Set expiration (24 hours) to prevent unbounded storage
            conn.expire(status_key, 24 * 3600)

            logger.debug(
                f"IceRun status updated: execution_id={execution_id}, status={status}"
            )

            # Publish to pub/sub channel for real-time updates
            channel = f"{ICERUNS_EVENTS_PREFIX}{execution_id}"
            event_payload = {
                "execution_id": execution_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                **data,
            }

            conn.publish(channel, json.dumps(event_payload))

        except redis.RedisError as e:
            logger.error(
                f"Failed to publish IceRun status update for execution_id={execution_id}: {str(e)}"
            )
            raise

    def subscribe_icerun_events(self, execution_id: str):
        """Subscribe to real-time IceRun execution events.

        Creates a Pub/Sub subscription to the iceruns:events:{execution_id}
        channel for receiving real-time status updates.

        Args:
            execution_id: Unique identifier for the execution

        Returns:
            Redis PubSub instance subscribed to the execution events channel.
            Call pubsub.listen() to iterate over incoming messages.

        Raises:
            redis.RedisError: If Redis operation fails
        """
        try:
            conn = self._get_redis_connection()

            channel = f"{ICERUNS_EVENTS_PREFIX}{execution_id}"
            pubsub = conn.pubsub()
            pubsub.subscribe(channel)

            logger.debug(f"Subscribed to IceRun events: {channel}")

            return pubsub

        except redis.RedisError as e:
            logger.error(
                f"Failed to subscribe to IceRun events for execution_id={execution_id}: {str(e)}"
            )
            raise
