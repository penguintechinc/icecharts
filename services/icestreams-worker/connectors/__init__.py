"""
IceCharts Connector Framework.

This package provides a modular connector system for integrating external products
(WaddleBot, WaddleAI, Elder, etc.) into the IceCharts workflow editor.

The framework uses YAML manifests to define connectors, which are then used to:
1. Generate workflow nodes dynamically at runtime
2. Render configuration UI panels from schema definitions
3. Execute API calls with proper authentication

Usage:
    from connectors import ConnectorRegistry, discover_connectors

    # Discover and load all connector manifests
    discover_connectors()

    # Get a specific connector
    waddlebot = ConnectorRegistry.get("waddlebot")

    # Execute an action
    result = await waddlebot.execute_action("send_chat", config, inputs)
"""

from connectors.base import (ActionDefinition, AuthMethod, BaseConnector,
                             ConfigField, ConnectorConfig, ConnectorManifest,
                             TransformDefinition, TriggerDefinition)
from connectors.executor import ConnectorActionExecutor
from connectors.node_generator import generate_nodes_from_connector
from connectors.registry import ConnectorRegistry, discover_connectors

__all__ = [
    # Base classes
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorManifest",
    "AuthMethod",
    "TriggerDefinition",
    "ActionDefinition",
    "TransformDefinition",
    "ConfigField",
    # Registry
    "ConnectorRegistry",
    "discover_connectors",
    # Node generation
    "generate_nodes_from_connector",
    # Execution
    "ConnectorActionExecutor",
]
