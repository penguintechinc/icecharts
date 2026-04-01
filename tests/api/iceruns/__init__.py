"""IceRuns API test fixtures and utilities."""

import json
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_function():
    """Sample IceRuns function for testing."""
    return {
        "name": "Test Function",
        "description": "A test function",
        "runtime": "python3.13",
        "entrypoint": "main.py",
        "handler": "handler",
        "memory_limit_mb": 128,
        "timeout_seconds": 60,
        "tags": ["test"],
    }


@pytest.fixture
def sample_execution():
    """Sample IceRuns execution."""
    return {
        "status": "completed",
        "input_json": {"name": "test"},
        "output_json": {"message": "success"},
        "exit_code": 0,
        "stdout": "output",
        "stderr": "",
    }


@pytest.fixture
def webhook_token():
    """Sample webhook token."""
    return "test_webhook_token_abc123xyz"


@pytest.fixture
def auth_token():
    """Sample JWT auth token."""
    return "Bearer test_jwt_token_xyz123"
