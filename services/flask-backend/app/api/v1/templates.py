"""Templates Endpoints for API v1.

Provides CRUD operations for drawing templates.
Templates are managed as drawings with is_template=true in the database.
"""

from flask import Blueprint, current_app, jsonify, request

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...services.drawing_storage_service import DrawingStorageService

templates_v1_bp = Blueprint("templates_v1", __name__, url_prefix="/templates")


def serialize_template(template, version=None):
    """Serialize a template (drawing) row to JSON-friendly dict."""
    result = {
        "id": str(template.id),
        "name": template.title,
        "description": template.description or "",
        "category": "custom",  # Default category for custom templates
        "created_by_id": (
            str(template.created_by_id) if template.created_by_id else None
        ),
        "owner_id": str(template.owner_id) if template.owner_id else None,
        "is_public": template.is_public,
        "tags": template.tags or [],
        "thumbnail_url": template.thumbnail_url,
        "status": template.status,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }
    if version:
        result["content"] = version.content_json or {"nodes": [], "edges": []}
        result["version"] = version.version_number
    return result


@templates_v1_bp.route("", methods=["GET"])
@auth_required
@scopes_required("templates:read")
def list_templates():
    """List all available templates.

    Query parameters:
        - category: Filter by category (optional)
        - search: Search templates by name (optional)

    Returns:
        JSON array of templates (public templates + user's own templates)
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()
        category = request.args.get("category", None)
        search = request.args.get("search", None)

        # Query templates: public templates OR user's own templates
        # Templates are drawings with is_template=true
        query = (db.drawings.is_template == True) & (
            (db.drawings.is_public == True)
            | (db.drawings.created_by_id == user_id)
            | (db.drawings.owner_id == user_id)
        )

        templates = db(query).select(orderby=~db.drawings.updated_at)

        # Apply filters
        result = []
        for template in templates:
            # Apply search filter
            if search:
                search_lower = search.lower()
                if not (
                    search_lower in template.title.lower()
                    or search_lower in (template.description or "").lower()
                ):
                    continue
            result.append(serialize_template(template))

        return (
            jsonify(
                {
                    "success": True,
                    "count": len(result),
                    "templates": result,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing templates: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>", methods=["GET"])
@auth_required
@scopes_required("templates:read")
def get_template(template_id: str):
    """Get a specific template by ID.

    Args:
        template_id: Template identifier

    Returns:
        JSON template object with full content
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query template
        template = db.drawings(template_id)
        if not template or not template.is_template:
            return jsonify({"success": False, "error": "Template not found"}), 404

        # Check access (owner, creator, or public)
        has_access = (
            template.created_by_id == user_id
            or template.owner_id == user_id
            or template.is_public
        )
        if not has_access:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Get latest version with content
        version = (
            db(db.drawing_versions.drawing_id == template.id)
            .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
            .first()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "template": serialize_template(template, version),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting template {template_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("", methods=["POST"])
@auth_required
@scopes_required("templates:write")
def create_template():
    """Create a new template from a drawing.

    Expected JSON body:
        {
            "name": "My Template",
            "description": "Template description",
            "drawing_id": "drawing_id",
            "is_public": false
        }

    Returns:
        JSON created template object
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        data = request.get_json() or {}
        db = get_db()

        # Validate required fields
        if not data.get("name"):
            return (
                jsonify({"success": False, "error": "Template name is required"}),
                400,
            )

        drawing_id = data.get("drawing_id")
        if not drawing_id:
            return jsonify({"success": False, "error": "Drawing ID is required"}), 400

        # Get the source drawing to copy content from
        source_drawing = db.drawings(drawing_id)
        if not source_drawing:
            return jsonify({"success": False, "error": "Source drawing not found"}), 404

        # Get the latest version of the source drawing
        source_version = (
            db(db.drawing_versions.drawing_id == source_drawing.id)
            .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
            .first()
        )

        # Create new template (as a drawing with is_template=True)
        template_id = db.drawings.insert(
            tenant_id=1,
            title=data.get("name"),
            description=data.get("description", ""),
            created_by_id=user_id,
            owner_id=user_id,
            user_id=user_id,
            is_public=data.get("is_public", False),
            is_template=True,
            status="published",
        )
        db.commit()

        # Copy content from source drawing to template
        template_content = (
            source_version.content_json
            if source_version
            else {"nodes": [], "edges": []}
        )

        # Create initial version with content
        db.drawing_versions.insert(
            drawing_id=template_id,
            version_number=1,
            created_by_id=user_id,
            content_json=template_content,
            change_summary="Initial version from drawing",
        )
        db.commit()

        # Save content to object storage
        try:
            DrawingStorageService.save_content(
                drawing_id=template_id,
                content=template_content,
                version=1,
                user_id=user_id,
            )
        except Exception as storage_err:
            current_app.logger.warning(
                f"Failed to save to object storage: {storage_err}"
            )

        # Get the created template
        template = db.drawings(template_id)
        if not template:
            return (
                jsonify({"success": False, "error": "Failed to create template"}),
                500,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "template": serialize_template(template),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating template: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>", methods=["PUT"])
@auth_required
@scopes_required("templates:write")
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
        user_id = user["id"]
        data = request.get_json() or {}
        db = get_db()

        # Query template
        template = db.drawings(template_id)
        if not template or not template.is_template:
            return jsonify({"success": False, "error": "Template not found"}), 404

        # Check ownership
        is_owner = template.created_by_id == user_id or template.owner_id == user_id
        if not is_owner:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Update template metadata
        update_data = {"updated_by_id": user_id}
        if "name" in data:
            update_data["title"] = data["name"]
        if "description" in data:
            update_data["description"] = data["description"]
        if "is_public" in data:
            update_data["is_public"] = data["is_public"]

        template.update_record(**update_data)
        db.commit()

        # Fetch updated template
        template = db.drawings(template_id)

        return (
            jsonify(
                {
                    "success": True,
                    "template": serialize_template(template),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating template {template_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>", methods=["DELETE"])
@auth_required
@scopes_required("templates:delete")
def delete_template(template_id: str):
    """Delete a template.

    Args:
        template_id: Template identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query template
        template = db.drawings(template_id)
        if not template or not template.is_template:
            return jsonify({"success": False, "error": "Template not found"}), 404

        # Check ownership
        is_owner = template.created_by_id == user_id or template.owner_id == user_id
        if not is_owner:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Delete from object storage first
        try:
            DrawingStorageService.delete_content(int(template_id))
        except Exception as storage_err:
            current_app.logger.warning(
                f"Failed to delete from object storage: {storage_err}"
            )

        # Delete template (cascade will handle versions, shapes, etc.)
        db(db.drawings.id == template_id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Template deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting template {template_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@templates_v1_bp.route("/<template_id>/use", methods=["POST"])
@auth_required
@scopes_required("templates:read", "drawings:write")
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
        user_id = user["id"]
        data = request.get_json() or {}
        db = get_db()

        # Validate required fields
        if not data.get("name"):
            return jsonify({"success": False, "error": "Drawing name is required"}), 400

        # Get template
        template = db.drawings(template_id)
        if not template or not template.is_template:
            return jsonify({"success": False, "error": "Template not found"}), 404

        # Check access (public templates or user's own templates)
        has_access = (
            template.created_by_id == user_id
            or template.owner_id == user_id
            or template.is_public
        )
        if not has_access:
            return jsonify({"success": False, "error": "Access denied"}), 403

        # Get latest version of template with content
        template_version = (
            db(db.drawing_versions.drawing_id == template.id)
            .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
            .first()
        )

        template_content = (
            template_version.content_json
            if template_version
            else {"nodes": [], "edges": []}
        )

        # Create new drawing from template
        drawing_id = db.drawings.insert(
            tenant_id=1,
            title=data.get("name"),
            description=data.get("description", ""),
            created_by_id=user_id,
            owner_id=user_id,
            user_id=user_id,
            is_public=False,
            is_template=False,
            status="draft",
        )
        db.commit()

        # Create initial version with template content
        db.drawing_versions.insert(
            drawing_id=drawing_id,
            version_number=1,
            created_by_id=user_id,
            content_json=template_content,
            change_summary="Created from template",
        )
        db.commit()

        # Save content to object storage
        try:
            DrawingStorageService.save_content(
                drawing_id=drawing_id,
                content=template_content,
                version=1,
                user_id=user_id,
            )
        except Exception as storage_err:
            current_app.logger.warning(
                f"Failed to save to object storage: {storage_err}"
            )

        # Get the created drawing
        drawing = db.drawings(drawing_id)
        if not drawing:
            return jsonify({"success": False, "error": "Failed to create drawing"}), 500

        return (
            jsonify(
                {
                    "success": True,
                    "drawing": {
                        "id": drawing.id,
                        "name": drawing.title,
                        "description": drawing.description or "",
                        "created_by_id": drawing.created_by_id,
                        "owner_id": drawing.owner_id,
                        "is_public": drawing.is_public,
                        "status": drawing.status,
                        "created_at": (
                            drawing.created_at.isoformat()
                            if drawing.created_at
                            else None
                        ),
                        "updated_at": (
                            drawing.updated_at.isoformat()
                            if drawing.updated_at
                            else None
                        ),
                    },
                    "drawing_id": drawing_id,
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(
            f"Error creating drawing from template: {e}", exc_info=True
        )
        return jsonify({"success": False, "error": str(e)}), 500
