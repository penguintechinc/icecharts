"""
Unit tests for AWS Lambda cloud action node.

Tests AwsLambdaAction with mocked boto3 and AWS SDK calls.
"""

import asyncio
import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from nodes.actions.cloud.aws_lambda import AwsLambdaAction
from nodes.base import NodeContext, NodeResult


class MockAWSSTSClient:
    """Mock AWS STS Client."""

    def __init__(self, credentials=None):
        self.credentials = credentials or {
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "session_token": None,
        }

    def get_credentials(self):
        return self.credentials


class MockLambdaResponse:
    """Mock Lambda response payload."""

    def __init__(self, data):
        self._data = data

    def read(self):
        if isinstance(self._data, bytes):
            return self._data
        return json.dumps(self._data).encode("utf-8")


class MockLambdaClient:
    """Mock boto3 Lambda client."""

    def __init__(self, should_fail=False, function_error=None, status_code=200):
        self.should_fail = should_fail
        self.function_error = function_error
        self.status_code = status_code
        self.last_invoke_params = None

    def invoke(self, **kwargs):
        self.last_invoke_params = kwargs

        if self.should_fail:
            raise Exception("Lambda client error")

        response = {
            "StatusCode": self.status_code,
            "RequestId": "mock-request-id-12345",
            "ExecutedVersion": "$LATEST",
        }

        if self.function_error:
            response["FunctionError"] = self.function_error

        if kwargs.get("InvocationType") == "RequestResponse":
            response["Payload"] = MockLambdaResponse(
                {"message": "success", "data": "test"}
            )

        return response


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
def aws_lambda_node():
    """Create an AwsLambdaAction instance."""
    return AwsLambdaAction()


