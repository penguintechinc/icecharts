"""Templates Endpoints for API v1.

Provides CRUD operations for drawing templates.
"""

from flask import Blueprint, jsonify, request

from ...middleware import auth_required, get_current_user

templates_v1_bp = Blueprint("templates_v1", __name__, url_prefix="/templates")


@templates_v1_bp.route("", methods=["GET"])
@auth_required
def list_templates():
    """List all available templates.

    Query parameters:
        - category: Filter by category (optional)
        - search: Search templates by name (optional)

    Returns:
        JSON array of templates
    """
    try:
        user = get_current_user()
        category = request.args.get("category", None)
        search = request.args.get("search", None)

        # TODO: Query templates from database
        # For now, return example templates
        templates = [
            {
                "id": "template_1",
                "name": "Blank Canvas",
                "description": "Start with a blank canvas",
                "category": "basic",
                "width": 800,
                "height": 600,
                "thumbnail": "data:image/png;base64,...",
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "id": "template_2",
                "name": "Grid Layout",
                "description": "Canvas with grid background",
                "category": "basic",
                "width": 800,
                "height": 600,
                "thumbnail": "data:image/png;base64,...",
                "created_at": "2024-01-01T00:00:00Z",
            },
        ]

        # Apply filters
        if category:
            templates = [t for t in templates if t["category"] == category]
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t["name"].lower() or search_lower in t["description"].lower()
            ]

        return jsonify({
            "success": True,
            "templates": templates,
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>", methods=["GET"])
@auth_required
def get_template(template_id: str):
    """Get a specific template by ID.

    Args:
        template_id: Template identifier

    Returns:
        JSON template object with full content
    """
    try:
        user = get_current_user()

        # TODO: Query template from database
        # For now, return error
        return jsonify({"success": False, "error": "Template not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("", methods=["POST"])
@auth_required
def create_template():
    """Create a new template from a drawing.

    Expected JSON body:
        {
            "name": "My Template",
            "description": "Template description",
            "category": "custom",
            "drawing_id": "drawing_id",
            "is_public": false
        }

    Returns:
        JSON created template object
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # Validate required fields
        if not data.get("name"):
            return jsonify({"success": False, "error": "Template name is required"}), 400

        drawing_id = data.get("drawing_id")
        if not drawing_id:
            return jsonify({"success": False, "error": "Drawing ID is required"}), 400

        # TODO: Save template to database
        # For now, return placeholder response
        template = {
            "id": "template_custom_1",
            "name": data.get("name"),
            "description": data.get("description", ""),
            "category": data.get("category", "custom"),
            "is_public": data.get("is_public", False),
            "created_by": user["id"],
            "created_at": "2024-01-01T00:00:00Z",
        }

        return jsonify({"success": True, "template": template}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>", methods=["PUT"])
@auth_required
def update_template(template_id: str):
    """Update a template.

    Args:
        template_id: Template identifier

    Expected JSON body:
        {
            "name": "Updated Name",
            "description": "Updated description",
            "is_public": true
        }

    Returns:
        JSON updated template object
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # TODO: Load template from database, verify ownership, update and save
        # For now, return placeholder
        return jsonify({"success": False, "error": "Template not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>", methods=["DELETE"])
@auth_required
def delete_template(template_id: str):
    """Delete a template.

    Args:
        template_id: Template identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()

        # TODO: Load template from database, verify ownership, delete
        # For now, return placeholder
        return jsonify({"success": False, "error": "Template not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>/use", methods=["POST"])
@auth_required
def use_template(template_id: str):
    """Create a new drawing from a template.

    Expected JSON body:
        {
            "name": "My Drawing from Template",
            "description": "Optional description"
        }

    Returns:
        JSON created drawing object
    """
    try:
        user = get_current_user()
        data = request.get_json() or {}

        # Validate required fields
        if not data.get("name"):
            return jsonify({"success": False, "error": "Drawing name is required"}), 400

        # TODO: Load template, create new drawing from it, save to database
        # For now, return placeholder
        drawing = {
            "id": "drawing_from_template_1",
            "name": data.get("name"),
            "template_id": template_id,
            "created_at": "2024-01-01T00:00:00Z",
        }

        return jsonify({"success": True, "drawing": drawing}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
