"""Shape Libraries Endpoints for API v1."""

from datetime import datetime
from typing import Optional

from flask import Blueprint, jsonify, request

from ...middleware import auth_required, get_current_user
from ...models import get_db

libraries_v1_bp = Blueprint("libraries_v1", __name__, url_prefix="/libraries")


def get_library_by_id(library_id: int) -> Optional[dict]:
    """Get library by ID."""
    db = get_db()
    library = db(db.shape_libraries.id == library_id).select().first()
    return library.as_dict() if library else None


def user_can_access_library(user_id: int, library_id: int) -> bool:
    """Check if user can access a library."""
    library = get_library_by_id(library_id)

    if not library:
        return False

    # Public libraries are accessible to all
    if library.get("is_public"):
        return True

    # Owner can always access
    if library["owner_id"] == user_id:
        return True

    return False


@libraries_v1_bp.route("", methods=["GET"])
@auth_required
def list_libraries():
    """List shape libraries."""
    user = get_current_user()
    db = get_db()

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    search = request.args.get("search", "").strip()
    show_public = request.args.get("public", "true").lower() == "true"

    offset = (page - 1) * per_page

    # Build query: user's libraries or public libraries
    if show_public:
        query = db(
            (db.shape_libraries.owner_id == user["id"]) |
            (db.shape_libraries.is_public == True)
        )
    else:
        query = db(db.shape_libraries.owner_id == user["id"])

    # Apply search filter
    if search:
        query = query & (
            db.shape_libraries.name.contains(search) |
            db.shape_libraries.description.contains(search)
        )

    libraries = query.select(
        orderby=db.shape_libraries.created_at,
        limitby=(offset, offset + per_page),
    )
    total = query.count()

    return jsonify({
        "libraries": [lib.as_dict() for lib in libraries],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }), 200


@libraries_v1_bp.route("", methods=["POST"])
@auth_required
def create_library():
    """Create a new shape library."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    is_public = data.get("is_public", False)

    # Validation
    if not name:
        return jsonify({"error": "Library name is required"}), 400

    db = get_db()

    # Create library
    library_id = db.shape_libraries.insert(
        name=name,
        description=description,
        owner_id=user["id"],
        is_public=is_public,
    )
    db.commit()

    library = get_library_by_id(library_id)

    return jsonify({
        "message": "Library created successfully",
        "library": library,
    }), 201


@libraries_v1_bp.route("/<int:library_id>", methods=["GET"])
@auth_required
def get_library(library_id: int):
    """Get library details with shapes."""
    user = get_current_user()

    # Check access
    if not user_can_access_library(user["id"], library_id):
        return jsonify({"error": "Library not found or access denied"}), 404

    library = get_library_by_id(library_id)

    # Get shapes in library
    db = get_db()
    shapes = db(db.library_shapes.library_id == library_id).select(
        orderby=db.library_shapes.name,
    )

    library["shapes"] = [s.as_dict() for s in shapes]
    library["shape_count"] = len(shapes)

    return jsonify({"library": library}), 200


@libraries_v1_bp.route("/<int:library_id>", methods=["PUT"])
@auth_required
def update_library(library_id: int):
    """Update library metadata."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    library = get_library_by_id(library_id)
    if not library:
        return jsonify({"error": "Library not found"}), 404

    # Only owner can update
    if library["owner_id"] != user["id"]:
        return jsonify({"error": "Only the owner can update this library"}), 403

    db = get_db()
    update_data = {}

    if "name" in data:
        update_data["name"] = data["name"].strip()
    if "description" in data:
        update_data["description"] = data["description"].strip()
    if "is_public" in data:
        update_data["is_public"] = data["is_public"]

    if update_data:
        db(db.shape_libraries.id == library_id).update(**update_data)
        db.commit()

    updated_library = get_library_by_id(library_id)

    return jsonify({
        "message": "Library updated successfully",
        "library": updated_library,
    }), 200


@libraries_v1_bp.route("/<int:library_id>", methods=["DELETE"])
@auth_required
def delete_library(library_id: int):
    """Delete library and all its shapes."""
    user = get_current_user()
    library = get_library_by_id(library_id)

    if not library:
        return jsonify({"error": "Library not found"}), 404

    # Only owner can delete
    if library["owner_id"] != user["id"]:
        return jsonify({"error": "Only the owner can delete this library"}), 403

    db = get_db()

    # Delete all shapes in library
    db(db.library_shapes.library_id == library_id).delete()

    # Delete library
    db(db.shape_libraries.id == library_id).delete()
    db.commit()

    return jsonify({
        "message": "Library deleted successfully",
    }), 200


@libraries_v1_bp.route("/<int:library_id>/shapes", methods=["GET"])
@auth_required
def list_library_shapes(library_id: int):
    """List shapes in a library."""
    user = get_current_user()

    # Check access
    if not user_can_access_library(user["id"], library_id):
        return jsonify({"error": "Library not found or access denied"}), 404

    db = get_db()

    shapes = db(db.library_shapes.library_id == library_id).select(
        orderby=db.library_shapes.name,
    )

    return jsonify({
        "shapes": [s.as_dict() for s in shapes],
        "total": len(shapes),
    }), 200


