"""
Connector Action Executor for IceCharts Connector Framework.

This module handles the execution of connector actions and transforms,
including variable interpolation, request building, and response handling.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

from .base import ActionDefinition, ConnectorConfig, TransformDefinition
from .registry import ConnectorRegistry

logger = logging.getLogger(__name__)


class ConnectorExecutionError(Exception):
    """Raised when connector action execution fails."""

    pass


class ConnectorActionExecutor:
    """
    Executes connector actions by building and sending API requests.

    Handles:
    - Variable interpolation in config values and request bodies
    - Request building based on action definition
    - Response parsing and error handling
    """

    # Pattern for {{variable}} interpolation
    VARIABLE_PATTERN = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")

    def __init__(self) -> None:
        """Initialize the executor."""
        self._connectors: Dict[str, Any] = {}

    def _get_connector(self, connector_id: str):
        """Get or create connector instance."""
        if connector_id not in self._connectors:
            connector = ConnectorRegistry.get_instance(connector_id)
            if connector is None:
                raise ConnectorExecutionError(f"Connector '{connector_id}' not found")
            self._connectors[connector_id] = connector
        return self._connectors[connector_id]

    def _interpolate_value(
        self,
        value: Any,
        inputs: Dict[str, Any],
        variables: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Any:
        """
        Interpolate variables in a value.

        Supports {{variable}}, {{input.field}}, {{config.field}} syntax.

        Args:
            value: Value to interpolate.
            inputs: Node input values.
            variables: Workflow variables.
            config: Node configuration.

        Returns:
            Interpolated value.
        """
        if not isinstance(value, str):
            return value

        def replace_match(match: re.Match) -> str:
            path = match.group(1)
            parts = path.split(".")

            # Determine which dict to look in
            if parts[0] == "input" and len(parts) > 1:
                data = inputs
                parts = parts[1:]
            elif parts[0] == "config" and len(parts) > 1:
                data = config
                parts = parts[1:]
            elif parts[0] in inputs:
                data = inputs
            elif parts[0] in variables:
                data = variables
            elif parts[0] in config:
                data = config
            else:
                # Check nested in input data
                input_data = inputs.get("in", {})
                if isinstance(input_data, dict) and parts[0] in input_data:
                    data = input_data
                else:
                    return match.group(0)  # Keep original if not found

            # Navigate nested path
            result = data
            for part in parts:
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    return match.group(0)  # Keep original if not found

            return str(result) if result is not None else ""

        return self.VARIABLE_PATTERN.sub(replace_match, value)

    def _interpolate_dict(
        self,
        data: Dict[str, Any],
        inputs: Dict[str, Any],
        variables: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Recursively interpolate variables in a dictionary."""
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._interpolate_value(value, inputs, variables, config)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict(value, inputs, variables, config)
            elif isinstance(value, list):
                result[key] = [
                    (
                        self._interpolate_value(item, inputs, variables, config)
                        if isinstance(item, str)
                        else (
                            self._interpolate_dict(item, inputs, variables, config)
                            if isinstance(item, dict)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def _build_request_body(
        self,
        action: ActionDefinition,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        variables: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Build request body from action definition and config.

        Args:
            action: Action definition.
            config: Node configuration.
            inputs: Node inputs.
            variables: Workflow variables.

        Returns:
            Request body dictionary or None.
        """
        if action.method.upper() in ("GET", "HEAD", "OPTIONS"):
            return None

        # If action has a body template, use it
        if action.request_body_template:
            try:
                template = action.request_body_template
                interpolated = self._interpolate_value(
                    template, inputs, variables, config
                )
                return json.loads(interpolated)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse body template as JSON")

        # Otherwise, build from config schema
        body = {}
        for field in action.config_schema:
            if field.field in config:
                value = config[field.field]
                # Interpolate if supports variables
                if field.supports_variables and isinstance(value, str):
                    value = self._interpolate_value(value, inputs, variables, config)
                body[field.field] = value

        # Include input data if available
        input_data = inputs.get("in")
        if input_data is not None:
            if isinstance(input_data, dict):
                # Merge input data into body
                for key, value in input_data.items():
                    if key not in body:
                        body[key] = value
            else:
                body["data"] = input_data

        return body if body else None

    async def execute_action(
        self,
        connector_id: str,
        action_id: str,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a connector action.

        Args:
            connector_id: Connector identifier.
            action_id: Action identifier within connector.
            config: Node configuration.
            inputs: Node inputs.
            variables: Workflow variables.

        Returns:
            Action result data.

        Raises:
            ConnectorExecutionError: If action fails.
        """
        connector = self._get_connector(connector_id)
        action = connector.get_action(action_id)

        if action is None:
            raise ConnectorExecutionError(
                f"Action '{action_id}' not found in connector '{connector_id}'"
            )

        # Build request
        endpoint = self._interpolate_value(action.endpoint, inputs, variables, config)
        body = self._build_request_body(action, config, inputs, variables)

        logger.debug(
            f"Executing action {connector_id}.{action_id}: "
            f"{action.method} {endpoint}"
        )

        try:
            result = await connector.call_api(
                endpoint=endpoint,
                method=action.method,
                body=body,
            )
            return result

        except Exception as e:
            logger.error(f"Action {connector_id}.{action_id} failed: {e}")
            raise ConnectorExecutionError(
                f"Action '{action_id}' failed: {str(e)}"
            ) from e

    async def execute_transform(
        self,
        connector_id: str,
        transform_id: str,
        config: Dict[str, Any],
        inputs: Dict[str, Any],
        variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a connector transform.

        Args:
            connector_id: Connector identifier.
            transform_id: Transform identifier within connector.
            config: Node configuration.
            inputs: Node inputs.
            variables: Workflow variables.

        Returns:
            Transform result data.

        Raises:
            ConnectorExecutionError: If transform fails.
        """
        connector = self._get_connector(connector_id)
        transform = connector.get_transform(transform_id)

        if transform is None:
            raise ConnectorExecutionError(
                f"Transform '{transform_id}' not found in connector '{connector_id}'"
            )

        if not transform.endpoint:
            # No API call needed, just pass through
            return inputs.get("in", {})

        # Build request
        endpoint = self._interpolate_value(
            transform.endpoint, inputs, variables, config
        )

        # Build query params from config
        params = {}
        for field in transform.config_schema:
            if field.field in config:
                value = config[field.field]
                if field.supports_variables and isinstance(value, str):
                    value = self._interpolate_value(value, inputs, variables, config)
                params[field.field] = value

        logger.debug(
            f"Executing transform {connector_id}.{transform_id}: "
            f"{transform.method} {endpoint}"
        )

        try:
            result = await connector.call_api(
                endpoint=endpoint,
                method=transform.method,
                params=params if params else None,
            )
            return result

        except Exception as e:
            logger.error(f"Transform {connector_id}.{transform_id} failed: {e}")
            raise ConnectorExecutionError(
                f"Transform '{transform_id}' failed: {str(e)}"
            ) from e

    async def cleanup(self) -> None:
        """Clean up connector instances."""
        for connector in self._connectors.values():
            await connector.cleanup()
        self._connectors.clear()
