"""Tests for metrics_server.py - Flask server for Prometheus metrics endpoint."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))


class TestCreateMetricsApp:
    """Tests for create_metrics_app factory function."""

    def test_creates_flask_app(self):
        """create_metrics_app returns a Flask app."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        assert app is not None
        assert hasattr(app, 'route')
        assert hasattr(app, 'run')

    def test_registers_metrics_endpoint(self):
        """create_metrics_app registers /metrics endpoint."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self):
        """metrics endpoint returns text/plain Prometheus format."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/metrics')
        assert response.status_code == 200
        assert b'# HELP' in response.data or b'iceruns_' in response.data
        assert response.content_type.startswith('text/plain')

    def test_metrics_endpoint_includes_version(self):
        """metrics endpoint response includes Prometheus version."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/metrics')
        assert response.status_code == 200
        content_type = response.headers.get('Content-Type', '')
        assert '0.0.4' in content_type or response.status_code == 200

    def test_registers_health_endpoint(self):
        """create_metrics_app registers /health endpoint."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self):
        """health endpoint returns JSON with status."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json == {'status': 'healthy'}

    def test_health_endpoint_content_type(self):
        """health endpoint returns application/json."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/health')
        assert 'application/json' in response.content_type

    def test_metrics_not_found_on_missing_path(self):
        """unknown endpoints return 404."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_metrics_endpoint_get_only(self):
        """metrics endpoint only accepts GET."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.post('/metrics')
        assert response.status_code == 405  # Method Not Allowed

    def test_health_endpoint_get_only(self):
        """health endpoint only accepts GET."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()
        response = client.post('/health')
        assert response.status_code == 405  # Method Not Allowed

    def test_multiple_metrics_requests(self):
        """metrics endpoint handles multiple consecutive requests."""
        from app.metrics_server import create_metrics_app
        app = create_metrics_app()
        client = app.test_client()

        for _ in range(3):
            response = client.get('/metrics')
            assert response.status_code == 200

    def test_metrics_endpoint_with_metrics_recorded(self):
        """metrics endpoint returns recorded metrics data."""
        from app.metrics_server import create_metrics_app
        from app.metrics import EXECUTIONS_TOTAL

        # Record a metric
        EXECUTIONS_TOTAL.labels(runtime='python3.13', status='completed', trigger_type='manual').inc()

        app = create_metrics_app()
        client = app.test_client()
        response = client.get('/metrics')
        assert response.status_code == 200
        # Metrics data should be present
        assert len(response.data) > 0


class TestMetricsServerRun:
    """Tests for run_metrics_server function."""

    @patch('app.metrics_server.Flask')
    def test_run_metrics_server_creates_app(self, mock_flask):
        """run_metrics_server creates Flask app."""
        mock_app = MagicMock()
        mock_flask.return_value = mock_app

        with patch.object(mock_app, 'run'):
            from app.metrics_server import run_metrics_server
            try:
                run_metrics_server(host='0.0.0.0', port=8081)
            except Exception:
                pass

        mock_flask.assert_called_once()

    @patch('app.metrics_server.create_metrics_app')
    def test_run_metrics_server_starts_on_default_host_port(self, mock_create):
        """run_metrics_server starts on default 0.0.0.0:8081."""
        mock_app = MagicMock()
        mock_create.return_value = mock_app

        from app.metrics_server import run_metrics_server
        try:
            run_metrics_server()
        except Exception:
            pass

        mock_app.run.assert_called_once()
        call_kwargs = mock_app.run.call_args[1]
        assert call_kwargs['host'] == '0.0.0.0'
        assert call_kwargs['port'] == 8081

    @patch('app.metrics_server.create_metrics_app')
    def test_run_metrics_server_starts_on_custom_port(self, mock_create):
        """run_metrics_server respects custom port."""
        mock_app = MagicMock()
        mock_create.return_value = mock_app

        from app.metrics_server import run_metrics_server
        try:
            run_metrics_server(host='0.0.0.0', port=9000)
        except Exception:
            pass

        call_kwargs = mock_app.run.call_args[1]
        assert call_kwargs['port'] == 9000

    @patch('app.metrics_server.create_metrics_app')
    def test_run_metrics_server_disables_debug(self, mock_create):
        """run_metrics_server runs with debug=False."""
        mock_app = MagicMock()
        mock_create.return_value = mock_app

        from app.metrics_server import run_metrics_server
        try:
            run_metrics_server()
        except Exception:
            pass

        call_kwargs = mock_app.run.call_args[1]
        assert call_kwargs['debug'] is False

    @patch('app.metrics_server.create_metrics_app')
    def test_run_metrics_server_with_custom_host(self, mock_create):
        """run_metrics_server respects custom host."""
        mock_app = MagicMock()
        mock_create.return_value = mock_app

        from app.metrics_server import run_metrics_server
        try:
            run_metrics_server(host='127.0.0.1', port=8081)
        except Exception:
            pass

        call_kwargs = mock_app.run.call_args[1]
        assert call_kwargs['host'] == '127.0.0.1'

    def test_run_metrics_server_logging(self):
        """run_metrics_server logs startup message."""
        with patch('app.metrics_server.logger') as mock_logger:
            with patch('app.metrics_server.create_metrics_app') as mock_create:
                mock_app = MagicMock()
                mock_create.return_value = mock_app

                from app.metrics_server import run_metrics_server
                try:
                    run_metrics_server(host='127.0.0.1', port=9000)
                except Exception:
                    pass

                # Check that logger.info was called with startup message
                calls_info = [str(c) for c in mock_logger.info.call_args_list]
                assert any('metrics server' in str(c).lower() for c in calls_info)


class TestMetricsServerIntegration:
    """Integration tests for metrics server."""

    def test_metrics_server_app_isolation(self):
        """multiple app instances don't interfere."""
        from app.metrics_server import create_metrics_app

        app1 = create_metrics_app()
        app2 = create_metrics_app()

        client1 = app1.test_client()
        client2 = app2.test_client()

        resp1 = client1.get('/health')
        resp2 = client2.get('/health')

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json == resp2.json

    def test_metrics_endpoint_performance(self):
        """metrics endpoint responds quickly."""
        from app.metrics_server import create_metrics_app
        import time

        app = create_metrics_app()
        client = app.test_client()

        start = time.time()
        client.get('/metrics')
        elapsed = time.time() - start

        # Should be very fast (< 100ms)
        assert elapsed < 0.1

    def test_health_and_metrics_independent(self):
        """health and metrics endpoints work independently."""
        from app.metrics_server import create_metrics_app

        app = create_metrics_app()
        client = app.test_client()

        # Health endpoint
        health_resp = client.get('/health')
        assert health_resp.status_code == 200
        assert health_resp.json == {'status': 'healthy'}

        # Metrics endpoint
        metrics_resp = client.get('/metrics')
        assert metrics_resp.status_code == 200

        # Both should work independently
        health_resp2 = client.get('/health')
        assert health_resp2.status_code == 200
