"""Elder API integration endpoints for IceCharts v1.0.0.

Provides endpoints to import infrastructure entities from Elder as shapes
and dependencies as connectors into IceCharts drawings.
"""

import logging
from typing import Optional

from flask import Blueprint, current_app, jsonify, request

from app.middleware import auth_required
from app.services.elder_service import ElderClient, ElderEntity, ElderDependency

logger = logging.getLogger(__name__)

# Create Elder blueprint
elder_v1_bp = Blueprint("elder", __name__, url_prefix="/elder")


@elder_v1_bp.route("/validate-connection", methods=["POST"])
@auth_required
async def validate_elder_connection():
    """Validate connection to Elder instance.

    Request body:
        {
            "base_url": "https://elder.example.com",
            "api_key": "your-api-key"
        }

    Returns:
        200: Connection is valid
        400: Invalid request parameters
        401: Invalid credentials
        503: Elder service unavailable
    """
    data = request.get_json() or {}

    base_url = data.get("base_url", "").strip()
    api_key = data.get("api_key", "").strip()

    if not base_url or not api_key:
        return jsonify({
            "success": False,
            "error": "base_url and api_key are required"
        }), 400

    try:
        client = ElderClient(base_url=base_url, api_key=api_key)
        # Try a simple request to validate
        entities = await client.get_entities(org_id=1, limit=1)
        return jsonify({
            "success": True,
            "message": "Connection to Elder validated successfully",
        }), 200
    except Exception as e:
        logger.error(f"Failed to validate Elder connection: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to connect to Elder: {str(e)}"
        }), 503


@elder_v1_bp.route("/entities", methods=["GET"])
@auth_required
async def get_entities():
    """Proxy entities from Elder API.

    Query Parameters:
        - base_url: Elder instance URL
        - api_key: Elder API key
        - org_id: Organization ID (required)
        - entity_type: Filter by entity type (optional)
        - limit: Maximum results (default: 100)
        - offset: Pagination offset (default: 0)

    Returns:
        200: List of entities
        400: Invalid parameters
        503: Elder service unavailable
    """
    base_url = request.args.get("base_url", "").strip()
    api_key = request.args.get("api_key", "").strip()
    org_id = request.args.get("org_id", type=int)
    entity_type = request.args.get("entity_type", "").strip() or None
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)

    if not base_url or not api_key or not org_id:
        return jsonify({
            "success": False,
            "error": "base_url, api_key, and org_id are required"
        }), 400

    try:
        client = ElderClient(base_url=base_url, api_key=api_key)
        entities = await client.get_entities(
            org_id=org_id,
            entity_type=entity_type,
            limit=limit,
            offset=offset,
        )

        return jsonify({
            "success": True,
            "entities": [e.to_dict() for e in entities],
            "total": len(entities),
            "limit": limit,
            "offset": offset,
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch entities from Elder: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to fetch entities: {str(e)}"
        }), 503


@elder_v1_bp.route("/relationships", methods=["GET"])
@auth_required
async def get_relationships():
    """Proxy relationships from Elder API.

    Query Parameters:
        - base_url: Elder instance URL
        - api_key: Elder API key
        - org_id: Organization ID (required)
        - source_entity_id: Filter by source (optional)
        - target_entity_id: Filter by target (optional)

    Returns:
        200: List of dependencies/relationships
        400: Invalid parameters
        503: Elder service unavailable
    """
    base_url = request.args.get("base_url", "").strip()
    api_key = request.args.get("api_key", "").strip()
    org_id = request.args.get("org_id", type=int)
    source_entity_id = request.args.get("source_entity_id", type=int)
    target_entity_id = request.args.get("target_entity_id", type=int)

    if not base_url or not api_key or not org_id:
        return jsonify({
            "success": False,
            "error": "base_url, api_key, and org_id are required"
        }), 400

    try:
        client = ElderClient(base_url=base_url, api_key=api_key)
        relationships = await client.get_relationships(
            org_id=org_id,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
        )

        return jsonify({
            "success": True,
            "relationships": [r.to_dict() for r in relationships],
            "total": len(relationships),
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch relationships from Elder: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to fetch relationships: {str(e)}"
        }), 503


