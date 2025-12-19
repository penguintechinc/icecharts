"""Collection service for managing drawing collections in IceCharts."""

import secrets
from typing import Dict, List, Optional

from app.models import get_db
from app.services.permission_service import Permission, PermissionService


class CollectionService:
    """Service for managing drawing collections (albums/folders)."""

    @staticmethod
    def create_collection(
        owner_id: int,
        name: str,
        description: str = "",
        share_mode: str = "private",
        is_public: bool = False,
    ) -> dict:
        """
        Create a new collection.

        Args:
            owner_id: ID of the user creating the collection
            name: Collection name
            description: Optional description
            share_mode: Share mode (private, link_only, registered_users)
            is_public: Whether collection is public

        Returns:
            Dictionary containing collection data

        Raises:
            ValueError: If creation fails or validation fails
        """
        if not name or not name.strip():
            raise ValueError("Collection name is required")

        if share_mode not in ["private", "link_only", "registered_users"]:
            raise ValueError(
                "share_mode must be 'private', 'link_only', or 'registered_users'"
            )

        db = get_db()

        # Verify user exists
        user = db(db.identities.id == owner_id).select().first()
        if not user:
            raise ValueError("User not found")

        # Create collection
        collection_id = db.collections.insert(
            name=name.strip(),
            description=description.strip() if description else "",
            owner_id=owner_id,
            share_mode=share_mode,
            is_public=is_public,
        )

        db.commit()

        collection = db(db.collections.id == collection_id).select().first()
        return collection.as_dict() if collection else None

    @staticmethod
    def get_collection_by_id(collection_id: int, user_id: int) -> Optional[dict]:
        """
        Get collection by ID with RBAC check.

        Args:
            collection_id: ID of the collection
            user_id: ID of the requesting user

        Returns:
            Collection dictionary or None if not found/no access
        """
        if not CollectionService.can_view_collection(collection_id, user_id):
            return None

        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return None

        collection_dict = collection.as_dict()

        # Add drawing count
        drawing_count = db(db.collection_items.collection_id == collection_id).count()
        collection_dict["drawing_count"] = drawing_count

        return collection_dict

    @staticmethod
    def update_collection(collection_id: int, user_id: int, **kwargs) -> Optional[dict]:
        """
        Update a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user making the update
            **kwargs: Fields to update (name, description, share_mode, is_public, thumbnail_url)

        Returns:
            Updated collection dictionary or None if not found/no access

        Raises:
            PermissionError: If user doesn't have edit permission
            ValueError: If validation fails
        """
        if not CollectionService.can_edit_collection(collection_id, user_id):
            raise PermissionError("You don't have permission to edit this collection")

        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return None

        # Filter allowed fields
        allowed_fields = {
            "name",
            "description",
            "share_mode",
            "is_public",
            "thumbnail_url",
        }
        update_data = {
            k: v for k, v in kwargs.items() if k in allowed_fields and v is not None
        }

        # Validate share_mode if provided
        if "share_mode" in update_data:
            if update_data["share_mode"] not in [
                "private",
                "link_only",
                "registered_users",
            ]:
                raise ValueError(
                    "share_mode must be 'private', 'link_only', or 'registered_users'"
                )

        # Validate and clean name if provided
        if "name" in update_data:
            name = update_data["name"].strip()
            if not name:
                raise ValueError("Collection name cannot be empty")
            update_data["name"] = name

        # Clean description if provided
        if "description" in update_data:
            update_data["description"] = update_data["description"].strip()

        if update_data:
            db(db.collections.id == collection_id).update(**update_data)
            db.commit()

        # Return updated collection
        updated = db(db.collections.id == collection_id).select().first()
        return updated.as_dict() if updated else None

    @staticmethod
    def delete_collection(collection_id: int, user_id: int) -> bool:
        """
        Delete a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user attempting deletion

        Returns:
            True if deleted successfully

        Raises:
            PermissionError: If user is not the owner or admin
        """
        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return False

        # Only owner or global admin can delete
        if collection.owner_id != user_id and not PermissionService.is_global_admin(
            user_id
        ):
            raise PermissionError("Only the collection owner or admin can delete it")

        # Delete collection (cascade will handle items and shares)
        db(db.collections.id == collection_id).delete()
        db.commit()

        return True

    @staticmethod
    def list_user_collections(user_id: int, page: int = 1, per_page: int = 20) -> dict:
        """
        List collections accessible by a user.

        Args:
            user_id: ID of the user
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Dictionary with collections list and pagination info
        """
        db = get_db()

        # Get collections owned by user
        owned_query = db.collections.owner_id == user_id

        # Get collections shared with user
        user_shares = db(db.collection_shares.shared_with_id == user_id).select(
            db.collection_shares.collection_id
        )
        user_share_ids = [s.collection_id for s in user_shares]

        # Get collections shared with user's groups
        user_groups = db(db.group_memberships.identity_id == user_id).select(
            db.group_memberships.group_id
        )
        group_ids = [g.group_id for g in user_groups]

        group_share_ids = []
        if group_ids:
            group_shares = db(
                db.collection_shares.shared_with_group_id.belongs(group_ids)
            ).select(db.collection_shares.collection_id)
            group_share_ids = [s.collection_id for s in group_shares]

        # Combine all accessible collection IDs
        accessible_ids = set(user_share_ids + group_share_ids)

        # Build query for all accessible collections
        if accessible_ids:
            query = (db.collections.id.belongs(accessible_ids)) | owned_query
        else:
            query = owned_query

        # Get total count
        total = db(query).count()

        # Get paginated results
        offset = (page - 1) * per_page
        collections = db(query).select(
            orderby=~db.collections.updated_at, limitby=(offset, offset + per_page)
        )

        # Add drawing count to each collection
        result_collections = []
        for collection in collections:
            coll_dict = collection.as_dict()
            drawing_count = db(
                db.collection_items.collection_id == collection.id
            ).count()
            coll_dict["drawing_count"] = drawing_count
            result_collections.append(coll_dict)

        return {
            "collections": result_collections,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }

    @staticmethod
    def add_drawing_to_collection(
        collection_id: int, drawing_id: int, user_id: int, order_index: int = 0
    ) -> dict:
        """
        Add a drawing to a collection.

        Args:
            collection_id: ID of the collection
            drawing_id: ID of the drawing to add
            user_id: ID of the user adding the drawing
            order_index: Position in the collection

        Returns:
            Dictionary with collection item data

        Raises:
            PermissionError: If user can't edit collection or view drawing
            ValueError: If drawing or collection not found, or item already exists
        """
        # Check collection edit permission
        if not CollectionService.can_edit_collection(collection_id, user_id):
            raise PermissionError("You don't have permission to edit this collection")

        # Check drawing view permission
        if not PermissionService.can_view_drawing(user_id, drawing_id):
            raise PermissionError("You don't have permission to view this drawing")

        db = get_db()

        # Verify collection exists
        collection = db(db.collections.id == collection_id).select().first()
        if not collection:
            raise ValueError("Collection not found")

        # Verify drawing exists
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            raise ValueError("Drawing not found")

        # Check if already in collection
        existing = (
            db(
                (db.collection_items.collection_id == collection_id)
                & (db.collection_items.drawing_id == drawing_id)
            )
            .select()
            .first()
        )

        if existing:
            raise ValueError("Drawing is already in this collection")

        # Add to collection
        item_id = db.collection_items.insert(
            collection_id=collection_id,
            drawing_id=drawing_id,
            added_by_id=user_id,
            order_index=order_index,
        )

        db.commit()

        item = db(db.collection_items.id == item_id).select().first()
        return item.as_dict() if item else None

    @staticmethod
    def remove_drawing_from_collection(
        collection_id: int, drawing_id: int, user_id: int
    ) -> bool:
        """
        Remove a drawing from a collection.

        Args:
            collection_id: ID of the collection
            drawing_id: ID of the drawing to remove
            user_id: ID of the user removing the drawing

        Returns:
            True if removed successfully

        Raises:
            PermissionError: If user doesn't have edit permission
        """
        if not CollectionService.can_edit_collection(collection_id, user_id):
            raise PermissionError("You don't have permission to edit this collection")

        db = get_db()

        # Delete the item
        deleted = db(
            (db.collection_items.collection_id == collection_id)
            & (db.collection_items.drawing_id == drawing_id)
        ).delete()

        db.commit()

        return deleted > 0

    @staticmethod
    def reorder_collection_drawings(
        collection_id: int, user_id: int, drawing_orders: List[Dict[str, int]]
    ) -> bool:
        """
        Reorder drawings in a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user reordering
            drawing_orders: List of {drawing_id, order_index} dicts

        Returns:
            True if reordered successfully

        Raises:
            PermissionError: If user doesn't have edit permission
        """
        if not CollectionService.can_edit_collection(collection_id, user_id):
            raise PermissionError("You don't have permission to edit this collection")

        db = get_db()

        # Update order for each drawing
        for item in drawing_orders:
            db(
                (db.collection_items.collection_id == collection_id)
                & (db.collection_items.drawing_id == item["drawing_id"])
            ).update(order_index=item["order_index"])

        db.commit()
        return True

    @staticmethod
    def get_collection_drawings(
        collection_id: int, user_id: int, page: int = 1, per_page: int = 20
    ) -> dict:
        """
        Get drawings in a collection with RBAC filtering.

        CRITICAL: Applies PermissionService.can_view_drawing() for each drawing.

        Args:
            collection_id: ID of the collection
            user_id: ID of the requesting user
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Dictionary with filtered drawings list and pagination info
        """
        if not CollectionService.can_view_collection(collection_id, user_id):
            return {
                "drawings": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
            }

        db = get_db()

        # Get all items in collection (ordered)
        items = db(db.collection_items.collection_id == collection_id).select(
            orderby=db.collection_items.order_index
        )

        # Filter by drawing view permission
        accessible_drawings = []
        for item in items:
            if PermissionService.can_view_drawing(user_id, item.drawing_id):
                # Get drawing details
                drawing = db(db.drawings.id == item.drawing_id).select().first()
                if drawing:
                    drawing_dict = drawing.as_dict()
                    drawing_dict["order_index"] = item.order_index
                    drawing_dict["added_at"] = item.added_at
                    accessible_drawings.append(drawing_dict)

        # Apply pagination to filtered results
        total = len(accessible_drawings)
        offset = (page - 1) * per_page
        paginated_drawings = accessible_drawings[offset : offset + per_page]

        return {
            "drawings": paginated_drawings,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
        }

    @staticmethod
    def generate_share_token(collection_id: int, user_id: int) -> str:
        """
        Generate or regenerate a share token for a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user requesting the token

        Returns:
            Share token string

        Raises:
            PermissionError: If user doesn't have admin permission
            ValueError: If collection not found
        """
        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            raise ValueError("Collection not found")

        # Only owner or admin can generate share token
        if collection.owner_id != user_id and not PermissionService.is_global_admin(
            user_id
        ):
            raise PermissionError(
                "Only the collection owner or admin can generate share tokens"
            )

        # Generate new token
        token = secrets.token_urlsafe(32)

        # Update collection with new token
        db(db.collections.id == collection_id).update(share_token=token)
        db.commit()

        return token

    @staticmethod
    def share_collection(
        collection_id: int,
        user_id: int,
        permission: str = "viewer",
        shared_with_id: Optional[int] = None,
        shared_with_group_id: Optional[int] = None,
    ) -> dict:
        """
        Share a collection with a user or group.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user creating the share
            permission: Permission level (viewer, editor, admin)
            shared_with_id: ID of user to share with
            shared_with_group_id: ID of group to share with

        Returns:
            Dictionary with share data

        Raises:
            PermissionError: If user doesn't have share permission
            ValueError: If validation fails
        """
        # Validate share type
        if not shared_with_id and not shared_with_group_id:
            raise ValueError(
                "Must specify either shared_with_id or shared_with_group_id"
            )

        if shared_with_id and shared_with_group_id:
            raise ValueError("Cannot share with both user and group simultaneously")

        # Validate permission level
        if permission not in ["viewer", "editor", "admin"]:
            raise ValueError("Permission must be 'viewer', 'editor', or 'admin'")

        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            raise ValueError("Collection not found")

        # Check if user can share the collection (owner or admin)
        if collection.owner_id != user_id and not PermissionService.is_global_admin(
            user_id
        ):
            raise PermissionError("Only the collection owner or admin can share it")

        # Validate target user/group exists
        if shared_with_id:
            target_user = db(db.identities.id == shared_with_id).select().first()
            if not target_user:
                raise ValueError("Target user not found")

            # Check if already shared with this user
            existing = (
                db(
                    (db.collection_shares.collection_id == collection_id)
                    & (db.collection_shares.shared_with_id == shared_with_id)
                )
                .select()
                .first()
            )

            if existing:
                # Update existing share
                db(db.collection_shares.id == existing.id).update(permission=permission)
                db.commit()
                updated = db(db.collection_shares.id == existing.id).select().first()
                return updated.as_dict()

        if shared_with_group_id:
            target_group = db(db.groups.id == shared_with_group_id).select().first()
            if not target_group:
                raise ValueError("Target group not found")

            # Check if already shared with this group
            existing = (
                db(
                    (db.collection_shares.collection_id == collection_id)
                    & (
                        db.collection_shares.shared_with_group_id
                        == shared_with_group_id
                    )
                )
                .select()
                .first()
            )

            if existing:
                # Update existing share
                db(db.collection_shares.id == existing.id).update(permission=permission)
                db.commit()
                updated = db(db.collection_shares.id == existing.id).select().first()
                return updated.as_dict()

        # Create new share
        share_id = db.collection_shares.insert(
            collection_id=collection_id,
            shared_with_id=shared_with_id,
            shared_with_group_id=shared_with_group_id,
            permission=permission,
            created_by_id=user_id,
        )

        db.commit()

        share = db(db.collection_shares.id == share_id).select().first()
        return share.as_dict() if share else None

    @staticmethod
    def revoke_collection_share(
        collection_id: int, share_id: int, user_id: int
    ) -> bool:
        """
        Revoke a collection share.

        Args:
            collection_id: ID of the collection
            share_id: ID of the share to revoke
            user_id: ID of the user revoking the share

        Returns:
            True if revoked successfully

        Raises:
            PermissionError: If user doesn't have permission to revoke
        """
        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return False

        # Only owner or admin can revoke shares
        if collection.owner_id != user_id and not PermissionService.is_global_admin(
            user_id
        ):
            raise PermissionError(
                "Only the collection owner or admin can revoke shares"
            )

        # Delete the share
        deleted = db(
            (db.collection_shares.id == share_id)
            & (db.collection_shares.collection_id == collection_id)
        ).delete()

        db.commit()

        return deleted > 0

    @staticmethod
    def list_collection_shares(collection_id: int, user_id: int) -> dict:
        """
        List all shares for a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the requesting user

        Returns:
            Dictionary with user_shares and group_shares lists

        Raises:
            PermissionError: If user doesn't have permission to view shares
        """
        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return {"user_shares": [], "group_shares": []}

        # Only owner or admin can view shares
        if collection.owner_id != user_id and not PermissionService.is_global_admin(
            user_id
        ):
            raise PermissionError("Only the collection owner or admin can view shares")

        # Get user shares with user details
        user_shares_rows = db(
            (db.collection_shares.collection_id == collection_id)
            & (db.collection_shares.shared_with_id == db.identities.id)
        ).select(
            db.collection_shares.ALL,
            db.identities.id,
            db.identities.email,
            db.identities.full_name,
        )

        user_shares = []
        for row in user_shares_rows:
            user_shares.append(
                {
                    "id": row.collection_shares.id,
                    "user_id": row.identities.id,
                    "email": row.identities.email,
                    "full_name": row.identities.full_name,
                    "permission": row.collection_shares.permission,
                    "created_at": (
                        row.collection_shares.created_at.isoformat()
                        if row.collection_shares.created_at
                        else None
                    ),
                }
            )

        # Get group shares with group details
        group_shares_rows = db(
            (db.collection_shares.collection_id == collection_id)
            & (db.collection_shares.shared_with_group_id == db.groups.id)
        ).select(
            db.collection_shares.ALL,
            db.groups.id,
            db.groups.name,
        )

        group_shares = []
        for row in group_shares_rows:
            group_shares.append(
                {
                    "id": row.collection_shares.id,
                    "group_id": row.groups.id,
                    "group_name": row.groups.name,
                    "permission": row.collection_shares.permission,
                    "created_at": (
                        row.collection_shares.created_at.isoformat()
                        if row.collection_shares.created_at
                        else None
                    ),
                }
            )

        return {
            "user_shares": user_shares,
            "group_shares": group_shares,
        }

    @staticmethod
    def get_collection_by_token(
        token: str, user_id: Optional[int] = None, log_access: bool = True
    ) -> Optional[dict]:
        """
        Get collection by share token.

        Args:
            token: Share token
            user_id: Optional ID of the accessing user
            log_access: Whether to log access to analytics

        Returns:
            Collection dictionary or None if not found/no access
        """
        db = get_db()
        collection = db(db.collections.share_token == token).select().first()

        if not collection:
            return None

        # Check share mode
        if collection.share_mode == "private":
            # Private collections can't be accessed via token
            return None
        elif collection.share_mode == "registered_users" and not user_id:
            # Requires authentication
            return None

        # Log access to analytics
        if log_access:
            from flask import request as flask_request

            access_ip = None
            user_agent = None

            try:
                access_ip = flask_request.remote_addr if flask_request else None
                user_agent = (
                    flask_request.headers.get("User-Agent") if flask_request else None
                )
            except:
                pass

            db.share_analytics.insert(
                share_type="collection",
                share_id=collection.id,
                share_token=token,
                accessed_by_id=user_id,
                access_ip=access_ip,
                user_agent=user_agent,
            )
            db.commit()

        collection_dict = collection.as_dict()

        # Add drawing count
        drawing_count = db(db.collection_items.collection_id == collection.id).count()
        collection_dict["drawing_count"] = drawing_count

        return collection_dict

    @staticmethod
    def can_view_collection(collection_id: int, user_id: int) -> bool:
        """
        Check if user can view a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user

        Returns:
            True if user has view permission
        """
        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return False

        # Owner can always view
        if collection.owner_id == user_id:
            return True

        # Global admin can view any collection
        if PermissionService.is_global_admin(user_id):
            return True

        # Public collections can be viewed by anyone
        if collection.is_public:
            return True

        # Check if collection is shared with user
        user_share = (
            db(
                (db.collection_shares.collection_id == collection_id)
                & (db.collection_shares.shared_with_id == user_id)
            )
            .select()
            .first()
        )

        if user_share:
            return True

        # Check if collection is shared with any of user's groups
        user_groups = db(db.group_memberships.identity_id == user_id).select(
            db.group_memberships.group_id
        )
        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_share = (
                db(
                    (db.collection_shares.collection_id == collection_id)
                    & (db.collection_shares.shared_with_group_id.belongs(group_ids))
                )
                .select()
                .first()
            )

            if group_share:
                return True

        return False

    @staticmethod
    def can_edit_collection(collection_id: int, user_id: int) -> bool:
        """
        Check if user can edit a collection.

        Args:
            collection_id: ID of the collection
            user_id: ID of the user

        Returns:
            True if user has edit permission
        """
        db = get_db()
        collection = db(db.collections.id == collection_id).select().first()

        if not collection:
            return False

        # Owner can always edit
        if collection.owner_id == user_id:
            return True

        # Global admin can edit any collection
        if PermissionService.is_global_admin(user_id):
            return True

        # Check if user has editor or admin permission via direct share
        user_share = (
            db(
                (db.collection_shares.collection_id == collection_id)
                & (db.collection_shares.shared_with_id == user_id)
                & (db.collection_shares.permission.belongs(["editor", "admin"]))
            )
            .select()
            .first()
        )

        if user_share:
            return True

        # Check if user has editor or admin permission via group share
        user_groups = db(db.group_memberships.identity_id == user_id).select(
            db.group_memberships.group_id
        )
        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_share = (
                db(
                    (db.collection_shares.collection_id == collection_id)
                    & (db.collection_shares.shared_with_group_id.belongs(group_ids))
                    & (db.collection_shares.permission.belongs(["editor", "admin"]))
                )
                .select()
                .first()
            )

            if group_share:
                return True

        return False

    @staticmethod
    def get_collection_stats(collection_id: int) -> dict:
        """
        Get statistics for a collection.

        Args:
            collection_id: ID of the collection

        Returns:
            Dictionary with stats (drawing_count, view_count, last_accessed)
        """
        db = get_db()

        # Get drawing count
        drawing_count = db(db.collection_items.collection_id == collection_id).count()

        # Get view count from analytics
        view_count = db(
            (db.share_analytics.share_type == "collection")
            & (db.share_analytics.share_id == collection_id)
        ).count()

        # Get last accessed time
        last_access = (
            db(
                (db.share_analytics.share_type == "collection")
                & (db.share_analytics.share_id == collection_id)
            )
            .select(
                db.share_analytics.accessed_at,
                orderby=~db.share_analytics.accessed_at,
                limitby=(0, 1),
            )
            .first()
        )

        last_accessed = last_access.accessed_at if last_access else None

        return {
            "drawing_count": drawing_count,
            "view_count": view_count,
            "last_accessed": last_accessed.isoformat() if last_accessed else None,
        }