@libraries_v1_bp.route("/<int:library_id>/shapes", methods=["POST"])
@auth_required
def add_library_shape(library_id: int):
    """Add a shape to library."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    library = get_library_by_id(library_id)
    if not library:
        return jsonify({"error": "Library not found"}), 404

    # Only owner can add shapes
    if library["owner_id"] != user["id"]:
        return jsonify({"error": "Only the owner can add shapes to this library"}), 403

    name = data.get("name", "").strip()
    shape_data = data.get("shape_data", {})

    # Validation
    if not name:
        return jsonify({"error": "Shape name is required"}), 400

    if not shape_data:
        return jsonify({"error": "Shape data is required"}), 400

    db = get_db()

    # Create shape
    shape_id = db.library_shapes.insert(
        library_id=library_id,
        name=name,
        description=data.get("description", ""),
        shape_data=shape_data,
        category=data.get("category", "custom"),
    )
    db.commit()

    shape = db(db.library_shapes.id == shape_id).select().first()

    return jsonify({
        "message": "Shape added to library successfully",
        "shape": shape.as_dict() if shape else None,
    }), 201


@libraries_v1_bp.route("/<int:library_id>/shapes/<int:shape_id>", methods=["GET"])
@auth_required
def get_library_shape(library_id: int, shape_id: int):
    """Get a specific shape from library."""
    user = get_current_user()

    # Check access
    if not user_can_access_library(user["id"], library_id):
        return jsonify({"error": "Library not found or access denied"}), 404

    db = get_db()

    shape = db(
        (db.library_shapes.id == shape_id) &
        (db.library_shapes.library_id == library_id)
    ).select().first()

    if not shape:
        return jsonify({"error": "Shape not found"}), 404

    return jsonify({"shape": shape.as_dict()}), 200


@libraries_v1_bp.route("/<int:library_id>/shapes/<int:shape_id>", methods=["PUT"])
@auth_required
def update_library_shape(library_id: int, shape_id: int):
    """Update a shape in library."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    library = get_library_by_id(library_id)
    if not library:
        return jsonify({"error": "Library not found"}), 404

    # Only owner can update
    if library["owner_id"] != user["id"]:
        return jsonify({"error": "Only the owner can update shapes in this library"}), 403

    db = get_db()

    update_data = {}
    if "name" in data:
        update_data["name"] = data["name"].strip()
    if "description" in data:
        update_data["description"] = data["description"].strip()
    if "shape_data" in data:
        update_data["shape_data"] = data["shape_data"]
    if "category" in data:
        update_data["category"] = data["category"]

    if update_data:
        updated = db(
            (db.library_shapes.id == shape_id) &
            (db.library_shapes.library_id == library_id)
        ).update(**update_data)

        if not updated:
            return jsonify({"error": "Shape not found"}), 404

        db.commit()

    shape = db(db.library_shapes.id == shape_id).select().first()

    return jsonify({
        "message": "Shape updated successfully",
        "shape": shape.as_dict() if shape else None,
    }), 200


@libraries_v1_bp.route("/<int:library_id>/shapes/<int:shape_id>", methods=["DELETE"])
@auth_required
def delete_library_shape(library_id: int, shape_id: int):
    """Delete a shape from library."""
    user = get_current_user()
    library = get_library_by_id(library_id)

    if not library:
        return jsonify({"error": "Library not found"}), 404

    # Only owner can delete
    if library["owner_id"] != user["id"]:
        return jsonify({"error": "Only the owner can delete shapes from this library"}), 403

    db = get_db()

    deleted = db(
        (db.library_shapes.id == shape_id) &
        (db.library_shapes.library_id == library_id)
    ).delete()

    if not deleted:
        return jsonify({"error": "Shape not found"}), 404

    db.commit()

    return jsonify({
        "message": "Shape deleted successfully",
    }), 200


@libraries_v1_bp.route("/<int:library_id>/duplicate", methods=["POST"])
@auth_required
def duplicate_library(library_id: int):
    """Duplicate a library with all its shapes."""
    user = get_current_user()

    # Check access
    if not user_can_access_library(user["id"], library_id):
        return jsonify({"error": "Library not found or access denied"}), 404

    source_library = get_library_by_id(library_id)
    db = get_db()

    # Create new library
    new_library_id = db.shape_libraries.insert(
        name=f"{source_library['name']} (Copy)",
        description=source_library.get("description", ""),
        owner_id=user["id"],
        is_public=False,  # Copies are private by default
    )

    # Copy all shapes
    source_shapes = db(db.library_shapes.library_id == library_id).select()

    for shape in source_shapes:
        db.library_shapes.insert(
            library_id=new_library_id,
            name=shape.name,
            description=shape.description,
            shape_data=shape.shape_data,
            category=shape.category,
        )

    db.commit()

    new_library = get_library_by_id(new_library_id)

    return jsonify({
        "message": "Library duplicated successfully",
        "library": new_library,
    }), 201
