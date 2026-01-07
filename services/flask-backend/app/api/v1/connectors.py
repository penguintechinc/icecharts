"""
Connector API endpoints for IceCharts Connector Framework.

Provides endpoints for:
- Listing available connectors and their node definitions
- Managing connector configurations
- Testing connector connections
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request

from app.middleware import auth_required

# Add icestreams-worker to path for connector imports
# In container: /app/icestreams-worker
# Local dev: ../../../icestreams-worker from this file
worker_paths = [
    Path("/app/icestreams-worker"),  # Container path
    Path(__file__).parent.parent.parent.parent.parent / "icestreams-worker",  # Local dev path
]
for worker_path in worker_paths:
    if worker_path.exists() and str(worker_path) not in sys.path:
        sys.path.insert(0, str(worker_path))
        break

logger = logging.getLogger(__name__)

connectors_v1_bp = Blueprint("connectors", __name__, url_prefix="/connectors")


def _get_connector_manifests() -> List[Dict[str, Any]]:
    """
    Get all connector manifests.

    Returns list of connector data formatted for API responses.
    """
    try:
        from connectors.registry import ConnectorRegistry, discover_connectors

        # Ensure connectors are discovered
        if not ConnectorRegistry.is_initialized():
            discover_connectors(register_nodes=False)

        # Get all manifests and convert to dict
        manifests = []
        for manifest in ConnectorRegistry.get_all_manifests():
            manifests.append(manifest.to_dict())

        return manifests

    except ImportError as e:
        logger.warning(f"Failed to import connectors module: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading connector manifests: {e}")
        return []


@connectors_v1_bp.route("", methods=["GET"], strict_slashes=False)
@connectors_v1_bp.route("/", methods=["GET"])
@auth_required
def list_connectors():
    """
    List all available connectors and their node definitions.

    Returns:
        {
            "connectors": [
                {
                    "id": "waddlebot",
                    "name": "WaddleBot",
                    "icon": "🤖",
                    "color": "#6366F1",
                    "triggers": [...],
                    "actions": [...],
                    "transforms": [...]
                }
            ]
        }
    """
    connectors = _get_connector_manifests()
    return jsonify({"connectors": connectors}), 200


@connectors_v1_bp.route("/<connector_id>", methods=["GET"])
@auth_required
def get_connector(connector_id: str):
    """
    Get a specific connector's definition.

    Args:
        connector_id: Connector identifier (e.g., "waddlebot")

    Returns:
        Connector definition or 404 if not found.
    """
    connectors = _get_connector_manifests()

    for connector in connectors:
        if connector["id"] == connector_id:
            return jsonify({"connector": connector}), 200

    return jsonify({"error": f"Connector '{connector_id}' not found"}), 404


@connectors_v1_bp.route("/<connector_id>/nodes", methods=["GET"])
@auth_required
def get_connector_nodes(connector_id: str):
    """
    Get all nodes (triggers, actions, transforms) for a connector.

    Args:
        connector_id: Connector identifier

    Returns:
        {
            "nodes": [
                {
                    "node_type": "trigger_waddlebot_command",
                    "category": "triggers",
                    "name": "WaddleBot: Chat Command",
                    "description": "...",
                    "icon": "💬",
                    "inputs": [...],
                    "outputs": [...],
                    "config_schema": [...]
                }
            ]
        }
    """
    connectors = _get_connector_manifests()

    for connector in connectors:
        if connector["id"] == connector_id:
            nodes = []

            # Add triggers
            for trigger in connector.get("triggers", []):
                nodes.append({
                    "node_type": f"trigger_{connector_id}_{trigger['id']}",
                    "category": "triggers",
                    "name": f"{connector['name']}: {trigger['name']}",
                    "description": trigger.get("description", ""),
                    "icon": trigger.get("icon", connector.get("icon", "")),
                    "inputs": [],
                    "outputs": trigger.get("outputs", []),
                    "config_schema": trigger.get("config_schema", []),
                    "connector_id": connector_id,
                    "connector_color": connector.get("color", "#6366F1"),
                })

            # Add actions
            for action in connector.get("actions", []):
                nodes.append({
                    "node_type": f"action_{connector_id}_{action['id']}",
                    "category": "actions",
                    "name": f"{connector['name']}: {action['name']}",
                    "description": action.get("description", ""),
                    "icon": action.get("icon", connector.get("icon", "")),
                    "inputs": action.get("inputs", [{"name": "in", "type": "any"}]),
                    "outputs": action.get("outputs", [{"name": "out", "type": "object"}]),
                    "config_schema": action.get("config_schema", []),
                    "connector_id": connector_id,
                    "connector_color": connector.get("color", "#6366F1"),
                })

            # Add transforms
            for transform in connector.get("transforms", []):
                nodes.append({
                    "node_type": f"transform_{connector_id}_{transform['id']}",
                    "category": "transforms",
                    "name": f"{connector['name']}: {transform['name']}",
                    "description": transform.get("description", ""),
                    "icon": transform.get("icon", connector.get("icon", "")),
                    "inputs": transform.get("inputs", [{"name": "in", "type": "any"}]),
                    "outputs": transform.get("outputs", [{"name": "out", "type": "any"}]),
                    "config_schema": transform.get("config_schema", []),
                    "connector_id": connector_id,
                    "connector_color": connector.get("color", "#6366F1"),
                })

            return jsonify({"nodes": nodes}), 200

    return jsonify({"error": f"Connector '{connector_id}' not found"}), 404


@connectors_v1_bp.route("/nodes", methods=["GET"])
@auth_required
def get_all_connector_nodes():
    """
    Get all connector nodes across all connectors.

    Query params:
        category: Filter by category (triggers, actions, transforms)

    Returns:
        {
            "nodes": [...]
        }
    """
    category_filter = request.args.get("category")
    connectors = _get_connector_manifests()
    nodes = []

    for connector in connectors:
        connector_id = connector["id"]

        # Add triggers
        if not category_filter or category_filter == "triggers":
            for trigger in connector.get("triggers", []):
                nodes.append({
                    "node_type": f"trigger_{connector_id}_{trigger['id']}",
                    "category": "triggers",
                    "name": f"{connector['name']}: {trigger['name']}",
                    "description": trigger.get("description", ""),
                    "icon": trigger.get("icon", connector.get("icon", "")),
                    "inputs": [],
                    "outputs": trigger.get("outputs", []),
                    "config_schema": trigger.get("config_schema", []),
                    "connector_id": connector_id,
                    "connector_name": connector["name"],
                    "connector_color": connector.get("color", "#6366F1"),
                })

        # Add actions
        if not category_filter or category_filter == "actions":
            for action in connector.get("actions", []):
                nodes.append({
                    "node_type": f"action_{connector_id}_{action['id']}",
                    "category": "actions",
                    "name": f"{connector['name']}: {action['name']}",
                    "description": action.get("description", ""),
                    "icon": action.get("icon", connector.get("icon", "")),
                    "inputs": action.get("inputs", [{"name": "in", "type": "any"}]),
                    "outputs": action.get("outputs", [{"name": "out", "type": "object"}]),
                    "config_schema": action.get("config_schema", []),
                    "connector_id": connector_id,
                    "connector_name": connector["name"],
                    "connector_color": connector.get("color", "#6366F1"),
                })

        # Add transforms
        if not category_filter or category_filter == "transforms":
            for transform in connector.get("transforms", []):
                nodes.append({
                    "node_type": f"transform_{connector_id}_{transform['id']}",
                    "category": "transforms",
                    "name": f"{connector['name']}: {transform['name']}",
                    "description": transform.get("description", ""),
                    "icon": transform.get("icon", connector.get("icon", "")),
                    "inputs": transform.get("inputs", [{"name": "in", "type": "any"}]),
                    "outputs": transform.get("outputs", [{"name": "out", "type": "any"}]),
                    "config_schema": transform.get("config_schema", []),
                    "connector_id": connector_id,
                    "connector_name": connector["name"],
                    "connector_color": connector.get("color", "#6366F1"),
                })

    return jsonify({"nodes": nodes}), 200


# TODO: Add connector configuration endpoints
# These will be implemented when connector settings UI is built
#
# @connectors_v1_bp.route("/<connector_id>/config", methods=["GET"])
# def get_connector_config(connector_id: str):
#     """Get user's configuration for a connector."""
#     pass
#
# @connectors_v1_bp.route("/<connector_id>/config", methods=["PUT"])
# def update_connector_config(connector_id: str):
#     """Update user's configuration for a connector."""
#     pass
#
# @connectors_v1_bp.route("/<connector_id>/test", methods=["POST"])
# def test_connector(connector_id: str):
#     """Test connector connection with current configuration."""
#     pass
