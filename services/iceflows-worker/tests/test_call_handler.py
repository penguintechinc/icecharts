"""Tests for CallHandler - IceStreams and IceRuns trigger orchestration."""

import os
import sys
import time
from unittest.mock import MagicMock, call, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from call_handler import CallHandler, CallResult


@pytest.fixture
def mock_session():
    """Mock requests.Session."""
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json.return_value = {"execution_id": "exec-abc"}
    session.post.return_value = response
    session.get.return_value = response
    return session


@pytest.fixture
def handler(mock_session):
    """Create CallHandler with mocked session."""
    with patch("call_handler.requests.Session", return_value=mock_session):
        h = CallHandler(api_base_url="http://api:5000", api_token="test-jwt")
        h.session = mock_session
        return h


class TestCallHandlerInit:
    """Tests for CallHandler initialization."""

    def test_constructor_creates_session_with_auth(self, mock_session):
        """Constructor creates session with Bearer token header."""
        with patch(
            "call_handler.requests.Session", return_value=mock_session
        ) as mock_cls:
            mock_session.headers = MagicMock()
            mock_session.headers.update = MagicMock()
            h = CallHandler(api_base_url="http://api:5000", api_token="my-token")
        mock_cls.assert_called_once()
        # The session headers.update should be called with Authorization
        update_calls = mock_session.headers.update.call_args_list
        auth_set = any("Authorization" in str(c) for c in update_calls)
        assert auth_set

    def test_constructor_strips_trailing_slash(self, mock_session):
        """api_base_url trailing slash is stripped."""
        with patch("call_handler.requests.Session", return_value=mock_session):
            h = CallHandler(api_base_url="http://api:5000/", api_token="tok")
        assert h.api_base_url == "http://api:5000"

    def test_constructor_stores_timeout(self, mock_session):
        """Timeout is stored correctly."""
        with patch("call_handler.requests.Session", return_value=mock_session):
            h = CallHandler(
                api_base_url="http://api:5000", api_token="tok", timeout_seconds=120
            )
        assert h.timeout_seconds == 120


class TestTriggerIcestreams:
    """Tests for _trigger_icestreams."""

    def test_trigger_icestreams_posts_correct_url(self, handler, mock_session):
        """_trigger_icestreams POSTs to correct playbook execute endpoint."""
        result = handler._trigger_icestreams("playbook-123", {"key": "val"})
        mock_session.post.assert_called_once()
        call_url = mock_session.post.call_args[0][0]
        assert "/api/v1/playbooks/playbook-123/execute" in call_url

    def test_trigger_icestreams_returns_execution_id(self, handler, mock_session):
        """_trigger_icestreams returns dict with execution_id."""
        result = handler._trigger_icestreams("pb-1", {})
        assert result["execution_id"] == "exec-abc"

    def test_trigger_icestreams_raises_on_missing_execution_id(
        self, handler, mock_session
    ):
        """_trigger_icestreams raises ValueError if execution_id absent."""
        mock_session.post.return_value.json.return_value = {}
        with pytest.raises(ValueError, match="missing execution_id"):
            handler._trigger_icestreams("pb-1", {})


class TestTriggerIceruns:
    """Tests for _trigger_iceruns."""

    def test_trigger_iceruns_posts_correct_url(self, handler, mock_session):
        """_trigger_iceruns POSTs to correct function invoke endpoint."""
        result = handler._trigger_iceruns("func-456", {"param": "val"})
        mock_session.post.assert_called_once()
        call_url = mock_session.post.call_args[0][0]
        assert "/api/v1/iceruns/functions/func-456/invoke" in call_url

    def test_trigger_iceruns_returns_execution_id(self, handler, mock_session):
        """_trigger_iceruns returns dict with execution_id."""
        result = handler._trigger_iceruns("fn-1", {})
        assert result["execution_id"] == "exec-abc"


class TestPollExecutionStatus:
    """Tests for _poll_execution_status."""

    def test_poll_until_completed(self, handler, mock_session):
        """Polling returns status=completed when API reports completed."""
        mock_session.get.return_value.json.return_value = {
            "status": "completed",
            "output": {"result": "ok"},
            "error_message": None,
        }
        result = handler._poll_execution_status("exec-1", "icestreams", timeout=30)
        assert result["status"] == "completed"
        assert result["output"] == {"result": "ok"}

    def test_poll_timeout(self, handler, mock_session):
        """Polling returns timeout status when elapsed exceeds timeout."""
        mock_session.get.return_value.json.return_value = {"status": "running"}
        with patch("time.time") as mock_time, patch("time.sleep"):
            # Simulate timeout immediately
            mock_time.side_effect = [0, 100, 100, 100]
            result = handler._poll_execution_status("exec-1", "icestreams", timeout=5)
        assert result["status"] == "timeout"

    def test_poll_exponential_backoff(self, handler, mock_session):
        """Polling uses increasing interval between checks."""
        statuses = [
            {"status": "running"},
            {"status": "running"},
            {"status": "completed", "output": None},
        ]
        mock_session.get.return_value.json.side_effect = statuses
        sleep_calls = []
        with patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)):
            with patch("time.time", side_effect=[0, 0.1, 0.2, 0.3, 0.4, 0.5]):
                result = handler._poll_execution_status(
                    "exec-1", "icestreams", timeout=60
                )
        # Should have slept at least once
        assert len(sleep_calls) >= 1
        # Intervals should be non-decreasing (exponential backoff)
        for i in range(1, len(sleep_calls)):
            assert sleep_calls[i] >= sleep_calls[i - 1]

    def test_poll_iceruns_endpoint(self, handler, mock_session):
        """Polling uses correct endpoint for iceruns call_type."""
        mock_session.get.return_value.json.return_value = {
            "status": "completed",
            "output": None,
        }
        handler._poll_execution_status("exec-1", "iceruns", timeout=30)
        call_url = mock_session.get.call_args[0][0]
        assert "/api/v1/iceruns/executions/exec-1" in call_url