@elder_v1_bp.route("/graph", methods=["GET"])
@auth_required
async def get_graph():
    """Get dependency graph from Elder API.

    Query Parameters:
        - base_url: Elder instance URL
        - api_key: Elder API key
        - org_id: Organization ID (required)
        - entity_id: Starting entity ID (optional)
        - depth: Graph traversal depth (default: 2)

    Returns:
        200: Graph with entities and dependencies
        400: Invalid parameters
        503: Elder service unavailable
    """
    base_url = request.args.get("base_url", "").strip()
    api_key = request.args.get("api_key", "").strip()
    org_id = request.args.get("org_id", type=int)
    entity_id = request.args.get("entity_id", type=int)
    depth = request.args.get("depth", 2, type=int)

    if not base_url or not api_key or not org_id:
        return jsonify({
            "success": False,
            "error": "base_url, api_key, and org_id are required"
        }), 400

    try:
        client = ElderClient(base_url=base_url, api_key=api_key)
        graph = await client.get_graph(
            org_id=org_id,
            entity_id=entity_id,
            depth=depth,
        )

        return jsonify({
            "success": True,
            "graph": graph,
        }), 200
    except Exception as e:
        logger.error(f"Failed to fetch graph from Elder: {e}")
        return jsonify({
            "success": False,
            "error": f"Failed to fetch graph: {str(e)}"
        }), 503


@elder_v1_bp.route("/import", methods=["POST"])
@auth_required
async def import_entities():
    """Import Elder entities as shapes into a drawing.

    Request body:
        {
            "drawing_id": "drawing-123",
            "base_url": "https://elder.example.com",
            "api_key": "api-key",
            "org_id": 1,
            "entity_ids": [1, 2, 3],
            "include_dependencies": true,
            "canvas_width": 1600,
            "canvas_height": 900
        }

    Returns:
        200: Import successful with nodes and connectors
        400: Invalid request
        503: Elder service unavailable
    """
    data = request.get_json() or {}

    drawing_id = data.get("drawing_id", "").strip()
    base_url = data.get("base_url", "").strip()
    api_key = data.get("api_key", "").strip()
    org_id = data.get("org_id")
    entity_ids = data.get("entity_ids", [])
    include_dependencies = data.get("include_dependencies", True)
    canvas_width = data.get("canvas_width", 1600)
    canvas_height = data.get("canvas_height", 900)

    if not all([drawing_id, base_url, api_key, org_id]):
        return jsonify({
            "success": False,
            "error": "drawing_id, base_url, api_key, and org_id are required"
        }), 400

    try:
        client = ElderClient(base_url=base_url, api_key=api_key)

        # Fetch entities
        all_entities = await client.get_entities(org_id=org_id, limit=1000)

        # Filter by requested IDs if provided
        if entity_ids:
            entities = [e for e in all_entities if e.id in entity_ids]
        else:
            entities = all_entities

        if not entities:
            return jsonify({
                "success": True,
                "message": "No entities found to import",
                "nodes": [],
                "connectors": [],
            }), 200

        # Calculate layout positions
        positions = ElderClient.calculate_layout_positions(
            entities,
            [],
            canvas_width=canvas_width,
            canvas_height=canvas_height,
        )

        # Map entities to nodes
        nodes = []
        entity_id_to_node_id = {}

        for entity in entities:
            pos = positions.get(entity.id, {"x": 0, "y": 0})
            node = ElderClient.map_entity_to_shape(entity, x=pos["x"], y=pos["y"])
            nodes.append(node.to_dict())
            entity_id_to_node_id[entity.id] = node.id

        # Fetch and map dependencies if requested
        connectors = []
        if include_dependencies:
            try:
                dependencies = await client.get_relationships(org_id=org_id)

                # Filter dependencies to only include imported entities
                entity_id_set = {e.id for e in entities}
                filtered_deps = [
                    d for d in dependencies
                    if d.source_entity_id in entity_id_set
                    and d.target_entity_id in entity_id_set
                ]

                # Map dependencies to connectors
                for dep in filtered_deps:
                    source_node_id = entity_id_to_node_id.get(
                        dep.source_entity_id
                    )
                    target_node_id = entity_id_to_node_id.get(
                        dep.target_entity_id
                    )

                    if source_node_id and target_node_id:
                        connector = ElderClient.map_relationship_to_connector(
                            dep,
                            source_node_id,
                            target_node_id,
                        )
                        connectors.append(connector.to_dict())
            except Exception as e:
                logger.warning(f"Failed to fetch dependencies: {e}")

        return jsonify({
            "success": True,
            "message": f"Imported {len(nodes)} entities and {len(connectors)} relationships",
            "nodes": nodes,
            "connectors": connectors,
            "entity_count": len(nodes),
            "relationship_count": len(connectors),
        }), 200

    except Exception as e:
        logger.error(f"Failed to import from Elder: {e}")
        return jsonify({
            "success": False,
            "error": f"Import failed: {str(e)}"
        }), 503


@elder_v1_bp.route("/health", methods=["GET"])
async def health_check():
    """Health check endpoint.

    Returns:
        200: Service is healthy
    """
    return jsonify({
        "status": "healthy",
        "service": "elder-integration",
    }), 200
