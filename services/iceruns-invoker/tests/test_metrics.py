"""Tests for MetricsRecorder - Prometheus metrics for IceRuns Invoker."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))


class TestMetricsRecorder:
    """Tests for MetricsRecorder static methods."""

    def test_record_execution_start_increments_gauge(self):
        """record_execution_start increments ACTIVE_EXECUTIONS gauge."""
        from app.metrics import MetricsRecorder, ACTIVE_EXECUTIONS

        mock_labels = MagicMock()
        with patch.object(ACTIVE_EXECUTIONS, "labels", return_value=mock_labels) as mock_lbl:
            MetricsRecorder.record_execution_start("worker-1")
            mock_lbl.assert_called_once_with(worker_id="worker-1")
        mock_labels.inc.assert_called_once()

    def test_record_execution_end_decrements_gauge(self):
        """record_execution_end decrements ACTIVE_EXECUTIONS gauge."""
        from app.metrics import MetricsRecorder, ACTIVE_EXECUTIONS

        mock_labels = MagicMock()
        with patch.object(ACTIVE_EXECUTIONS, "labels", return_value=mock_labels):
            MetricsRecorder.record_execution_end("worker-1")
        mock_labels.dec.assert_called_once()

    def test_record_execution_complete_increments_counter(self):
        """record_execution_complete increments EXECUTIONS_TOTAL."""
        from app.metrics import MetricsRecorder, EXECUTIONS_TOTAL

        mock_labels = MagicMock()
        with patch.object(EXECUTIONS_TOTAL, "labels", return_value=mock_labels) as mock_lbl:
            with patch("app.metrics.EXECUTION_DURATION") as mock_dur:
                mock_dur.labels.return_value = MagicMock()
                MetricsRecorder.record_execution_complete(
                    runtime="python3.13",
                    status="completed",
                    duration_ms=1500,
                    trigger_type="manual",
                )
            mock_lbl.assert_called_once_with(
                runtime="python3.13", status="completed", trigger_type="manual"
            )
        mock_labels.inc.assert_called_once()

    def test_record_execution_complete_observes_duration(self):
        """record_execution_complete observes execution duration histogram."""
        from app.metrics import MetricsRecorder, EXECUTION_DURATION

        mock_labels = MagicMock()
        with patch.object(EXECUTION_DURATION, "labels", return_value=mock_labels):
            with patch("app.metrics.EXECUTIONS_TOTAL") as mock_total:
                mock_total.labels.return_value = MagicMock()
                MetricsRecorder.record_execution_complete(
                    runtime="nodejs",
                    status="completed",
                    duration_ms=2000,
                )
        # duration_ms=2000 => 2.0 seconds
        mock_labels.observe.assert_called_once_with(2.0)

    def test_record_execution_complete_observes_memory_when_provided(self):
        """record_execution_complete observes memory histogram when memory_mb given."""
        from app.metrics import MetricsRecorder, EXECUTION_MEMORY

        mock_labels = MagicMock()
        with patch.object(EXECUTION_MEMORY, "labels", return_value=mock_labels):
            with patch("app.metrics.EXECUTIONS_TOTAL") as mock_total, \
                 patch("app.metrics.EXECUTION_DURATION") as mock_dur:
                mock_total.labels.return_value = MagicMock()
                mock_dur.labels.return_value = MagicMock()
                MetricsRecorder.record_execution_complete(
                    runtime="python3.13",
                    status="completed",
                    duration_ms=500,
                    memory_mb=128,
                )
        mock_labels.observe.assert_called_once_with(128)

    def test_record_execution_error_increments_error_counter(self):
        """record_execution_error increments EXECUTION_ERRORS counter."""
        from app.metrics import MetricsRecorder, EXECUTION_ERRORS

        mock_labels = MagicMock()
        with patch.object(EXECUTION_ERRORS, "labels", return_value=mock_labels) as mock_lbl:
            MetricsRecorder.record_execution_error(runtime="go", error_type="timeout")
            mock_lbl.assert_called_once_with(runtime="go", error_type="timeout")
        mock_labels.inc.assert_called_once()

    def test_set_queue_size(self):
        """set_queue_size sets QUEUE_SIZE gauge."""
        from app.metrics import MetricsRecorder, QUEUE_SIZE

        with patch.object(QUEUE_SIZE, "set") as mock_set:
            MetricsRecorder.set_queue_size(42)
        mock_set.assert_called_once_with(42)

    def test_get_metrics_output_returns_bytes(self):
        """get_metrics_output returns bytes for Prometheus scraping."""
        from app.metrics import MetricsRecorder
        output = MetricsRecorder.get_metrics_output()
        assert isinstance(output, bytes)
        assert len(output) > 0