class TestRenderTemplate:
    """Tests for _render_template."""

    def test_render_simple_string(self, handler):
        """{{var}} substitution in string."""
        result = handler._render_template("Hello {{name}}", {"name": "World"})
        assert result == "Hello World"

    def test_render_nested_dict(self, handler):
        """Template rendering recurses into dicts."""
        template = {"greeting": "Hello {{name}}", "nested": {"key": "{{val}}"}}
        result = handler._render_template(template, {"name": "Alice", "val": "42"})
        assert result["greeting"] == "Hello Alice"
        assert result["nested"]["key"] == "42"

    def test_render_list_items(self, handler):
        """Template rendering recurses into lists."""
        template = ["{{a}}", "{{b}}", "static"]
        result = handler._render_template(template, {"a": "x", "b": "y"})
        assert result == ["x", "y", "static"]

    def test_render_non_string_passthrough(self, handler):
        """Non-string/dict/list values are returned as-is."""
        assert handler._render_template(42, {}) == 42
        assert handler._render_template(True, {}) is True
        assert handler._render_template(None, {}) is None


class TestExecuteCalls:
    """Tests for execute_calls phase filtering."""

    def test_execute_calls_filters_by_trigger_phase(self, handler, mock_session):
        """execute_calls only runs calls matching trigger_phase."""
        mock_session.post.return_value.json.return_value = {"execution_id": "e1"}
        mock_session.get.return_value.json.return_value = {
            "status": "completed",
            "output": None,
        }
        configs = [
            {
                "call_id": "c1",
                "name": "Pre Merge Call",
                "call_type": "icestreams",
                "target_id": "pb-1",
                "input_template": {},
                "is_blocking": False,
                "trigger_on": "pre_merge",
            },
            {
                "call_id": "c2",
                "name": "Post Merge Call",
                "call_type": "icestreams",
                "target_id": "pb-2",
                "input_template": {},
                "is_blocking": False,
                "trigger_on": "post_merge",
            },
        ]
        results = handler.execute_calls(configs, {}, trigger_phase="post_merge")
        assert len(results) == 1
        assert results[0].call_id == "c2"

    def test_non_blocking_call_succeeds_on_trigger(self, handler, mock_session):
        """Non-blocking call is successful once triggered."""
        mock_session.post.return_value.json.return_value = {"execution_id": "exec-nb"}
        config = {
            "call_id": "nb-1",
            "name": "Non-blocking",
            "call_type": "icestreams",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        results = handler.execute_calls([config], {}, trigger_phase="post_merge")
        assert results[0].success is True
        assert results[0].status == "triggered"

    def test_blocking_call_polls_for_completion(self, handler, mock_session):
        """Blocking call polls for completion status."""
        # Use separate response objects for post and get to avoid
        # the second json.return_value overwriting the first
        post_response = MagicMock()
        post_response.json.return_value = {"execution_id": "exec-bl"}
        mock_session.post.return_value = post_response
        get_response = MagicMock()
        get_response.json.return_value = {
            "status": "completed",
            "output": {"ok": True},
        }
        mock_session.get.return_value = get_response
        config = {
            "call_id": "bl-1",
            "name": "Blocking",
            "call_type": "icestreams",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": True,
            "timeout_seconds": 30,
            "trigger_on": "post_merge",
        }
        results = handler.execute_calls([config], {}, trigger_phase="post_merge")
        assert results[0].success is True
        assert results[0].status == "completed"


class TestCallHandlerErrors:
    """Error path tests for call handler."""

    def test_http_timeout_returns_error_status(self, handler, mock_session):
        """When HTTP call times out, CallResult status is 'error'."""
        import requests

        mock_session.post.side_effect = requests.Timeout("Connection timeout")
        config = {
            "call_id": "err-timeout",
            "name": "Timeout Call",
            "call_type": "icestreams",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "API request failed" in result.error_message

    def test_http_connection_error_returns_error_status(self, handler, mock_session):
        """When HTTP connection fails, CallResult status is 'error'."""
        import requests

        mock_session.post.side_effect = requests.ConnectionError("Connection refused")
        config = {
            "call_id": "err-conn",
            "name": "Connection Error Call",
            "call_type": "iceruns",
            "target_id": "fn-1",
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "Connection refused" in result.error_message

    def test_http_auth_failure_raises_for_status(self, handler, mock_session):
        """When API returns 401/403, response.raise_for_status() raises."""
        import requests

        mock_session.post.return_value.status_code = 401
        mock_session.post.return_value.raise_for_status.side_effect = (
            requests.HTTPError("401 Unauthorized")
        )
        config = {
            "call_id": "err-auth",
            "name": "Auth Failure Call",
            "call_type": "icestreams",
            "target_id": "pb-2",
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "API request failed" in result.error_message

    def test_missing_target_id_returns_config_error(self, handler):
        """When target_id is missing, CallResult status is 'error'."""
        config = {
            "call_id": "err-no-target",
            "name": "Missing Target Call",
            "call_type": "icestreams",
            # target_id missing
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "target_id is required" in result.error_message

    def test_invalid_call_type_returns_config_error(self, handler):
        """When call_type is invalid, CallResult status is 'error'."""
        config = {
            "call_id": "err-bad-type",
            "name": "Bad Call Type",
            "call_type": "invalid_type",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "Invalid call_type" in result.error_message

    def test_polling_timeout_returns_timeout_status(self, handler, mock_session):
        """When polling times out, status is 'timeout'."""
        post_response = MagicMock()
        post_response.json.return_value = {"execution_id": "exec-timeout"}
        mock_session.post.return_value = post_response

        get_response = MagicMock()
        get_response.json.return_value = {"status": "running"}
        mock_session.get.return_value = get_response

        config = {
            "call_id": "bl-timeout",
            "name": "Blocking Timeout",
            "call_type": "icestreams",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": True,
            "timeout_seconds": 2,  # Very short timeout
            "trigger_on": "post_merge",
        }

        with patch("time.time") as mock_time, patch("time.sleep"):
            # Simulate time passing: start=0, each poll adds 10s
            mock_time.side_effect = [0, 0, 10, 10, 20, 20]
            result = handler.execute_call(config, {})

        assert result.success is False
        assert result.status == "timeout"
        assert "did not complete" in result.error_message

    def test_invalid_execution_id_response_raises_value_error(
        self, handler, mock_session
    ):
        """When execution_id missing in response, raises ValueError."""
        mock_session.post.return_value.json.return_value = {"no_id_here": "value"}
        config = {
            "call_id": "err-no-exec-id",
            "name": "No Exec ID Call",
            "call_type": "icestreams",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": False,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "missing execution_id" in result.error_message

    def test_blocking_call_with_failed_status_returns_failed(
        self, handler, mock_session
    ):
        """When blocking call returns failed status, result.success is False."""
        post_response = MagicMock()
        post_response.json.return_value = {"execution_id": "exec-failed"}
        mock_session.post.return_value = post_response

        get_response = MagicMock()
        get_response.json.return_value = {
            "status": "failed",
            "output": None,
            "error_message": "Execution failed",
        }
        mock_session.get.return_value = get_response

        config = {
            "call_id": "bl-failed",
            "name": "Blocking Failed",
            "call_type": "iceruns",
            "target_id": "fn-1",
            "input_template": {},
            "is_blocking": True,
            "timeout_seconds": 30,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "failed"
        assert result.error_message == "Execution failed"

    def test_polling_api_error_during_poll_returns_error(self, handler, mock_session):
        """When API errors during polling, status is 'error'."""
        import requests

        post_response = MagicMock()
        post_response.json.return_value = {"execution_id": "exec-poll-err"}
        mock_session.post.return_value = post_response

        mock_session.get.side_effect = requests.ConnectionError("Poll failed")

        config = {
            "call_id": "bl-poll-error",
            "name": "Blocking Poll Error",
            "call_type": "icestreams",
            "target_id": "pb-1",
            "input_template": {},
            "is_blocking": True,
            "timeout_seconds": 30,
            "trigger_on": "post_merge",
        }
        result = handler.execute_call(config, {})
        assert result.success is False
        assert result.status == "error"
        assert "API error" in result.error_message

    def test_execute_calls_continues_after_single_call_failure(
        self, handler, mock_session
    ):
        """execute_calls processes all calls even if one fails."""
        # First call fails
        mock_session.post.side_effect = [
            MagicMock(json=MagicMock(return_value={})),  # No execution_id
            MagicMock(
                json=MagicMock(return_value={"execution_id": "exec-ok"}),
                raise_for_status=MagicMock(),
            ),
        ]

        configs = [
            {
                "call_id": "c1",
                "name": "Call 1",
                "call_type": "icestreams",
                "target_id": "pb-1",
                "input_template": {},
                "is_blocking": False,
                "trigger_on": "post_merge",
            },
            {
                "call_id": "c2",
                "name": "Call 2",
                "call_type": "icestreams",
                "target_id": "pb-2",
                "input_template": {},
                "is_blocking": False,
                "trigger_on": "post_merge",
            },
        ]

        results = handler.execute_calls(configs, {}, trigger_phase="post_merge")
        assert len(results) == 2
        assert results[0].success is False
        assert results[1].success is True
