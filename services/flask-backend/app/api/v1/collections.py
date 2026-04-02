"""Collections Management Endpoints for API v1."""

from app.middleware import auth_required, get_current_user, optional_auth
from app.schemas.collection_schemas import (AddDrawingToCollectionRequest,
                                            CreateCollectionRequest,
                                            ReorderCollectionDrawingsRequest,
                                            UpdateCollectionRequest)
from app.services.collection_service import CollectionService
from app.utils.validation import validate_json
from flask import Blueprint, jsonify, request

collections_v1_bp = Blueprint("collections_v1", __name__, url_prefix="/collections")


@collections_v1_bp.route("", methods=["POST"])
@auth_required
@validate_json(CreateCollectionRequest)
def create_collection(validated_data: CreateCollectionRequest):
    """Create a new collection."""
    user = get_current_user()

    try:
        collection = CollectionService.create_collection(
            owner_id=user["id"],
            name=validated_data.name,
            description=validated_data.description or "",
            share_mode=validated_data.share_mode,
            is_public=validated_data.is_public,
        )

        return jsonify({"collection": collection}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to create collection"}), 500


@collections_v1_bp.route("", methods=["GET"])
@auth_required
def list_collections():
    """List user's accessible collections."""
    user = get_current_user()

    # Get pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Validate pagination
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    try:
        result = CollectionService.list_user_collections(
            user_id=user["id"],
            page=page,
            per_page=per_page,
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "Failed to list collections"}), 500


@collections_v1_bp.route("/<int:collection_id>", methods=["GET"])
@auth_required
def get_collection(collection_id: int):
    """Get collection details."""
    user = get_current_user()

    try:
        collection = CollectionService.get_collection_by_id(
            collection_id=collection_id,
            user_id=user["id"],
        )

        if not collection:
            return jsonify({"error": "Collection not found or access denied"}), 404

        return jsonify({"collection": collection}), 200

    except Exception as e:
        return jsonify({"error": "Failed to get collection"}), 500


@collections_v1_bp.route("/<int:collection_id>", methods=["PUT"])
@auth_required
@validate_json(UpdateCollectionRequest)
def update_collection(collection_id: int, validated_data: UpdateCollectionRequest):
    """Update a collection."""
    user = get_current_user()

    try:
        # Convert validated data to dict, excluding None values
        update_fields = validated_data.model_dump(exclude_none=True)

        collection = CollectionService.update_collection(
            collection_id=collection_id,
            user_id=user["id"],
            **update_fields,
        )

        if not collection:
            return jsonify({"error": "Collection not found"}), 404

        return jsonify({"collection": collection}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to update collection"}), 500


@collections_v1_bp.route("/<int:collection_id>", methods=["DELETE"])
@auth_required
def delete_collection(collection_id: int):
    """Delete a collection."""
    user = get_current_user()

    try:
        deleted = CollectionService.delete_collection(
            collection_id=collection_id,
            user_id=user["id"],
        )

        if not deleted:
            return jsonify({"error": "Collection not found"}), 404

        return jsonify({"message": "Collection deleted successfully"}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "Failed to delete collection"}), 500


# ==========================================
# Collection Items (Drawings)
# ==========================================


@collections_v1_bp.route("/<int:collection_id>/drawings", methods=["POST"])
@auth_required
@validate_json(AddDrawingToCollectionRequest)
def add_drawing_to_collection(
    collection_id: int, validated_data: AddDrawingToCollectionRequest
):
    """Add a drawing to a collection."""
    user = get_current_user()

    try:
        item = CollectionService.add_drawing_to_collection(
            collection_id=collection_id,
            drawing_id=validated_data.drawing_id,
            user_id=user["id"],
            order_index=validated_data.order_index or 0,
        )

        return jsonify({"item": item}), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to add drawing to collection"}), 500


@collections_v1_bp.route("/<int:collection_id>/drawings", methods=["GET"])
@auth_required
def get_collection_drawings(collection_id: int):
    """Get drawings in a collection (RBAC filtered)."""
    user = get_current_user()

    # Get pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Validate pagination
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    try:
        result = CollectionService.get_collection_drawings(
            collection_id=collection_id,
            user_id=user["id"],
            page=page,
            per_page=per_page,
        )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "Failed to get collection drawings"}), 500


@collections_v1_bp.route(
    "/<int:collection_id>/drawings/<int:drawing_id>", methods=["DELETE"]
)
@auth_required
def remove_drawing_from_collection(collection_id: int, drawing_id: int):
    """Remove a drawing from a collection."""
    user = get_current_user()

    try:
        removed = CollectionService.remove_drawing_from_collection(
            collection_id=collection_id,
            drawing_id=drawing_id,
            user_id=user["id"],
        )

        if not removed:
            return jsonify({"error": "Drawing not found in collection"}), 404

        return jsonify({"message": "Drawing removed from collection"}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "Failed to remove drawing from collection"}), 500


