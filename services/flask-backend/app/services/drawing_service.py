"""Drawing management service for IceCharts."""

import datetime
from dataclasses import dataclass
from typing import Optional

from app.models import get_db
from app.services.permission_service import PermissionService


@dataclass(slots=True)
class DrawingData:
    """Data class for drawing information."""

    id: int
    tenant_id: int
    title: str
    description: Optional[str]
    created_by_id: int
    updated_by_id: Optional[int]
    is_public: bool
    is_template: bool
    status: str
    tags: list[str]
    thumbnail_url: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime


class DrawingService:
    """Service for managing drawings."""

    @staticmethod
    def create_drawing(
        owner_id: int,
        title: str,
        description: Optional[str] = None,
        is_public: bool = False,
        is_template: bool = False,
        tags: Optional[list[str]] = None,
        tenant_id: int = 1
    ) -> dict:
        """
        Create a new drawing.

        Args:
            owner_id: ID of the user creating the drawing
            title: Title of the drawing
            description: Optional description
            is_public: Whether the drawing is public
            is_template: Whether this is a template
            tags: Optional list of tags
            tenant_id: Tenant ID (defaults to 1)

        Returns:
            Dictionary containing drawing data

        Raises:
            ValueError: If title is empty or drawing creation fails
        """
        if not title or not title.strip():
            raise ValueError("Drawing title cannot be empty")

        db = get_db()

        try:
            drawing_id = db.drawings.insert(
                tenant_id=tenant_id,
                title=title.strip(),
                description=description.strip() if description else None,
                created_by_id=owner_id,
                updated_by_id=owner_id,
                is_public=is_public,
                is_template=is_template,
                status="draft",
                tags=tags or [],
            )
            db.commit()

            return DrawingService.get_drawing(drawing_id, owner_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create drawing: {str(e)}")

    @staticmethod
    def get_drawing(drawing_id: int, user_id: int) -> Optional[dict]:
        """
        Get drawing by ID with permission check.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user requesting the drawing

        Returns:
            Dictionary containing drawing data or None if not found/no access

        Raises:
            PermissionError: If user doesn't have permission to view
        """
        db = get_db()
        drawing = db(db.drawings.id == drawing_id).select().first()

        if not drawing:
            return None

        # Check view permission
        if not PermissionService.can_view_drawing(user_id, drawing_id):
            raise PermissionError("You don't have permission to view this drawing")

        return drawing.as_dict()

    @staticmethod
    def get_drawing_by_id(drawing_id: int) -> Optional[dict]:
        """
        Get drawing by ID without permission check (internal use).

        Args:
            drawing_id: ID of the drawing

        Returns:
            Dictionary containing drawing data or None if not found
        """
        db = get_db()
        drawing = db(db.drawings.id == drawing_id).select().first()
        return drawing.as_dict() if drawing else None

    @staticmethod
    def update_drawing(
        drawing_id: int,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_template: Optional[bool] = None,
        status: Optional[str] = None,
        tags: Optional[list[str]] = None,
        thumbnail_url: Optional[str] = None
    ) -> Optional[dict]:
        """
        Update drawing information.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user updating the drawing
            title: New title (optional)
            description: New description (optional)
            is_public: New public status (optional)
            is_template: New template status (optional)
            status: New status (optional)
            tags: New tags (optional)
            thumbnail_url: New thumbnail URL (optional)

        Returns:
            Updated drawing dictionary or None if not found

        Raises:
            PermissionError: If user doesn't have edit permission
            ValueError: If update fails or validation fails
        """
        # Check if drawing exists and user has permission
        if not DrawingService.get_drawing_by_id(drawing_id):
            return None

        if not PermissionService.can_edit_drawing(user_id, drawing_id):
            raise PermissionError("You don't have permission to edit this drawing")

        db = get_db()

        update_data = {}
        if title is not None:
            if not title.strip():
                raise ValueError("Drawing title cannot be empty")
            update_data["title"] = title.strip()

        if description is not None:
            update_data["description"] = description.strip() if description else None

        if is_public is not None:
            update_data["is_public"] = is_public

        if is_template is not None:
            update_data["is_template"] = is_template

        if status is not None:
            if status not in ["draft", "published", "archived"]:
                raise ValueError("Invalid status")
            update_data["status"] = status

        if tags is not None:
            update_data["tags"] = tags

        if thumbnail_url is not None:
            update_data["thumbnail_url"] = thumbnail_url

        if update_data:
            update_data["updated_by_id"] = user_id

        if not update_data:
            return DrawingService.get_drawing_by_id(drawing_id)

        try:
            db(db.drawings.id == drawing_id).update(**update_data)
            db.commit()
            return DrawingService.get_drawing_by_id(drawing_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update drawing: {str(e)}")

    @staticmethod
    def delete_drawing(drawing_id: int, user_id: int) -> bool:
        """
        Delete a drawing and all its related data.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user deleting the drawing

        Returns:
            True if deleted, False if drawing not found

        Raises:
            PermissionError: If user doesn't have delete permission
            ValueError: If deletion fails
        """
        # Check if drawing exists and user has permission
        if not DrawingService.get_drawing_by_id(drawing_id):
            return False

        if not PermissionService.can_delete_drawing(user_id, drawing_id):
            raise PermissionError("You don't have permission to delete this drawing")

        db = get_db()

        try:
            # Delete related data (cascade should handle most of this)
            db(db.shapes.drawing_id == drawing_id).delete()
            db(db.connectors.drawing_id == drawing_id).delete()
            db(db.shape_metadata.drawing_id == drawing_id).delete()
            db(db.comments.drawing_id == drawing_id).delete()
            db(db.drawing_versions.drawing_id == drawing_id).delete()
            db(db.drawing_shares.drawing_id == drawing_id).delete()
            db(db.collaboration_sessions.drawing_id == drawing_id).delete()

            # Delete drawing
            deleted = db(db.drawings.id == drawing_id).delete()
            db.commit()

            return deleted > 0

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to delete drawing: {str(e)}")

    @staticmethod
    def list_drawings(
        user_id: int,
        search: Optional[str] = None,
        status: Optional[str] = None,
        is_template: Optional[bool] = None,
        tags: Optional[list[str]] = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[list[dict], int]:
        """
        List drawings accessible to the user.

        Args:
            user_id: ID of the user
            search: Optional search query for title/description
            status: Optional status filter
            is_template: Optional template filter
            tags: Optional tag filters
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Tuple of (list of drawing dictionaries, total count)
        """
        db = get_db()
        offset = (page - 1) * per_page

        # Build query
        # Get drawings where user is owner, or drawings shared with user/groups
        query = (
            (db.drawings.created_by_id == user_id) |
            (db.drawings.is_public == True) |
            (db.drawings.id.belongs(
                db(db.drawing_shares.shared_with_id == user_id)._select(
                    db.drawing_shares.drawing_id
                )
            ))
        )

        # Add group shares
        user_groups = db(
            db.group_memberships.identity_id == user_id
        ).select(db.group_memberships.group_id)
        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            query = query | (db.drawings.id.belongs(
                db(db.drawing_shares.shared_with_group_id.belongs(group_ids))._select(
                    db.drawing_shares.drawing_id
                )
            ))

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query & (
                (db.drawings.title.like(search_term)) |
                (db.drawings.description.like(search_term))
            )

        if status:
            query = query & (db.drawings.status == status)

        if is_template is not None:
            query = query & (db.drawings.is_template == is_template)

        if tags:
            # Filter by tags - drawing must have all specified tags
            for tag in tags:
                query = query & (db.drawings.tags.contains(tag))

        # Get results
        drawings = db(query).select(
            orderby=~db.drawings.updated_at,
            limitby=(offset, offset + per_page),
        )

        total = db(query).count()

        return [d.as_dict() for d in drawings], total

    @staticmethod
    def duplicate_drawing(
        drawing_id: int,
        user_id: int,
        new_title: Optional[str] = None
    ) -> dict:
        """
        Duplicate a drawing (copy with new owner).

        Args:
            drawing_id: ID of the drawing to duplicate
            user_id: ID of the user creating the duplicate
            new_title: Optional new title (defaults to "Copy of {original_title}")

        Returns:
            Dictionary containing new drawing data

        Raises:
            PermissionError: If user doesn't have view permission
            ValueError: If duplication fails
        """
        # Check if user can view the original drawing
        if not PermissionService.can_view_drawing(user_id, drawing_id):
            raise PermissionError(
                "You don't have permission to duplicate this drawing"
            )

        db = get_db()
        original = db(db.drawings.id == drawing_id).select().first()

        if not original:
            raise ValueError("Drawing not found")

        # Determine new title
        if not new_title:
            new_title = f"Copy of {original.title}"

        try:
            # Create new drawing
            new_drawing_id = db.drawings.insert(
                tenant_id=original.tenant_id,
                title=new_title,
                description=original.description,
                created_by_id=user_id,
                updated_by_id=user_id,
                is_public=False,  # Duplicates are private by default
                is_template=original.is_template,
                status="draft",
                tags=original.tags or [],
            )

            # Copy shapes
            shapes = db(db.shapes.drawing_id == drawing_id).select()
            for shape in shapes:
                db.shapes.insert(
                    drawing_id=new_drawing_id,
                    shape_id=shape.shape_id,
                    shape_type=shape.shape_type,
                    x=shape.x,
                    y=shape.y,
                    width=shape.width,
                    height=shape.height,
                    rotation=shape.rotation,
                    fill_color=shape.fill_color,
                    stroke_color=shape.stroke_color,
                    stroke_width=shape.stroke_width,
                    text_content=shape.text_content,
                    properties_json=shape.properties_json,
                    z_index=shape.z_index,
                )

            # Copy connectors
            connectors = db(db.connectors.drawing_id == drawing_id).select()
            for connector in connectors:
                db.connectors.insert(
                    drawing_id=new_drawing_id,
                    connector_id=connector.connector_id,
                    source_shape_id=connector.source_shape_id,
                    target_shape_id=connector.target_shape_id,
                    connector_type=connector.connector_type,
                    stroke_color=connector.stroke_color,
                    stroke_width=connector.stroke_width,
                    properties_json=connector.properties_json,
                )

            db.commit()

            return DrawingService.get_drawing_by_id(new_drawing_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to duplicate drawing: {str(e)}")

    @staticmethod
    def get_drawing_stats(drawing_id: int) -> dict:
        """
        Get statistics for a drawing.

        Args:
            drawing_id: ID of the drawing

        Returns:
            Dictionary with stats (shape_count, connector_count, etc.)
        """
        db = get_db()

        shape_count = db(db.shapes.drawing_id == drawing_id).count()
        connector_count = db(db.connectors.drawing_id == drawing_id).count()
        comment_count = db(db.comments.drawing_id == drawing_id).count()
        version_count = db(db.drawing_versions.drawing_id == drawing_id).count()
        share_count = db(db.drawing_shares.drawing_id == drawing_id).count()

        return {
            "shape_count": shape_count,
            "connector_count": connector_count,
            "comment_count": comment_count,
            "version_count": version_count,
            "share_count": share_count,
        }
