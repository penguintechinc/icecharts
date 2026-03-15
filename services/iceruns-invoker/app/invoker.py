"""Main invoker loop for IceRuns execution (OpenWhisk pattern)."""

import os
import sys
import io
import json
import socket
import tempfile
import zipfile
import tarfile
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import redis
import docker
from pydal import DAL
from app.container_pool import ContainerPool
from app.action_runtime import RuntimeManager
from app.metrics import MetricsRecorder, QUEUE_SIZE

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IceRunsInvoker:
    """Main worker process for executing IceRuns functions."""

    def __init__(self):
        """Initialize invoker with connections and config."""
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        self.db = self._get_db_connection()
        self.docker_client = docker.from_env()
        self.worker_id = f"worker-{socket.gethostname()}-{os.getpid()}"
        self.container_pool = ContainerPool(self.docker_client)
        self.concurrency = int(os.getenv('INVOKER_CONCURRENCY', '5'))

        logger.info(f"Invoker initialized: {self.worker_id}")

    def _get_db_connection(self) -> DAL:
        """Initialize PyDAL database connection."""
        db_type = os.getenv('DB_TYPE', 'postgres')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'icecharts')
        db_user = os.getenv('DB_USER', 'icecharts')
        db_pass = os.getenv('DB_PASSWORD', '')

        db_uri = f"{db_type}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        return DAL(
            db_uri,
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            migrate_enabled=False,
            check_reserved=['all'],
            lazy_tables=True
        )

    def run(self):
        """Main worker loop - consume tasks from Redis Streams."""
        logger.info(f"Starting worker loop with concurrency={self.concurrency}")

        # Create consumer group if not exists
        try:
            self.redis_client.xgroup_create('iceruns:tasks', 'iceruns-workers', id='0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            if 'BUSYGROUP' not in str(e):
                raise

        while True:
            try:
                # Update queue size metric
                queue_len = self.redis_client.xlen('iceruns:tasks')
                QUEUE_SIZE.set(queue_len)

                # Read from stream with blocking (timeout 5s)
                messages = self.redis_client.xreadgroup(
                    'iceruns-workers',
                    self.worker_id,
                    {'iceruns:tasks': '>'},
                    count=1,
                    block=5000
                )

                for stream_name, message_list in messages:
                    for message_id, data in message_list:
                        try:
                            # Decode byte strings
                            task_data = {k.decode() if isinstance(k, bytes) else k:
                                       v.decode() if isinstance(v, bytes) else v
                                       for k, v in data.items()}

                            self.process_task(task_data)
                            self.redis_client.xack('iceruns:tasks', 'iceruns-workers', message_id)
                        except Exception as e:
                            logger.error(f"Error processing task {message_id}: {e}")

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                continue

    def process_task(self, task_data: Dict[str, Any]):
        """Execute a single IceRun function."""
        execution_id = task_data['execution_id']
        function_id = task_data['function_id']
        config_json = task_data.get('config', '{}')
        input_json = task_data.get('input_data', '{}')

        config = json.loads(config_json) if isinstance(config_json, str) else config_json
        input_data = json.loads(input_json) if isinstance(input_json, str) else input_json

        temp_dir = None
        started_at = datetime.utcnow()
        runtime = config.get('runtime', 'unknown')

        # Record execution start
        MetricsRecorder.record_execution_start(self.worker_id)

        try:
            # Update status: running
            self._update_status(execution_id, 'running', {'worker_id': self.worker_id})

            # Download package from S3
            package_bytes = self._load_package(config['package_key'])

            # Extract package to temp dir
            temp_dir = self._extract_package(package_bytes, config.get('entrypoint', 'main.py'))

            # Select runtime
            runtime = RuntimeManager.get_runtime(config['runtime'])

            # Execute in sandboxed container
            result = runtime.execute(
                code_dir=temp_dir,
                entrypoint=config['entrypoint'],
                handler=config['handler'],
                input_data=input_data,
                env_vars=config.get('env_vars', {}),
                secrets=config.get('secrets', {}),
                memory_limit_mb=config.get('memory_limit_mb', 128),
                timeout_seconds=config.get('timeout_seconds', 60),
                cpu_limit=config.get('cpu_limit', 0.5),
                execution_id=execution_id,
            )

            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Store logs in S3 if large
            logs_key = None
            if len(result.get('stdout', '')) > 10000:
                logs_key = self._save_execution_logs(
                    execution_id,
                    result.get('stdout', '') + result.get('stderr', '')
                )

            # Update database
            status = 'completed' if result.get('exit_code', 1) == 0 else 'failed'
            self.db.executesql(
                """UPDATE iceruns_executions SET
                   status=?, output_json=?, stdout=?, stderr=?, exit_code=?,
                   completed_at=?, duration_ms=?, memory_used_mb=?, cpu_time_ms=?,
                   logs_key=?, container_id=?, worker_id=?
                   WHERE execution_id=?""",
                [
                    status,
                    json.dumps(result.get('output')),
                    result.get('stdout', '')[:10000],
                    result.get('stderr', '')[:10000],
                    result.get('exit_code', 1),
                    completed_at,
                    duration_ms,
                    result.get('memory_used_mb', 0),
                    result.get('cpu_time_ms', 0),
                    logs_key,
                    result.get('container_id', ''),
                    self.worker_id,
                    execution_id
                ]
            )
            self.db.commit()

            # Update status: completed
            self._update_status(execution_id, status, {
                'output': result.get('output'),
                'exit_code': result.get('exit_code', 1),
                'duration_ms': duration_ms
            })

            # Record metrics
            MetricsRecorder.record_execution_complete(
                runtime=runtime,
                status=status,
                duration_ms=duration_ms,
                memory_mb=result.get('memory_used_mb'),
                trigger_type=task_data.get('trigger_type', 'manual')
            )

            logger.info(f"Execution {execution_id} completed: {status}")

        except TimeoutError as e:
            # Record timeout error metric
            MetricsRecorder.record_execution_error(runtime=runtime, error_type='timeout')
            self._handle_timeout(execution_id, str(e))
        except Exception as e:
            # Record general error metric
            error_type = type(e).__name__
            MetricsRecorder.record_execution_error(runtime=runtime, error_type=error_type)
            self._handle_error(execution_id, e)
        finally:
            # Record execution end
            MetricsRecorder.record_execution_end(self.worker_id)
            # Cleanup
            if temp_dir:
                self._cleanup(temp_dir)

    def _load_package(self, package_key: str) -> bytes:
        """Download function package from S3/MinIO."""
        # Stub - implement S3 download
        logger.warning(f"S3 download not implemented for {package_key}")
        return b""

    def _extract_package(self, package_bytes: bytes, entrypoint: str) -> str:
        """Extract package to temp directory."""
        temp_dir = tempfile.mkdtemp(prefix='icerun_')

        if not package_bytes:
            # Create minimal structure
            os.makedirs(temp_dir, exist_ok=True)
            return temp_dir

        try:
            # Try zip first
            with zipfile.ZipFile(io.BytesIO(package_bytes)) as zf:
                zf.extractall(temp_dir)
        except zipfile.BadZipFile:
            try:
                # Try tar.gz
                with tarfile.open(fileobj=io.BytesIO(package_bytes)) as tf:
                    tf.extractall(temp_dir)
            except tarfile.TarError:
                # Single file - write directly
                with open(os.path.join(temp_dir, entrypoint), 'wb') as f:
                    f.write(package_bytes)

        return temp_dir

    def _save_execution_logs(self, execution_id: str, logs: str) -> str:
        """Upload full execution logs to S3."""
        logs_key = f"iceruns/logs/{execution_id}.log"
        # Stub - implement S3 upload
        logger.warning(f"S3 upload not implemented for {logs_key}")
        return logs_key

    def _update_status(self, execution_id: str, status: str, data: Dict[str, Any]):
        """Update IceRun execution status and publish to pub/sub."""
        # Update hash
        status_data = {
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            **data
        }
        self.redis_client.hset(f'iceruns:status:{execution_id}', mapping=status_data)
        self.redis_client.expire(f'iceruns:status:{execution_id}', 86400)  # 24 hours

        # Publish event
        self.redis_client.publish(
            f'iceruns:events:{execution_id}',
            json.dumps(status_data)
        )

    def _handle_timeout(self, execution_id: str, error_msg: str):
        """Handle execution timeout."""
        self.db.executesql(
            """UPDATE iceruns_executions SET
               status=?, error_message=?, completed_at=?
               WHERE execution_id=?""",
            ['timeout', error_msg, datetime.utcnow(), execution_id]
        )
        self.db.commit()
        self._update_status(execution_id, 'timeout', {'error': error_msg})
        logger.warning(f"Execution {execution_id} timed out: {error_msg}")

    def _handle_error(self, execution_id: str, error: Exception):
        """Handle execution error."""
        error_msg = str(error)
        self.db.executesql(
            """UPDATE iceruns_executions SET
               status=?, error_message=?, completed_at=?
               WHERE execution_id=?""",
            ['failed', error_msg, datetime.utcnow(), execution_id]
        )
        self.db.commit()
        self._update_status(execution_id, 'failed', {'error': error_msg})
        logger.error(f"Execution {execution_id} failed: {error_msg}")

    def _cleanup(self, temp_dir: str):
        """Cleanup temporary directory."""
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Cleanup failed for {temp_dir}: {e}")


def main():
    """Entry point."""
    import threading
    from app.metrics_server import run_metrics_server

    # Start metrics server in background thread
    metrics_port = int(os.getenv('METRICS_PORT', '8081'))
    metrics_thread = threading.Thread(
        target=run_metrics_server,
        kwargs={'host': '0.0.0.0', 'port': metrics_port},
        daemon=True
    )
    metrics_thread.start()
    logger.info(f"Metrics server started on port {metrics_port}")

    # Start main invoker
    invoker = IceRunsInvoker()
    invoker.run()


if __name__ == '__main__':
    main()
