"""Prometheus metrics for IceRuns Invoker service."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import os

# Metric 1: Total executions counter
EXECUTIONS_TOTAL = Counter(
    'iceruns_executions_total',
    'Total IceRuns executions',
    ['runtime', 'status', 'trigger_type']
)

# Metric 2: Execution duration histogram
EXECUTION_DURATION = Histogram(
    'iceruns_execution_duration_seconds',
    'IceRuns execution duration in seconds',
    ['runtime', 'status'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# Metric 3: Execution memory usage histogram
EXECUTION_MEMORY = Histogram(
    'iceruns_execution_memory_mb',
    'IceRuns execution memory usage in MB',
    ['runtime'],
    buckets=[64, 128, 256, 512, 1024, 2048, 4096]
)

# Metric 4: Active executions gauge
ACTIVE_EXECUTIONS = Gauge(
    'iceruns_active_executions',
    'Number of currently running executions',
    ['worker_id']
)

# Metric 5: Task queue size gauge
QUEUE_SIZE = Gauge(
    'iceruns_queue_size',
    'Number of tasks in execution queue'
)

# Metric 6: Execution errors counter
EXECUTION_ERRORS = Counter(
    'iceruns_execution_errors_total',
    'Total IceRuns execution errors',
    ['runtime', 'error_type']
)


class MetricsRecorder:
    """Helper class to record metrics with consistent labels."""

    @staticmethod
    def record_execution_start(worker_id: str):
        """Record execution start."""
        ACTIVE_EXECUTIONS.labels(worker_id=worker_id).inc()

    @staticmethod
    def record_execution_end(worker_id: str):
        """Record execution end."""
        ACTIVE_EXECUTIONS.labels(worker_id=worker_id).dec()

    @staticmethod
    def record_execution_complete(runtime: str, status: str, duration_ms: int,
                                  memory_mb: int = None, trigger_type: str = 'manual'):
        """Record completed execution metrics."""
        duration_seconds = duration_ms / 1000.0

        # Record counters and histograms
        EXECUTIONS_TOTAL.labels(
            runtime=runtime,
            status=status,
            trigger_type=trigger_type
        ).inc()

        EXECUTION_DURATION.labels(
            runtime=runtime,
            status=status
        ).observe(duration_seconds)

        if memory_mb is not None:
            EXECUTION_MEMORY.labels(runtime=runtime).observe(memory_mb)

    @staticmethod
    def record_execution_error(runtime: str, error_type: str):
        """Record execution error."""
        EXECUTION_ERRORS.labels(
            runtime=runtime,
            error_type=error_type
        ).inc()

    @staticmethod
    def set_queue_size(size: int):
        """Set current queue size."""
        QUEUE_SIZE.set(size)

    @staticmethod
    def get_metrics_output() -> bytes:
        """Generate Prometheus metrics output."""
        return generate_latest()
