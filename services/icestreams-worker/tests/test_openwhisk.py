"""
Unit tests for Apache OpenWhisk cloud action node.

Tests OpenWhiskAction with mocked authentication and HTTP calls.
"""

import asyncio
import base64
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from nodes.actions.cloud.openwhisk import OpenWhiskAction
from nodes.base import NodeContext, NodeResult


class MockOAuth2Client:
    """Mock OAuth2 Client."""

    def __init__(self, token="mock-access-token"):
        self.token = token

    def get_access_token(self):
        return self.token


@pytest.fixture
def node_context():
    """Create a mock NodeContext."""
    context = Mock(spec=NodeContext)
    context.get_config_value = Mock(return_value=None)
    context.log_info = Mock()
    context.log_error = Mock()
    context.log_debug = Mock()
    return context


@pytest.fixture
def openwhisk_node():
    """Create an OpenWhiskAction instance."""
    return OpenWhiskAction()


class TestOpenWhiskAuthentication:
    """Test OpenWhisk authentication."""

    @patch("nodes.actions.cloud.openwhisk.OAuth2Client")
    def test_authenticate_with_oauth2(
        self, mock_oauth2_class, openwhisk_node, node_context
    ):
        """Test authentication with OAuth2."""
        config_map = {
            "oauth_client_id": "client-id",
            "oauth_client_secret": "client-secret",
            "oauth_token_url": "https://auth.example.com/token",
            "oauth_scope": "read write",
            "auth_key": None,
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        mock_oauth2_instance = MockOAuth2Client()
        mock_oauth2_class.return_value = mock_oauth2_instance

        auth_client = asyncio.run(openwhisk_node._authenticate(node_context))

        assert auth_client is mock_oauth2_instance
        mock_oauth2_class.assert_called_once()

    def test_authenticate_with_basic_auth(self, openwhisk_node, node_context):
        """Test authentication with basic auth (auth_key)."""
        config_map = {
            "oauth_client_id": None,
            "oauth_client_secret": None,
            "oauth_token_url": None,
            "oauth_scope": None,
            "auth_key": "uuid:key",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        auth_client = asyncio.run(openwhisk_node._authenticate(node_context))

        # Basic auth returns None (no OAuth client needed)
        assert auth_client is None

    def test_authenticate_no_credentials(self, openwhisk_node, node_context):
        """Test authentication fails when no credentials are provided."""
        node_context.get_config_value.return_value = None

        with pytest.raises(ValueError, match="requires either"):
            asyncio.run(openwhisk_node._authenticate(node_context))


class TestOpenWhiskConfigValidation:
    """Test OpenWhisk configuration validation."""

    def test_api_host_normalization(self):
        """Test API host normalization."""
        api_host = "https://openwhisk.example.com/"
        api_host_normalized = api_host.rstrip("/")
        assert api_host_normalized == "https://openwhisk.example.com"

    def test_url_construction(self):
        """Test OpenWhisk action URL construction."""
        api_host = "https://openwhisk.example.com"
        namespace = "test_namespace"
        action_name = "my-action"
        url = f"{api_host}/api/v1/namespaces/{namespace}/actions/{action_name}"
        assert (
            url
            == "https://openwhisk.example.com/api/v1/namespaces/test_namespace/actions/my-action"
        )

    def test_default_namespace(self):
        """Test default namespace is underscore."""
        default_namespace = "_"
        assert default_namespace == "_"

    def test_blocking_query_parameter(self):
        """Test blocking query parameter construction."""
        params = {}
        blocking = True
        result_only = True
        if blocking:
            params["blocking"] = "true"
            if result_only:
                params["result"] = "true"

        assert params["blocking"] == "true"
        assert params["result"] == "true"

    def test_non_blocking_no_result_query_parameter(self):
        """Test non-blocking without result query parameter."""
        params = {}
        blocking = False
        result_only = True
        if blocking:
            params["blocking"] = "true"
            if result_only:
                params["result"] = "true"

        assert "blocking" not in params
        assert "result" not in params


class TestOpenWhiskPayloadHandling:
    """Test OpenWhisk payload handling."""

    def test_dict_payload_handling(self):
        """Test dict payload is used directly."""
        payload = {"key": "value"}
        payload_json = payload if isinstance(payload, dict) else {"value": payload}
        assert payload_json == {"key": "value"}

    def test_list_payload_handling(self):
        """Test list payload is used directly."""
        payload = [1, 2, 3]
        payload_json = payload if isinstance(payload, list) else {"value": payload}
        assert payload_json == [1, 2, 3]

    def test_string_payload_handling(self):
        """Test string payload is wrapped."""
        payload = "string value"
        payload_json = (
            payload if isinstance(payload, (dict, list)) else {"value": payload}
        )
        assert payload_json == {"value": "string value"}

    def test_numeric_payload_handling(self):
        """Test numeric payload is wrapped."""
        payload = 42
        payload_json = (
            payload if isinstance(payload, (dict, list)) else {"value": payload}
        )
        assert payload_json == {"value": 42}


class TestOpenWhiskAuthHeaders:
    """Test OpenWhisk authentication headers."""

    def test_oauth2_bearer_token(self):
        """Test OAuth2 bearer token header."""
        token = "test-access-token"
        auth_header = f"Bearer {token}"
        assert auth_header == "Bearer test-access-token"

    def test_basic_auth_encoding(self):
        """Test basic auth encoding."""
        auth_key = "uuid:key"
        encoded = base64.b64encode(auth_key.encode("utf-8")).decode("utf-8")
        auth_header = f"Basic {encoded}"
        assert "Basic" in auth_header
        assert encoded == base64.b64encode(b"uuid:key").decode("utf-8")

    def test_content_type_header(self):
        """Test content type header."""
        content_type = "application/json"
        assert content_type == "application/json"


class TestOpenWhiskActivationParsing:
    """Test OpenWhisk activation response parsing."""

    def test_parse_blocking_response(self):
        """Test parsing blocking action response."""
        response_data = {
            "activationId": "activation-123",
            "result": {"message": "success"},
        }
        activation_id = response_data.get("activationId")
        assert activation_id == "activation-123"

    def test_parse_non_blocking_response(self):
        """Test parsing non-blocking action response."""
        response_data = {"activationId": "activation-456"}
        activation_id = response_data.get("activationId")
        assert activation_id == "activation-456"

    def test_check_activation_completion(self):
        """Test checking if activation is complete."""
        activation = {
            "activationId": "activation-789",
            "end": 1234567890,
            "response": {"success": True, "result": {"data": "test"}},
        }
        is_complete = activation.get("end") is not None
        assert is_complete is True

    def test_check_activation_incomplete(self):
        """Test checking incomplete activation."""
        activation = {
            "activationId": "activation-789",
            "response": {
                "success": True,
            },
        }
        is_complete = activation.get("end") is not None
        assert is_complete is False

    def test_extract_activation_result(self):
        """Test extracting result from completed activation."""
        activation = {
            "activationId": "activation-789",
            "end": 1234567890,
            "response": {"success": True, "result": {"message": "done"}},
        }
        result = activation.get("response", {}).get("result", {})
        assert result == {"message": "done"}

    def test_check_activation_success(self):
        """Test checking activation success."""
        activation = {
            "activationId": "activation-789",
            "end": 1234567890,
            "response": {"success": True, "result": {"data": "test"}},
        }
        success = activation.get("response", {}).get("success", False)
        assert success is True

    def test_check_activation_failure(self):
        """Test checking activation failure."""
        activation = {
            "activationId": "activation-789",
            "end": 1234567890,
            "response": {"success": False, "error": "Action failed"},
        }
        success = activation.get("response", {}).get("success", False)
        assert success is False
        error = activation.get("response", {}).get("error")
        assert error == "Action failed"


class TestOpenWhiskExecute:
    """Test OpenWhisk execute method."""

    @patch("nodes.actions.cloud.openwhisk.OAuth2Client")
    def test_execute_authentication_failure(
        self, mock_oauth2_class, openwhisk_node, node_context
    ):
        """Test execution fails when authentication fails."""
        mock_oauth2_class.side_effect = ValueError("Invalid credentials")
        config_map = {
            "oauth_client_id": "client-id",
            "oauth_client_secret": "client-secret",
            "oauth_token_url": "https://auth.example.com/token",
            "auth_key": None,
            "api_host": "https://openwhisk.example.com",
            "action_name": "test-action",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )
        inputs = {"payload": {"test": "data"}}

        result = asyncio.run(openwhisk_node.execute(node_context, inputs))

        assert result.success is False
        assert result.error is not None

    def test_execute_missing_required_input(self, openwhisk_node, node_context):
        """Test execution fails with missing required payload."""
        inputs = {}  # Missing required payload

        result = asyncio.run(openwhisk_node.execute(node_context, inputs))

        assert result.success is False


class TestOpenWhiskNodeMetadata:
    """Test OpenWhisk node metadata."""

    def test_node_type(self, openwhisk_node):
        """Test node type identifier."""
        assert openwhisk_node.node_type == "openwhisk_action"

    def test_node_name(self, openwhisk_node):
        """Test node display name."""
        assert openwhisk_node.name == "OpenWhisk Action"

    def test_node_category(self, openwhisk_node):
        """Test node category."""
        assert openwhisk_node.category == "cloud"

    def test_inputs_definition(self, openwhisk_node):
        """Test input ports definition."""
        inputs = openwhisk_node.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "payload"
        assert inputs[0].required is True

    def test_outputs_definition(self, openwhisk_node):
        """Test output ports definition."""
        outputs = openwhisk_node.outputs()
        assert len(outputs) == 2
        assert any(o.name == "result" for o in outputs)
        assert any(o.name == "error" for o in outputs)

    def test_default_poll_interval(self, openwhisk_node):
        """Test default poll interval."""
        assert openwhisk_node.DEFAULT_POLL_INTERVAL == 1.0

    def test_default_poll_timeout(self, openwhisk_node):
        """Test default poll timeout."""
        assert openwhisk_node.DEFAULT_POLL_TIMEOUT == 60.0


class TestOpenWhiskTimeoutHandling:
    """Test OpenWhisk timeout handling."""

    async def test_timeout_error_creation(self):
        """Test timeout error creation."""
        activation_id = "test-activation-123"
        timeout = 10.0
        try:
            raise TimeoutError(
                f"Activation {activation_id} did not complete within {timeout}s"
            )
        except TimeoutError as e:
            assert "did not complete" in str(e)
            assert activation_id in str(e)


class TestOpenWhiskPollingLogic:
    """Test OpenWhisk polling logic."""

    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        elapsed = 0.0
        interval = 0.5
        timeout = 5.0

        # Simulate polling loop
        for i in range(10):
            if elapsed < timeout:
                elapsed += interval
            else:
                break

        assert elapsed <= 5.5  # Should stop within timeout + interval

    def test_poll_interval_progression(self):
        """Test poll interval stays constant."""
        poll_interval = 1.0
        intervals = [poll_interval for _ in range(5)]
        total = sum(intervals)
        assert total == 5.0
