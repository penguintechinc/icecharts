"""
Base cloud function node framework for cloud action integrations.

This module provides the abstract base class for all cloud function action nodes.
Cloud function nodes invoke external serverless functions on various cloud platforms.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from ...base import BaseNode, NodeContext, NodeResult


class BaseCloudFunction(BaseNode):
    """
    Abstract base class for cloud function action nodes.

    This class provides common functionality for nodes that invoke cloud functions,
    including authentication handling, retry logic, error handling, and response
    standardization.

    Subclasses must implement:
    - _authenticate: Provider-specific authentication
    - _invoke_function: Provider-specific function invocation
    """

    # Common retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 30.0

    def __init__(self) -> None:
        """Initialize base cloud function node."""
        super().__init__()
        self._auth_client: Optional[Any] = None

    @abstractmethod
    async def _authenticate(self, context: NodeContext) -> Any:
        """
        Authenticate with the cloud provider.

        Args:
            context: Node execution context containing authentication config.

        Returns:
            Authentication client or credentials object.

        Raises:
            Exception: If authentication fails.
        """
        pass

    @abstractmethod
    async def _invoke_function(
        self,
        context: NodeContext,
        auth_client: Any,
        function_config: Dict[str, Any],
        payload: Any,
    ) -> Dict[str, Any]:
        """
        Invoke the cloud function with the given payload.

        Args:
            context: Node execution context.
            auth_client: Authenticated client or credentials.
            function_config: Function-specific configuration.
            payload: Payload to send to the function.

        Returns:
            Function response as dictionary.

        Raises:
            Exception: If invocation fails.
        """
        pass

    async def _retry_operation(
        self,
        operation: Any,
        max_retries: int,
        retry_delay: float,
        context: NodeContext,
    ) -> Any:
        """
        Execute an operation with exponential backoff retry logic.

        Args:
            operation: Async callable to retry.
            max_retries: Maximum number of retry attempts.
            retry_delay: Initial delay between retries in seconds.
            context: Node execution context for logging.

        Returns:
            Operation result.

        Raises:
            Exception: If all retries are exhausted.
        """
        last_exception = None
        current_delay = retry_delay

        for attempt in range(max_retries + 1):
            try:
                return await operation()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    context.log_warning(
                        f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    context.log_debug(f"Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
                else:
                    context.log_error(
                        f"Operation failed after {max_retries + 1} attempts: {e}"
                    )

        raise last_exception

    def _standardize_response(
        self,
        raw_response: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Standardize cloud function response format.

        Args:
            raw_response: Raw response from cloud function.
            success: Whether invocation was successful.
            error: Error message if invocation failed.

        Returns:
            Standardized response dictionary.
        """
        return {
            "success": success,
            "response": raw_response if success else None,
            "error": error,
            "raw": raw_response,
        }

    def _extract_config_values(
        self,
        context: NodeContext,
        required_keys: List[str],
        optional_keys: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract and validate configuration values.

        Args:
            context: Node execution context.
            required_keys: List of required configuration keys.
            optional_keys: Dictionary of optional keys with default values.

        Returns:
            Dictionary of extracted configuration values.

        Raises:
            ValueError: If required keys are missing.
        """
        config = {}
        missing_keys = []

        # Extract required keys
        for key in required_keys:
            value = context.get_config_value(key)
            if value is None:
                missing_keys.append(key)
            else:
                config[key] = value

        if missing_keys:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_keys)}"
            )

        # Extract optional keys with defaults
        if optional_keys:
            for key, default in optional_keys.items():
                config[key] = context.get_config_value(key, default)

        return config

    async def cleanup(self) -> None:
        """
        Clean up authentication client and resources.

        Override this method in subclasses if additional cleanup is needed.
        """
        if self._auth_client and hasattr(self._auth_client, "close"):
            try:
                await self._auth_client.close()
            except Exception:
                pass  # Best effort cleanup
        self._auth_client = None
