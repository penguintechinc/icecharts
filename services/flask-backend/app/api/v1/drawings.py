"""Drawings Endpoints for API v1.

Provides CRUD operations and export functionality for IceCharts drawings.
Drawing content is stored in S3-compatible object storage (MinIO for dev, AWS S3 for prod).
"""

import datetime
import io

from flask import Blueprint, current_app, jsonify, request, send_file

from ...middleware import auth_required, get_current_user, scopes_required
from ...models import get_db
from ...schemas.drawing_schemas import CreateDrawingRequest, UpdateDrawingRequest
from ...services.drawing_storage_service import DrawingStorageService
from ...services.export_service import ExportOptions, ExportService
from ...tasks.export_tasks import (
    export_drawing_task,
    get_export_metadata,
    get_export_result,
    get_export_status,
)
from ...utils.validation import validate_json

drawings_v1_bp = Blueprint("drawings_v1", __name__, url_prefix="/drawings")


def serialize_drawing(drawing, version=None):
    """Serialize a drawing row to JSON-friendly dict."""
    result = {
        "id": str(drawing.id),
        "name": drawing.title,
        "description": drawing.description or "",
        "created_by_id": str(drawing.created_by_id) if drawing.created_by_id else None,
        "owner_id": str(drawing.owner_id) if drawing.owner_id else None,
        "is_public": drawing.is_public,
        "is_template": drawing.is_template,
        "status": drawing.status,
        "tags": drawing.tags or [],
        "thumbnail_url": drawing.thumbnail_url,
        "created_at": drawing.created_at.isoformat() if drawing.created_at else None,
        "updated_at": drawing.updated_at.isoformat() if drawing.updated_at else None,
    }
    if version:
        result["content"] = version.content_json or {"nodes": [], "edges": []}
        result["version"] = version.version_number
    return result