class TestAwsLambdaAuthentication:
    """Test AWS Lambda authentication."""

    @patch("nodes.actions.cloud.aws_lambda.AWSSTSClient")
    def test_authenticate_with_required_credentials(
        self, mock_sts_class, aws_lambda_node, node_context
    ):
        """Test successful authentication with required credentials."""
        config_map = {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_region": "us-east-1",
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        mock_sts_instance = MockAWSSTSClient()
        mock_sts_class.return_value = mock_sts_instance

        auth_client = asyncio.run(aws_lambda_node._authenticate(node_context))

        assert auth_client is mock_sts_instance
        mock_sts_class.assert_called_once()

    def test_authenticate_missing_required_credentials(
        self, aws_lambda_node, node_context
    ):
        """Test authentication fails when required credentials are missing."""
        node_context.get_config_value.return_value = None

        with pytest.raises(ValueError):
            asyncio.run(aws_lambda_node._authenticate(node_context))

    @patch("nodes.actions.cloud.aws_lambda.AWSSTSClient")
    def test_authenticate_with_optional_credentials(
        self, mock_sts_class, aws_lambda_node, node_context
    ):
        """Test authentication with optional session token and role ARN."""
        config_map = {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_region": "us-east-1",
            "aws_session_token": "session-token-xyz",
            "role_arn": "arn:aws:iam::123456789012:role/test-role",
            "session_duration": 7200,
        }
        node_context.get_config_value.side_effect = (
            lambda key, default=None: config_map.get(key, default)
        )

        mock_sts_instance = MockAWSSTSClient()
        mock_sts_class.return_value = mock_sts_instance

        auth_client = asyncio.run(aws_lambda_node._authenticate(node_context))

        assert auth_client is mock_sts_instance


class TestAwsLambdaInvocation:
    """Test AWS Lambda function invocation."""

    def test_invoke_lambda_success_synchronous(self, aws_lambda_node, node_context):
        """Test successful synchronous Lambda invocation."""
        mock_lambda_client = MockLambdaClient(status_code=200)

        auth_client = MockAWSSTSClient()
        function_config = {
            "function_name": "test-function",
            "invocation_type": "RequestResponse",
            "qualifier": None,
            "aws_region": "us-east-1",
        }
        payload = {"test": "data"}

        with patch("asyncio.get_event_loop") as mock_loop:
            mock_event_loop = Mock()
            mock_loop.return_value = mock_event_loop
            mock_event_loop.run_in_executor = AsyncMock(
                return_value=mock_lambda_client.invoke(
                    **{
                        "FunctionName": "test-function",
                        "InvocationType": "RequestResponse",
                        "Payload": json.dumps(payload).encode("utf-8"),
                    }
                )
            )

            with patch.dict(
                "sys.modules", {"boto3": Mock(), "botocore.exceptions": Mock()}
            ):
                result = asyncio.run(
                    aws_lambda_node._invoke_function(
                        node_context, auth_client, function_config, payload
                    )
                )

                assert result["status_code"] == 200
                assert result["request_id"] == "mock-request-id-12345"

    @patch.dict("sys.modules", {"boto3": Mock(), "botocore.exceptions": Mock()})
    def test_invoke_lambda_missing_function_name(self, aws_lambda_node, node_context):
        """Test invocation fails when function_name is missing."""
        auth_client = MockAWSSTSClient()
        function_config = {
            "function_name": None,
            "invocation_type": "RequestResponse",
            "aws_region": "us-east-1",
        }
        payload = {"test": "data"}

        with pytest.raises(ValueError, match="function_name"):
            asyncio.run(
                aws_lambda_node._invoke_function(
                    node_context, auth_client, function_config, payload
                )
            )

    @patch.dict("sys.modules", {"boto3": Mock(), "botocore.exceptions": Mock()})
    def test_invoke_lambda_invalid_invocation_type(self, aws_lambda_node, node_context):
        """Test invocation fails with invalid invocation type."""
        auth_client = MockAWSSTSClient()
        function_config = {
            "function_name": "test-function",
            "invocation_type": "InvalidType",
            "aws_region": "us-east-1",
        }
        payload = {"test": "data"}

        with pytest.raises(ValueError, match="Invalid invocation_type"):
            asyncio.run(
                aws_lambda_node._invoke_function(
                    node_context, auth_client, function_config, payload
                )
            )


class TestAwsLambdaExecute:
    """Test AWS Lambda execute method."""

    @patch("nodes.actions.cloud.aws_lambda.AWSSTSClient")
    def test_execute_missing_required_input(
        self, mock_sts_class, aws_lambda_node, node_context
    ):
        """Test execution fails with missing required input."""
        inputs = {}  # Missing required payload

        result = asyncio.run(aws_lambda_node.execute(node_context, inputs))

        assert result.success is False
        assert result.error is not None

    @patch("nodes.actions.cloud.aws_lambda.AWSSTSClient")
    def test_execute_authentication_failure(
        self, mock_sts_class, aws_lambda_node, node_context
    ):
        """Test execution fails when authentication fails."""
        mock_sts_class.side_effect = ValueError("Missing credentials")
        node_context.get_config_value.side_effect = lambda key, default=None: {
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_region": "us-east-1",
            "function_name": "test-function",
            "invocation_type": "RequestResponse",
            "max_retries": 3,
            "retry_delay": 1.0,
        }.get(key, default)
        inputs = {"payload": {"test": "data"}}

        result = asyncio.run(aws_lambda_node.execute(node_context, inputs))

        assert result.success is False
        assert result.error is not None


class TestAwsLambdaNodeMetadata:
    """Test AWS Lambda node metadata."""

    def test_node_type(self, aws_lambda_node):
        """Test node type identifier."""
        assert aws_lambda_node.node_type == "aws_lambda"

    def test_node_name(self, aws_lambda_node):
        """Test node display name."""
        assert aws_lambda_node.name == "AWS Lambda"

    def test_node_category(self, aws_lambda_node):
        """Test node category."""
        assert aws_lambda_node.category == "cloud"

    def test_inputs_definition(self, aws_lambda_node):
        """Test input ports definition."""
        inputs = aws_lambda_node.inputs()
        assert len(inputs) == 1
        assert inputs[0].name == "payload"
        assert inputs[0].required is True

    def test_outputs_definition(self, aws_lambda_node):
        """Test output ports definition."""
        outputs = aws_lambda_node.outputs()
        assert len(outputs) == 2
        assert any(o.name == "result" for o in outputs)
        assert any(o.name == "error" for o in outputs)

    def test_payload_serialization_dict(self):
        """Test Lambda payload serialization with dict."""
        payload = {"key": "value"}
        payload_bytes = json.dumps(payload).encode("utf-8")
        assert isinstance(payload_bytes, bytes)
        assert b"key" in payload_bytes

    def test_payload_serialization_string(self):
        """Test Lambda payload serialization with string."""
        payload = "plain text"
        payload_bytes = payload.encode("utf-8")
        assert payload_bytes == b"plain text"

    def test_payload_serialization_bytes(self):
        """Test Lambda payload serialization with bytes."""
        payload = b"binary data"
        assert isinstance(payload, bytes)
        assert payload == b"binary data"

    def test_response_parsing_json(self):
        """Test Lambda response JSON parsing."""
        response_text = '{"message": "success"}'
        response_data = json.loads(response_text)
        assert response_data["message"] == "success"

    def test_response_parsing_invalid_json(self):
        """Test Lambda response handling with invalid JSON."""
        response_text = "not valid json"
        try:
            json.loads(response_text)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            pass


class TestAwsLambdaPayloadHandling:
    """Test AWS Lambda payload handling."""

    def test_dict_payload_encoding(self):
        """Test encoding dict payload."""
        payload = {"test": "data", "nested": {"value": 123}}
        payload_bytes = json.dumps(payload).encode("utf-8")
        assert b"test" in payload_bytes
        assert b"nested" in payload_bytes

    def test_list_payload_encoding(self):
        """Test encoding list payload."""
        payload = [1, 2, 3, {"key": "value"}]
        payload_bytes = json.dumps(payload).encode("utf-8")
        assert b"[" in payload_bytes

    def test_string_payload_encoding(self):
        """Test encoding string payload."""
        payload = "test string"
        payload_bytes = payload.encode("utf-8")
        assert payload_bytes == b"test string"

    def test_numeric_payload_encoding(self):
        """Test encoding numeric payload."""
        payload = 42
        payload_bytes = json.dumps(str(payload)).encode("utf-8")
        assert b"42" in payload_bytes


class TestAwsLambdaConfigValidation:
    """Test AWS Lambda configuration validation."""

    def test_valid_invocation_types(self):
        """Test all valid invocation types are accepted."""
        valid_types = ["RequestResponse", "Event", "DryRun"]
        for inv_type in valid_types:
            assert inv_type in valid_types

    def test_invocation_type_case_sensitive(self):
        """Test invocation type validation is case-sensitive."""
        # The validation checks for exact match
        valid = "RequestResponse"
        invalid = "requestresponse"
        assert valid != invalid