@collections_v1_bp.route("/<int:collection_id>/drawings/reorder", methods=["PUT"])
@auth_required
@validate_json(ReorderCollectionDrawingsRequest)
def reorder_collection_drawings(
    collection_id: int, validated_data: ReorderCollectionDrawingsRequest
):
    """Reorder drawings in a collection."""
    user = get_current_user()

    try:
        success = CollectionService.reorder_collection_drawings(
            collection_id=collection_id,
            user_id=user["id"],
            drawing_orders=validated_data.drawing_orders,
        )

        if success:
            return jsonify({"message": "Drawings reordered successfully"}), 200
        else:
            return jsonify({"error": "Failed to reorder drawings"}), 400

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "Failed to reorder drawings"}), 500


# ==========================================
# Collection Sharing
# ==========================================


@collections_v1_bp.route("/<int:collection_id>/share", methods=["POST"])
@auth_required
def share_collection(collection_id: int):
    """Create a share for a collection (user or group)."""
    user = get_current_user()
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Extract share parameters
    permission = data.get("permission", "viewer")
    shared_with_id = data.get("shared_with_id")
    shared_with_group_id = data.get("shared_with_group_id")

    try:
        share = CollectionService.share_collection(
            collection_id=collection_id,
            user_id=user["id"],
            permission=permission,
            shared_with_id=shared_with_id,
            shared_with_group_id=shared_with_group_id,
        )

        return jsonify({"share": share}), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to share collection"}), 500


@collections_v1_bp.route("/<int:collection_id>/shares", methods=["GET"])
@auth_required
def list_collection_shares(collection_id: int):
    """List all shares for a collection."""
    user = get_current_user()

    try:
        shares = CollectionService.list_collection_shares(
            collection_id=collection_id,
            user_id=user["id"],
        )

        return jsonify({"shares": shares}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "Failed to list shares"}), 500


@collections_v1_bp.route(
    "/<int:collection_id>/shares/<int:share_id>", methods=["DELETE"]
)
@auth_required
def revoke_collection_share(collection_id: int, share_id: int):
    """Revoke a collection share."""
    user = get_current_user()

    try:
        revoked = CollectionService.revoke_collection_share(
            collection_id=collection_id,
            share_id=share_id,
            user_id=user["id"],
        )

        if not revoked:
            return jsonify({"error": "Share not found"}), 404

        return jsonify({"message": "Share revoked successfully"}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": "Failed to revoke share"}), 500


@collections_v1_bp.route("/<int:collection_id>/share/token", methods=["POST"])
@auth_required
def generate_share_token(collection_id: int):
    """Generate or regenerate a public share token."""
    user = get_current_user()

    try:
        token = CollectionService.generate_share_token(
            collection_id=collection_id,
            user_id=user["id"],
        )

        return jsonify({"token": token}), 200

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Failed to generate share token"}), 500


# ==========================================
# Public Access
# ==========================================


@collections_v1_bp.route("/shared/<token>", methods=["GET"])
@optional_auth
def get_shared_collection(token: str):
    """Access a shared collection via public token (may be unauthenticated)."""
    # Get user if authenticated
    user = None
    try:
        user = get_current_user()
    except:
        pass

    user_id = user["id"] if user else None

    try:
        collection = CollectionService.get_collection_by_token(
            token=token,
            user_id=user_id,
            log_access=True,
        )

        if not collection:
            return jsonify({"error": "Collection not found or access denied"}), 404

        return jsonify({"collection": collection}), 200

    except Exception as e:
        return jsonify({"error": "Failed to access shared collection"}), 500


@collections_v1_bp.route("/shared/<token>/drawings", methods=["GET"])
@optional_auth
def get_shared_collection_drawings(token: str):
    """Get drawings from a shared collection via public token."""
    # Get user if authenticated
    user = None
    try:
        user = get_current_user()
    except:
        pass

    user_id = user["id"] if user else None

    # Get pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    # Validate pagination
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    try:
        # First verify access to the collection
        collection = CollectionService.get_collection_by_token(
            token=token,
            user_id=user_id,
            log_access=False,  # Don't log for drawings endpoint
        )

        if not collection:
            return jsonify({"error": "Collection not found or access denied"}), 404

        # Get drawings with RBAC filtering
        # For unauthenticated users, they can only see public drawings
        # For authenticated users, apply normal RBAC
        if user_id:
            result = CollectionService.get_collection_drawings(
                collection_id=collection["id"],
                user_id=user_id,
                page=page,
                per_page=per_page,
            )
        else:
            # For unauthenticated users, return empty (or implement public drawing logic)
            result = {
                "drawings": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": "Failed to get collection drawings"}), 500


# ==========================================
# Analytics
# ==========================================


@collections_v1_bp.route("/<int:collection_id>/analytics", methods=["GET"])
@auth_required
def get_collection_analytics(collection_id: int):
    """Get analytics/stats for a collection (owner/admin only)."""
    user = get_current_user()

    try:
        # Verify user is owner or admin
        from app.models import get_db
        from app.services.permission_service import PermissionService

        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return jsonify({"error": "Collection not found"}), 404

        # Only owner or global admin can view analytics
        if collection.owner_id != user["id"] and not PermissionService.is_global_admin(
            user["id"]
        ):
            return (
                jsonify(
                    {"error": "Only the collection owner or admin can view analytics"}
                ),
                403,
            )

        stats = CollectionService.get_collection_stats(collection_id=collection_id)

        return jsonify({"stats": stats}), 200

    except Exception as e:
        return jsonify({"error": "Failed to get collection analytics"}), 500