@drawings_v1_bp.route("", methods=["GET"])
@auth_required
@scopes_required("drawings:read")
def list_drawings():
    """List all drawings for current user.

    Returns:
        JSON array of drawings with metadata
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query drawings owned by or created by the user
        drawings = db(
            (db.drawings.created_by_id == user_id)
            | (db.drawings.owner_id == user_id)
            | (db.drawings.user_id == user_id)
        ).select(orderby=~db.drawings.updated_at)

        result = [serialize_drawing(d) for d in drawings]

        return (
            jsonify(
                {
                    "success": True,
                    "count": len(result),
                    "items": result,
                    "drawings": result,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error listing drawings: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>", methods=["GET"])
@auth_required
@scopes_required("drawings:read")
def get_drawing(drawing_id: str):
    """Get a specific drawing by ID.

    Args:
        drawing_id: Drawing identifier

    Returns:
        JSON drawing object with content and metadata
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query drawing
        drawing = db.drawings(drawing_id)
        if not drawing:
            return jsonify({"error": "Drawing not found"}), 404

        # Check access (owner, creator, or public)
        has_access = (
            drawing.created_by_id == user_id
            or drawing.owner_id == user_id
            or drawing.user_id == user_id
            or drawing.is_public
        )
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        # Get latest version with content
        version = (
            db(db.drawing_versions.drawing_id == drawing.id)
            .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
            .first()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "drawing": serialize_drawing(drawing, version),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting drawing {drawing_id}: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("", methods=["POST"])
@auth_required
@scopes_required("drawings:write")
@validate_json(CreateDrawingRequest)
def create_drawing(validated_data: CreateDrawingRequest):
    """Create a new drawing.

    Expected JSON body:
        {
            "name": "My Drawing",
            "description": "Optional description",
            "content": {...},
            "visibility": "private",
            "is_template": false,
            "tags": ["tag1", "tag2"]
        }

    Returns:
        JSON created drawing object
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # All fields are already validated by Pydantic
        name = validated_data.name
        description = validated_data.description or ""
        content = validated_data.content
        is_public = validated_data.visibility == "public"
        is_template = validated_data.is_template or False
        tags = validated_data.tags or []

        # Create drawing record
        drawing_id = db.drawings.insert(
            tenant_id=1,
            title=name,
            description=description,
            created_by_id=user_id,
            owner_id=user_id,
            user_id=user_id,
            is_public=is_public,
            is_template=is_template,
            tags=tags,
            status="draft",
        )
        db.commit()

        # Create initial version with content
        db.drawing_versions.insert(
            drawing_id=drawing_id,
            version_number=1,
            created_by_id=user_id,
            content_json=content,
            change_summary="Initial version",
        )
        db.commit()

        # Save content to object storage (MinIO/S3)
        try:
            DrawingStorageService.save_content(
                drawing_id=drawing_id,
                content=content,
                version=1,
                user_id=user_id,
            )
        except Exception as storage_err:
            current_app.logger.warning(
                f"Failed to save to object storage: {storage_err}"
            )
            # Continue even if storage fails - content is in DB

        # Fetch the created drawing
        drawing = db.drawings(drawing_id)

        return (
            jsonify(
                {
                    "success": True,
                    "drawing": serialize_drawing(drawing),
                }
            ),
            201,
        )

    except Exception as e:
        current_app.logger.error(f"Error creating drawing: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>", methods=["PUT"])
@auth_required
@scopes_required("drawings:write")
@validate_json(UpdateDrawingRequest)
def update_drawing(drawing_id: str, validated_data: UpdateDrawingRequest):
    """Update a drawing.

    Args:
        drawing_id: Drawing identifier

    Expected JSON body:
        {
            "name": "Updated Name",
            "description": "Updated description",
            "content": {...},
            "visibility": "public",
            "tags": ["tag1", "tag2"],
            "status": "published"
        }

    Returns:
        JSON updated drawing object
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query drawing
        drawing = db.drawings(drawing_id)
        if not drawing:
            return jsonify({"error": "Drawing not found"}), 404

        # Check ownership
        is_owner = (
            drawing.created_by_id == user_id
            or drawing.owner_id == user_id
            or drawing.user_id == user_id
        )
        if not is_owner:
            return jsonify({"error": "Access denied"}), 403

        # Update drawing metadata (all fields validated by Pydantic)
        update_data = {"updated_by_id": user_id}
        if validated_data.name is not None:
            update_data["title"] = validated_data.name
        if validated_data.description is not None:
            update_data["description"] = validated_data.description
        if validated_data.visibility is not None:
            update_data["is_public"] = validated_data.visibility == "public"
        if validated_data.is_template is not None:
            update_data["is_template"] = validated_data.is_template
        if validated_data.tags is not None:
            update_data["tags"] = validated_data.tags
        if validated_data.status is not None:
            update_data["status"] = validated_data.status

        drawing.update_record(**update_data)
        db.commit()

        # If content is provided, create new version
        if validated_data.content is not None:
            # Get current max version
            max_version = (
                db(db.drawing_versions.drawing_id == drawing_id)
                .select(db.drawing_versions.version_number.max())
                .first()[db.drawing_versions.version_number.max()]
                or 0
            )

            new_version = max_version + 1
            db.drawing_versions.insert(
                drawing_id=drawing_id,
                version_number=new_version,
                created_by_id=user_id,
                content_json=validated_data.content,
                change_summary="Updated",
            )
            db.commit()

            # Save content to object storage (MinIO/S3)
            try:
                DrawingStorageService.save_content(
                    drawing_id=int(drawing_id),
                    content=validated_data.content,
                    version=new_version,
                    user_id=user_id,
                )
            except Exception as storage_err:
                current_app.logger.warning(
                    f"Failed to save to object storage: {storage_err}"
                )
                # Continue even if storage fails - content is in DB

        # Fetch updated drawing with latest version
        drawing = db.drawings(drawing_id)
        version = (
            db(db.drawing_versions.drawing_id == drawing_id)
            .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
            .first()
        )

        return (
            jsonify(
                {
                    "success": True,
                    "drawing": serialize_drawing(drawing, version),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error updating drawing {drawing_id}: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>", methods=["DELETE"])
@auth_required
@scopes_required("drawings:delete")
def delete_drawing(drawing_id: str):
    """Delete a drawing.

    Args:
        drawing_id: Drawing identifier

    Returns:
        JSON success/error response
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Query drawing
        drawing = db.drawings(drawing_id)
        if not drawing:
            return jsonify({"error": "Drawing not found"}), 404

        # Check ownership
        is_owner = (
            drawing.created_by_id == user_id
            or drawing.owner_id == user_id
            or drawing.user_id == user_id
        )
        if not is_owner:
            return jsonify({"error": "Access denied"}), 403

        # Delete from object storage first
        try:
            DrawingStorageService.delete_content(int(drawing_id))
        except Exception as storage_err:
            current_app.logger.warning(
                f"Failed to delete from object storage: {storage_err}"
            )
            # Continue with DB deletion even if storage fails

        # Delete drawing (cascade will handle versions, shapes, etc.)
        db(db.drawings.id == drawing_id).delete()
        db.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Drawing deleted successfully",
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting drawing {drawing_id}: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>/export", methods=["POST"])
@auth_required
@scopes_required("exports:create")
def export_drawing(drawing_id: str):
    """Export drawing with automatic background job handling for large exports.

    Request JSON body:
        {
            "format": "png",  # png, jpg, svg, pdf, json
            "width": 800,
            "height": 600,
            "quality": 95,  # for PNG/JPG
            "include_background": true,
            "page_size": "A4"  # for PDF
        }

    Query parameters:
        - async: Force async processing (default: false for small, true for large)

    Returns:
        - 200 with binary file: For small exports (<2000x2000px)
        - 202 with job_id: For large exports (queued as background job)
    """
    try:
        user = get_current_user()
        user_id = user["id"]
        db = get_db()

        # Get drawing
        drawing = db.drawings(drawing_id)
        if not drawing:
            return jsonify({"error": "Drawing not found"}), 404

        # Check access
        has_access = (
            drawing.created_by_id == user_id
            or drawing.owner_id == user_id
            or drawing.user_id == user_id
        )
        if not has_access:
            return jsonify({"error": "Access denied"}), 403

        # Get latest version with content
        version = (
            db(db.drawing_versions.drawing_id == drawing.id)
            .select(orderby=~db.drawing_versions.version_number, limitby=(0, 1))
            .first()
        )

        if not version:
            return jsonify({"error": "No drawing content found"}), 404

        # Get export parameters from request
        data = request.get_json() or {}
        export_format = data.get("format", "png").lower()
        width = data.get("width", 800)
        height = data.get("height", 600)
        quality = data.get("quality", 95 if export_format == "png" else 85)
        include_background = data.get("include_background", True)
        page_size = data.get("page_size", "A4")
        force_async = request.args.get("async", "false").lower() == "true"

        # Validate format
        if export_format not in ExportService.VALID_FORMATS:
            return (
                jsonify(
                    {
                        "error": f"Invalid format. Must be one of: {ExportService.VALID_FORMATS}"
                    }
                ),
                400,
            )

        # Validate dimensions
        if width <= 0 or height <= 0:
            return jsonify({"error": "Width and height must be positive"}), 400
        if not (1 <= quality <= 100):
            return jsonify({"error": "Quality must be between 1 and 100"}), 400

        # Determine if should use background job
        use_background_job = (
            force_async
            or width > 2000
            or height > 2000
            or export_format in ["png", "jpg"]
        )

        if use_background_job:
            # Queue background job
            drawing_data = version.content_json or {"elements": []}
            options = {
                "format": export_format,
                "width": width,
                "height": height,
                "quality": quality,
                "include_background": include_background,
                "page_size": page_size,
            }

            task = export_drawing_task.delay(
                drawing_id=int(drawing_id),
                format=export_format,
                options=options,
                drawing_data=drawing_data,
            )

            current_app.logger.info(
                f"Queued background export job {task.id} for drawing {drawing_id}"
            )

            return (
                jsonify(
                    {
                        "job_id": task.id,
                        "status": "processing",
                        "message": "Export job queued for processing",
                    }
                ),
                202,
            )

        else:
            # Synchronous export for small files
            drawing_data = version.content_json or {"elements": []}

            export_options = ExportOptions(
                format=export_format,
                width=width,
                height=height,
                quality=quality,
                page_size=page_size,
                include_background=include_background,
            )

            exported_content = ExportService.export(export_options, drawing_data)

            # Determine mimetype and filename
            if export_format == "png":
                mimetype = "image/png"
                filename = f"{drawing.title or drawing_id}.png"
            elif export_format == "jpg":
                mimetype = "image/jpeg"
                filename = f"{drawing.title or drawing_id}.jpg"
            elif export_format == "svg":
                mimetype = "image/svg+xml"
                filename = f"{drawing.title or drawing_id}.svg"
            elif export_format == "pdf":
                mimetype = "application/pdf"
                filename = f"{drawing.title or drawing_id}.pdf"
            else:  # json
                mimetype = "application/json"
                filename = f"{drawing.title or drawing_id}.json"

            return send_file(
                (
                    io.BytesIO(exported_content)
                    if isinstance(exported_content, bytes)
                    else io.BytesIO(exported_content.encode("utf-8"))
                ),
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename,
            )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error exporting drawing {drawing_id}: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>/export/png", methods=["GET"])
@auth_required
def export_drawing_png(drawing_id: str):
    """Export drawing as PNG image (legacy endpoint).

    Query parameters:
        - width: Image width (default: 800)
        - height: Image height (default: 600)
        - quality: PNG quality 1-100 (default: 95)
        - include_background: Include background (default: true)

    Returns:
        PNG image file
    """
    try:
        user = get_current_user()

        # Get query parameters
        width = request.args.get("width", 800, type=int)
        height = request.args.get("height", 600, type=int)
        quality = request.args.get("quality", 95, type=int)
        include_background = (
            request.args.get("include_background", "true").lower() == "true"
        )

        # Validate dimensions
        if width <= 0 or height <= 0:
            return jsonify({"error": "Width and height must be positive"}), 400
        if not (1 <= quality <= 100):
            return jsonify({"error": "Quality must be between 1 and 100"}), 400

        # TODO: Load drawing from database, verify user access
        # Placeholder drawing data
        drawing_data = {
            "width": width,
            "height": height,
            "background_color": (255, 255, 255),
            "include_background": include_background,
            "elements": [],
        }

        # Export to PNG
        png_bytes = ExportService.export_to_png(
            drawing_data,
            width=width,
            height=height,
            quality=quality,
            include_background=include_background,
        )

        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=f"{drawing_id}.png",
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>/export/svg", methods=["GET"])
@auth_required
def export_drawing_svg(drawing_id: str):
    """Export drawing as SVG vector image.

    Returns:
        SVG file
    """
    try:
        user = get_current_user()

        # TODO: Load drawing from database, verify user access
        # Placeholder drawing data
        drawing_data = {
            "width": 800,
            "height": 600,
            "background_color": "rgb(255,255,255)",
            "include_background": True,
            "elements": [],
        }

        # Export to SVG
        svg_content = ExportService.export_to_svg(drawing_data)

        return send_file(
            io.BytesIO(svg_content.encode("utf-8")),
            mimetype="image/svg+xml",
            as_attachment=True,
            download_name=f"{drawing_id}.svg",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>/export/pdf", methods=["GET"])
@auth_required
def export_drawing_pdf(drawing_id: str):
    """Export drawing as PDF document.

    Query parameters:
        - page_size: PDF page size (default: A4)
                     Valid: A0, A1, A2, A3, A4, A5, A6, Letter, Legal, Tabloid, Ledger
        - include_background: Include background (default: true)

    Returns:
        PDF file
    """
    try:
        user = get_current_user()

        # Get query parameters
        page_size = request.args.get("page_size", "A4")
        include_background = (
            request.args.get("include_background", "true").lower() == "true"
        )

        # TODO: Load drawing from database, verify user access
        # Placeholder drawing data
        drawing_data = {
            "width": 800,
            "height": 600,
            "background_color": "rgb(255,255,255)",
            "include_background": include_background,
            "elements": [],
        }

        # Export to PDF
        pdf_bytes = ExportService.export_to_pdf(
            drawing_data,
            page_size=page_size,
            include_background=include_background,
        )

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{drawing_id}.pdf",
        )

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/<drawing_id>/export/json", methods=["GET"])
@auth_required
def export_drawing_json(drawing_id: str):
    """Export drawing as JSON data.

    Returns:
        JSON file with drawing data
    """
    try:
        user = get_current_user()

        # TODO: Load drawing from database, verify user access
        # Placeholder drawing data
        drawing_data = {
            "id": drawing_id,
            "name": "Drawing",
            "width": 800,
            "height": 600,
            "elements": [],
        }

        # Export to JSON
        json_content = ExportService.export_to_json(drawing_data)

        return send_file(
            io.BytesIO(json_content.encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name=f"{drawing_id}.json",
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/exports/<job_id>/status", methods=["GET"])
@auth_required
def get_export_job_status(job_id: str):
    """Get status of a background export job.

    Args:
        job_id: Celery task ID from export response

    Returns:
        JSON with job status and progress
    """
    try:
        user = get_current_user()

        # Get job status from Redis
        status = get_export_status(job_id)

        if not status:
            return jsonify({"error": "Job not found or expired"}), 404

        return (
            jsonify(
                {
                    "success": True,
                    "job_id": job_id,
                    "status": status.get("status", "unknown"),
                    "progress": status.get("progress", 0),
                    "error": status.get("error"),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error getting export status {job_id}: {e}")
        return jsonify({"error": str(e)}), 500


@drawings_v1_bp.route("/exports/<job_id>/download", methods=["GET"])
@auth_required
def download_export_result(job_id: str):
    """Download completed export result.

    Args:
        job_id: Celery task ID from export response

    Returns:
        Binary file with export content
    """
    try:
        user = get_current_user()

        # Get metadata and content from Redis
        metadata = get_export_metadata(job_id)
        content = get_export_result(job_id)

        if not metadata or not content:
            return jsonify({"error": "Export not found or expired"}), 404

        # Determine mimetype and filename
        export_format = metadata.get("format", "png")
        drawing_id = metadata.get("drawing_id")

        if export_format == "png":
            mimetype = "image/png"
            filename = f"drawing_{drawing_id}.png"
        elif export_format == "jpg":
            mimetype = "image/jpeg"
            filename = f"drawing_{drawing_id}.jpg"
        elif export_format == "svg":
            mimetype = "image/svg+xml"
            filename = f"drawing_{drawing_id}.svg"
        elif export_format == "pdf":
            mimetype = "application/pdf"
            filename = f"drawing_{drawing_id}.pdf"
        else:  # json
            mimetype = "application/json"
            filename = f"drawing_{drawing_id}.json"

        return send_file(
            io.BytesIO(content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading export {job_id}: {e}")
        return jsonify({"error": str(e)}), 500
