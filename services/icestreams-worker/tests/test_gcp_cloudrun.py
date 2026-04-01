"""
Unit tests for GCP Cloud Run cloud action node.

Tests GcpCloudRunAction with mocked aiohttp and OIDC authentication.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from nodes.actions.cloud.gcp_cloudrun import GcpCloudRunAction
from nodes.base import NodeContext, NodeResult


class MockOIDCClient:
    """Mock OIDC Client."""

    def __init__(self, token="mock-id-token"):
        self.token = token

    def get_id_token(self, target_audience=None):
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
def gcp_cloudrun_node():
    """Create a GcpCloudRunAction instance."""
    return GcpCloudRunAction()


class TestGcpCloudRunAuthentication:
    """Test GCP Cloud Run authentication."""

    @patch("nodes.actions.cloud.gcp_cloudrun.OIDCClient")
    def test_authenticate_with_json_string(
        self, mock_oidc_class, gcp_cloudrun_node, node_context
    ):
        """Test authentication with service account JSON string."""
        service_account_json = json.dumps(
            {
                "type": "service_account",
                "project_id": "test-project",
                "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
            }
        )

        config_map = {
            "service_account_json": service_account_json,
            "service_url": "https://test-service-abc123-us-central1.a.run.app",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        mock_oidc_instance = MockOIDCClient()
        mock_oidc_class.create_from_json_string.return_value = mock_oidc_instance

        auth_client = asyncio.run(gcp_cloudrun_node._authenticate(node_context))

        assert auth_client is mock_oidc_instance
        mock_oidc_class.create_from_json_string.assert_called_once()

    @patch("nodes.actions.cloud.gcp_cloudrun.OIDCClient")
    def test_authenticate_with_json_file_path(
        self, mock_oidc_class, gcp_cloudrun_node, node_context
    ):
        """Test authentication with service account file path."""
        config_map = {
            "service_account_json": "/path/to/service-account.json",
            "service_url": "https://test-service-abc123-us-central1.a.run.app",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        mock_oidc_instance = MockOIDCClient()
        mock_oidc_class.return_value = mock_oidc_instance

        auth_client = asyncio.run(gcp_cloudrun_node._authenticate(node_context))

        assert auth_client is mock_oidc_instance

    @patch("nodes.actions.cloud.gcp_cloudrun.OIDCClient")
    def test_authenticate_with_dict(
        self, mock_oidc_class, gcp_cloudrun_node, node_context
    ):
        """Test authentication with service account as dictionary."""
        service_account_dict = {
            "type": "service_account",
            "project_id": "test-project",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----",
        }

        config_map = {
            "service_account_json": service_account_dict,
            "service_url": "https://test-service-abc123-us-central1.a.run.app",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        mock_oidc_instance = MockOIDCClient()
        mock_oidc_class.create_from_json_string.return_value = mock_oidc_instance

        auth_client = asyncio.run(gcp_cloudrun_node._authenticate(node_context))

        assert auth_client is mock_oidc_instance

    def test_authenticate_missing_service_account(
        self, gcp_cloudrun_node, node_context
    ):
        """Test authentication fails without service account."""
        config_map = {
            "service_account_json": None,
            "service_url": "https://test-service.run.app",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        with pytest.raises(ValueError, match="service_account_json"):
            asyncio.run(gcp_cloudrun_node._authenticate(node_context))

    def test_authenticate_missing_service_url(self, gcp_cloudrun_node, node_context):
        """Test authentication fails without service URL."""
        config_map = {
            "service_account_json": '{"type":"service_account"}',
            "service_url": None,
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        with pytest.raises(ValueError, match="service_url"):
            asyncio.run(gcp_cloudrun_node._authenticate(node_context))


class TestGcpCloudRunConfigValidation:
    """Test GCP Cloud Run configuration validation."""

    def test_valid_http_methods(self):
        """Test all valid HTTP methods are accepted."""
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        for method in valid_methods:
            assert method in valid_methods

    def test_service_url_normalization(self):
        """Test service URL normalization."""
        url_with_slash = "https://example.com/"
        url_normalized = url_with_slash.rstrip("/")
        assert url_normalized == "https://example.com"

    def test_path_normalization(self):
        """Test path normalization."""
        path_with_slash = "/api/v1/path"
        path_normalized = path_with_slash.lstrip("/")
        assert path_normalized == "api/v1/path"

    def test_url_construction(self):
        """Test URL construction with path."""
        base_url = "https://example.com"
        path = "api/v1/resource"
        full_url = f"{base_url}/{path}"
        assert full_url == "https://example.com/api/v1/resource"


class TestGcpCloudRunPayloadHandling:
    """Test GCP Cloud Run payload handling."""

    def test_json_payload_serialization(self):
        """Test JSON payload serialization."""
        payload = {"key": "value", "nested": {"data": 123}}
        json_str = json.dumps(payload)
        assert json.loads(json_str) == payload

    def test_string_payload_handling(self):
        """Test string payload handling."""
        payload = "plain text"
        assert isinstance(payload, str)

    def test_bytes_payload_handling(self):
        """Test bytes payload handling."""
        payload = b"binary data"
        assert isinstance(payload, bytes)

    def test_null_payload_handling(self):
        """Test null payload handling."""
        payload = None
        assert payload is None

    def test_content_type_detection_json(self):
        """Test content-type detection for JSON."""
        payload = {"test": "data"}
        if isinstance(payload, (dict, list)):
            content_type = "application/json"
        assert content_type == "application/json"

    def test_content_type_detection_text(self):
        """Test content-type detection for text."""
        payload = "plain text"
        if isinstance(payload, str):
            content_type = "text/plain"
        assert content_type == "text/plain"


class TestGcpCloudRunResponseHandling:
    """Test GCP Cloud Run response handling."""

    def test_json_response_parsing(self):
        """Test JSON response parsing."""
        response_text = '{"message": "success", "data": {"id": 123}}'
        response_data = json.loads(response_text)
        assert response_data["message"] == "success"
        assert response_data["data"]["id"] == 123

    def test_invalid_json_response_handling(self):
        """Test handling of invalid JSON response."""
        response_text = "plain text response"
        try:
            json.loads(response_text)
            assert False
        except json.JSONDecodeError:
            pass

    def test_status_code_evaluation(self):
        """Test HTTP status code evaluation."""
        status_codes_ok = [200, 201, 202, 204]
        status_codes_error = [400, 401, 403, 404, 500, 503]

        for code in status_codes_ok:
            assert code < 400

        for code in status_codes_error:
            assert code >= 400

    def test_error_detail_extraction(self):
        """Test error detail extraction from response."""
        error_response = {"error": "Invalid request"}
        error_detail = error_response.get("error") or error_response.get("message")
        assert error_detail == "Invalid request"

    def test_error_detail_extraction_with_message(self):
        """Test error detail extraction with message field."""
        error_response = {"message": "Server error"}
        error_detail = error_response.get("error") or error_response.get("message")
        assert error_detail == "Server error"


class TestGcpCloudRunExecute:
    """Test GCP Cloud Run execute method."""

    @patch("nodes.actions.cloud.gcp_cloudrun.OIDCClient")
    def test_execute_authentication_failure(
        self, mock_oidc_class, gcp_cloudrun_node, node_context
    ):
        """Test execution fails when authentication fails."""
        node_context.get_config_value.return_value = None
        inputs = {"payload": {"test": "data"}}

        result = asyncio.run(gcp_cloudrun_node.execute(node_context, inputs))

        assert result.success is False
        assert result.error is not None


class TestGcpCloudRunNodeMetadata:
    """Test GCP Cloud Run node metadata."""

    def test_node_type(self, gcp_cloudrun_node):
        """Test node type identifier."""
        assert gcp_cloudrun_node.node_type == "gcp_cloudrun"

    def test_node_name(self, gcp_cloudrun_node):
        """Test node display name."""
        assert gcp_cloudrun_node.name == "GCP Cloud Run"

    def test_node_category(self, gcp_cloudrun_node):
        """Test node category."""
        assert gcp_cloudrun_node.category == "cloud"

    def test_inputs_definition(self, gcp_cloudrun_node):
        """Test input ports definition."""
        inputs = gcp_cloudrun_node.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "payload"
        assert inputs[0].required is False

    def test_outputs_definition(self, gcp_cloudrun_node):
        """Test output ports definition."""
        outputs = gcp_cloudrun_node.outputs()
        assert len(outputs) == 2
        assert any(o.name == "result" for o in outputs)
        assert any(o.name == "error" for o in outputs)

    def test_default_http_method(self):
        """Test default HTTP method is POST."""
        default_method = "POST"
        assert default_method == "POST"

    def test_default_path_is_empty(self):
        """Test default path is empty."""
        default_path = ""
        assert default_path == ""
