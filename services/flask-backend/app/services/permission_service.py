"""Permission service for RBAC checks in IceCharts."""

from dataclasses import dataclass
from typing import Optional

from app.models import get_db


@dataclass(slots=True, frozen=True)
class Permission:
    """Permission level constants."""

    VIEW = "viewer"
    EDIT = "editor"
    ADMIN = "admin"


class PermissionService:
    """Service for checking user permissions on drawings and groups."""

    @staticmethod
    def is_global_admin(user_id: int) -> bool:
        """
        Check if user is a global admin.

        Args:
            user_id: ID of the user

        Returns:
            True if user has admin role
        """
        db = get_db()
        user = db(db.identities.id == user_id).select(
            db.identities.role
        ).first()

        if not user:
            return False

        return user.role == "admin"

    @staticmethod
    def get_user_role_in_group(user_id: int, group_id: int) -> Optional[str]:
        """
        Get user's role in a specific group.

        Args:
            user_id: ID of the user
            group_id: ID of the group

        Returns:
            Role string or None if not a member
        """
        db = get_db()
        membership = db(
            (db.group_memberships.identity_id == user_id) &
            (db.group_memberships.group_id == group_id)
        ).select().first()

        return membership.role if membership else None

    @staticmethod
    def can_manage_group(user_id: int, group_id: int) -> bool:
        """
        Check if user can manage a group (add/remove members, update settings).

        Args:
            user_id: ID of the user
            group_id: ID of the group

        Returns:
            True if user can manage the group
        """
        # Global admins can manage any group
        if PermissionService.is_global_admin(user_id):
            return True

        # Check if user is group admin
        db = get_db()
        membership = db(
            (db.group_memberships.identity_id == user_id) &
            (db.group_memberships.group_id == group_id)
        ).select().first()

        if not membership:
            return False

        # Only group admins can manage
        return membership.role == "admin"

    @staticmethod
    def can_view_drawing(user_id: int, drawing_id: int) -> bool:
        """
        Check if user can view a drawing.

        Args:
            user_id: ID of the user
            drawing_id: ID of the drawing

        Returns:
            True if user has view permission
        """
        db = get_db()

        # Get drawing
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            return False

        # Owner can always view
        if drawing.created_by_id == user_id:
            return True

        # Global admins can view any drawing
        if PermissionService.is_global_admin(user_id):
            return True

        # Public drawings can be viewed by anyone
        if drawing.is_public:
            return True

        # Check if drawing is shared with user
        share = db(
            (db.drawing_shares.drawing_id == drawing_id) &
            (db.drawing_shares.shared_with_id == user_id)
        ).select().first()

        if share:
            return True

        # Check if drawing is shared with any of user's groups
        user_groups = db(
            db.group_memberships.identity_id == user_id
        ).select(db.group_memberships.group_id)

        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_share = db(
                (db.drawing_shares.drawing_id == drawing_id) &
                (db.drawing_shares.shared_with_group_id.belongs(group_ids))
            ).select().first()

            if group_share:
                return True

        return False

    @staticmethod
    def can_edit_drawing(user_id: int, drawing_id: int) -> bool:
        """
        Check if user can edit a drawing.

        Args:
            user_id: ID of the user
            drawing_id: ID of the drawing

        Returns:
            True if user has edit permission
        """
        db = get_db()

        # Get drawing
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            return False

        # Owner can always edit
        if drawing.created_by_id == user_id:
            return True

        # Global admins can edit any drawing
        if PermissionService.is_global_admin(user_id):
            return True

        # Check if drawing is shared with user with edit permission
        share = db(
            (db.drawing_shares.drawing_id == drawing_id) &
            (db.drawing_shares.shared_with_id == user_id) &
            (db.drawing_shares.permission.belongs([Permission.EDIT, Permission.ADMIN]))
        ).select().first()

        if share:
            return True

        # Check if drawing is shared with any of user's groups with edit permission
        user_groups = db(
            db.group_memberships.identity_id == user_id
        ).select(db.group_memberships.group_id)

        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_share = db(
                (db.drawing_shares.drawing_id == drawing_id) &
                (db.drawing_shares.shared_with_group_id.belongs(group_ids)) &
                (db.drawing_shares.permission.belongs([Permission.EDIT, Permission.ADMIN]))
            ).select().first()

            if group_share:
                return True

        return False

    @staticmethod
    def can_delete_drawing(user_id: int, drawing_id: int) -> bool:
        """
        Check if user can delete a drawing.

        Args:
            user_id: ID of the user
            drawing_id: ID of the drawing

        Returns:
            True if user has delete permission
        """
        db = get_db()

        # Get drawing
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            return False

        # Only owner or global admin can delete
        if drawing.created_by_id == user_id:
            return True

        if PermissionService.is_global_admin(user_id):
            return True

        return False

    @staticmethod
    def can_share_drawing(user_id: int, drawing_id: int) -> bool:
        """
        Check if user can share a drawing with others.

        Args:
            user_id: ID of the user
            drawing_id: ID of the drawing

        Returns:
            True if user has share permission
        """
        db = get_db()

        # Get drawing
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            return False

        # Owner can always share
        if drawing.created_by_id == user_id:
            return True

        # Global admins can share any drawing
        if PermissionService.is_global_admin(user_id):
            return True

        # Check if user has admin permission on the drawing share
        share = db(
            (db.drawing_shares.drawing_id == drawing_id) &
            (db.drawing_shares.shared_with_id == user_id) &
            (db.drawing_shares.permission == Permission.ADMIN)
        ).select().first()

        if share:
            return True

        # Check if user's group has admin permission
        user_groups = db(
            db.group_memberships.identity_id == user_id
        ).select(db.group_memberships.group_id)

        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_share = db(
                (db.drawing_shares.drawing_id == drawing_id) &
                (db.drawing_shares.shared_with_group_id.belongs(group_ids)) &
                (db.drawing_shares.permission == Permission.ADMIN)
            ).select().first()

            if group_share:
                return True

        return False

    @staticmethod
    def get_drawing_permission_level(user_id: int, drawing_id: int) -> Optional[str]:
        """
        Get the highest permission level a user has for a drawing.

        Args:
            user_id: ID of the user
            drawing_id: ID of the drawing

        Returns:
            Permission level string (admin, editor, viewer) or None
        """
        db = get_db()

        # Get drawing
        drawing = db(db.drawings.id == drawing_id).select().first()
        if not drawing:
            return None

        # Owner has admin permission
        if drawing.created_by_id == user_id:
            return Permission.ADMIN

        # Global admin has admin permission
        if PermissionService.is_global_admin(user_id):
            return Permission.ADMIN

        # Check direct share
        share = db(
            (db.drawing_shares.drawing_id == drawing_id) &
            (db.drawing_shares.shared_with_id == user_id)
        ).select(db.drawing_shares.permission).first()

        highest_permission = share.permission if share else None

        # Check group shares
        user_groups = db(
            db.group_memberships.identity_id == user_id
        ).select(db.group_memberships.group_id)

        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_shares = db(
                (db.drawing_shares.drawing_id == drawing_id) &
                (db.drawing_shares.shared_with_group_id.belongs(group_ids))
            ).select(db.drawing_shares.permission)

            # Get highest permission from group shares
            for gs in group_shares:
                if highest_permission is None:
                    highest_permission = gs.permission
                elif gs.permission == Permission.ADMIN:
                    highest_permission = Permission.ADMIN
                elif gs.permission == Permission.EDIT and highest_permission == Permission.VIEW:
                    highest_permission = Permission.EDIT

        # If no shares found but drawing is public, grant view permission
        if highest_permission is None and drawing.is_public:
            highest_permission = Permission.VIEW

        return highest_permission
