"""Drawing sharing service for IceCharts."""

import datetime
import secrets
from dataclasses import dataclass
from typing import Optional

from app.models import get_db
from app.services.permission_service import Permission, PermissionService
from flask import request


@dataclass(slots=True)
class ShareData:
    """Data class for share information."""

    id: int
    drawing_id: int
    shared_with_id: Optional[int]
    shared_with_group_id: Optional[int]
    permission: str
    expires_at: Optional[datetime.datetime]
    share_token: Optional[str]
    created_at: datetime.datetime


class ShareService:
    """Service for managing drawing shares."""

    @staticmethod
    def _generate_share_token() -> str:
        """
        Generate a secure random token for public shares.

        Returns:
            Random token string
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_share(
        drawing_id: int,
        created_by_id: int,
        permission: str = Permission.VIEW,
        shared_with_id: Optional[int] = None,
        shared_with_group_id: Optional[int] = None,
        expires_at: Optional[datetime.datetime] = None,
        generate_token: bool = False,
    ) -> dict:
        """
        Create a share for a drawing.

        Args:
            drawing_id: ID of the drawing to share
            created_by_id: ID of the user creating the share
            permission: Permission level (viewer, editor, admin)
            shared_with_id: ID of user to share with (for user shares)
            shared_with_group_id: ID of group to share with (for group shares)
            expires_at: Optional expiration datetime
            generate_token: Whether to generate a public share token

        Returns:
            Dictionary containing share data

        Raises:
            PermissionError: If user doesn't have share permission
            ValueError: If share creation fails or validation fails
        """
        # Validate share type
        if not shared_with_id and not shared_with_group_id and not generate_token:
            raise ValueError(
                "Must specify either shared_with_id, shared_with_group_id, "
                "or generate_token=True for public share"
            )

        if (
            (shared_with_id and shared_with_group_id)
            or (shared_with_id and generate_token)
            or (shared_with_group_id and generate_token)
        ):
            raise ValueError(
                "Share can only be for one target (user, group, or public)"
            )

        # Check if user can share the drawing
        if not PermissionService.can_share_drawing(created_by_id, drawing_id):
            raise PermissionError("You don't have permission to share this drawing")

        # Validate permission level
        if permission not in [Permission.VIEW, Permission.EDIT, Permission.ADMIN]:
            raise ValueError(f"Invalid permission level: {permission}")

        db = get_db()

        # Check if drawing exists
        if not db(db.drawings.id == drawing_id).select().first():
            raise ValueError("Drawing not found")

        # Validate target user/group exists
        if shared_with_id:
            if not db(db.identities.id == shared_with_id).select().first():
                raise ValueError("Target user not found")

            # Check if share already exists for this user
            existing = (
                db(
                    (db.drawing_shares.drawing_id == drawing_id)
                    & (db.drawing_shares.shared_with_id == shared_with_id)
                )
                .select()
                .first()
            )
            if existing:
                raise ValueError("Drawing is already shared with this user")

        if shared_with_group_id:
            if not db(db.groups.id == shared_with_group_id).select().first():
                raise ValueError("Target group not found")

            # Check if share already exists for this group
            existing = (
                db(
                    (db.drawing_shares.drawing_id == drawing_id)
                    & (db.drawing_shares.shared_with_group_id == shared_with_group_id)
                )
                .select()
                .first()
            )
            if existing:
                raise ValueError("Drawing is already shared with this group")

        # Generate token for public shares
        share_token = ShareService._generate_share_token() if generate_token else None

        try:
            share_id = db.drawing_shares.insert(
                drawing_id=drawing_id,
                shared_with_id=shared_with_id,
                shared_with_group_id=shared_with_group_id,
                permission=permission,
                expires_at=expires_at,
                share_token=share_token,
            )
            db.commit()

            return ShareService.get_share_by_id(share_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create share: {str(e)}")

    @staticmethod
    def get_share_by_id(share_id: int) -> Optional[dict]:
        """
        Get share by ID.

        Args:
            share_id: ID of the share

        Returns:
            Dictionary containing share data or None if not found
        """
        db = get_db()
        share = db(db.drawing_shares.id == share_id).select().first()
        return share.as_dict() if share else None

    @staticmethod
    def get_by_token(token: str) -> Optional[dict]:
        """
        Get drawing by public share token.

        Args:
            token: Public share token

        Returns:
            Dictionary containing drawing data or None if not found/expired
        """
        db = get_db()

        # Get share by token
        share = db(db.drawing_shares.share_token == token).select().first()
        if not share:
            return None

        # Check if expired
        if share.expires_at:
            if share.expires_at < datetime.datetime.now(datetime.timezone.utc):
                return None

        # Get drawing
        drawing = db(db.drawings.id == share.drawing_id).select().first()
        if not drawing:
            return None

        drawing_dict = drawing.as_dict()
        drawing_dict["share_permission"] = share.permission
        return drawing_dict

    @staticmethod
    def list_shares(drawing_id: int, user_id: int) -> list[dict]:
        """
        List all shares for a drawing.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user requesting shares

        Returns:
            List of share dictionaries with target details

        Raises:
            PermissionError: If user doesn't have share permission
            ValueError: If drawing not found
        """
        db = get_db()

        # Check if drawing exists
        if not db(db.drawings.id == drawing_id).select().first():
            raise ValueError("Drawing not found")

        # Check if user can view shares (must have share permission)
        if not PermissionService.can_share_drawing(user_id, drawing_id):
            raise PermissionError(
                "You don't have permission to view shares for this drawing"
            )

        # Get all shares with user/group details
        shares = db(db.drawing_shares.drawing_id == drawing_id).select(
            orderby=db.drawing_shares.created_at
        )

        result = []
        for share in shares:
            share_dict = share.as_dict()

            # Add user details if shared with user
            if share.shared_with_id:
                user = db(db.identities.id == share.shared_with_id).select().first()
                if user:
                    share_dict["shared_with_user"] = {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "full_name": user.full_name,
                    }

            # Add group details if shared with group
            if share.shared_with_group_id:
                group = db(db.groups.id == share.shared_with_group_id).select().first()
                if group:
                    share_dict["shared_with_group"] = {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                    }

            # Indicate if this is a public share
            share_dict["is_public"] = bool(share.share_token)

            result.append(share_dict)

        return result

    @staticmethod
    def update_share(
        share_id: int,
        user_id: int,
        permission: Optional[str] = None,
        expires_at: Optional[datetime.datetime] = None,
    ) -> Optional[dict]:
        """
        Update an existing share.

        Args:
            share_id: ID of the share
            user_id: ID of the user updating the share
            permission: New permission level (optional)
            expires_at: New expiration datetime (optional)

        Returns:
            Updated share dictionary or None if not found

        Raises:
            PermissionError: If user doesn't have share permission
            ValueError: If update fails
        """
        db = get_db()

        # Get share
        share = ShareService.get_share_by_id(share_id)
        if not share:
            return None

        # Check if user can update this share
        if not PermissionService.can_share_drawing(user_id, share["drawing_id"]):
            raise PermissionError("You don't have permission to update this share")

        update_data = {}
        if permission is not None:
            if permission not in [Permission.VIEW, Permission.EDIT, Permission.ADMIN]:
                raise ValueError(f"Invalid permission level: {permission}")
            update_data["permission"] = permission

        if expires_at is not None:
            update_data["expires_at"] = expires_at

        if not update_data:
            return share

        try:
            db(db.drawing_shares.id == share_id).update(**update_data)
            db.commit()
            return ShareService.get_share_by_id(share_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update share: {str(e)}")

    @staticmethod
    def revoke_share(share_id: int, user_id: int) -> bool:
        """
        Revoke (delete) a share.

        Args:
            share_id: ID of the share
            user_id: ID of the user revoking the share

        Returns:
            True if revoked, False if share not found

        Raises:
            PermissionError: If user doesn't have share permission
            ValueError: If revocation fails
        """
        db = get_db()

        # Get share
        share = ShareService.get_share_by_id(share_id)
        if not share:
            return False

        # Check if user can revoke this share
        if not PermissionService.can_share_drawing(user_id, share["drawing_id"]):
            raise PermissionError("You don't have permission to revoke this share")

        try:
            deleted = db(db.drawing_shares.id == share_id).delete()
            db.commit()
            return deleted > 0

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to revoke share: {str(e)}")

    @staticmethod
    def check_share_permission(drawing_id: int, user_id: int) -> Optional[str]:
        """
        Check the permission level a user has via shares.

        Args:
            drawing_id: ID of the drawing
            user_id: ID of the user

        Returns:
            Permission level string or None if no share exists
        """
        db = get_db()

        # Check direct user share
        user_share = (
            db(
                (db.drawing_shares.drawing_id == drawing_id)
                & (db.drawing_shares.shared_with_id == user_id)
            )
            .select()
            .first()
        )

        highest_permission = user_share.permission if user_share else None

        # Check group shares
        user_groups = db(db.group_memberships.identity_id == user_id).select(
            db.group_memberships.group_id
        )

        group_ids = [g.group_id for g in user_groups]

        if group_ids:
            group_shares = db(
                (db.drawing_shares.drawing_id == drawing_id)
                & (db.drawing_shares.shared_with_group_id.belongs(group_ids))
            ).select()

            # Get highest permission from group shares
            for share in group_shares:
                if highest_permission is None:
                    highest_permission = share.permission
                elif share.permission == Permission.ADMIN:
                    highest_permission = Permission.ADMIN
                elif (
                    share.permission == Permission.EDIT
                    and highest_permission == Permission.VIEW
                ):
                    highest_permission = Permission.EDIT

        return highest_permission

    @staticmethod
    def regenerate_public_token(share_id: int, user_id: int) -> dict:
        """
        Regenerate public share token (invalidates old one).

        Args:
            share_id: ID of the share
            user_id: ID of the user regenerating the token

        Returns:
            Updated share dictionary with new token

        Raises:
            PermissionError: If user doesn't have share permission
            ValueError: If share is not a public share or update fails
        """
        db = get_db()

        # Get share
        share = ShareService.get_share_by_id(share_id)
        if not share:
            raise ValueError("Share not found")

        # Verify it's a public share
        if not share.get("share_token"):
            raise ValueError("This is not a public share")

        # Check permission
        if not PermissionService.can_share_drawing(user_id, share["drawing_id"]):
            raise PermissionError(
                "You don't have permission to regenerate this share token"
            )

        # Generate new token
        new_token = ShareService._generate_share_token()

        try:
            db(db.drawing_shares.id == share_id).update(share_token=new_token)
            db.commit()
            return ShareService.get_share_by_id(share_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to regenerate token: {str(e)}")

    @staticmethod
    def get_shared_drawings(
        user_id: int, page: int = 1, per_page: int = 20
    ) -> tuple[list[dict], int]:
        """
        Get all drawings shared with a user (directly or via groups).

        Args:
            user_id: ID of the user
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            Tuple of (list of drawing dictionaries, total count)
        """
        db = get_db()
        offset = (page - 1) * per_page

        # Get user's groups
        user_groups = db(db.group_memberships.identity_id == user_id).select(
            db.group_memberships.group_id
        )
        group_ids = [g.group_id for g in user_groups]

        # Build query for shared drawings
        query = (
            (db.drawing_shares.shared_with_id == user_id)
            | (db.drawing_shares.shared_with_group_id.belongs(group_ids))
            if group_ids
            else (db.drawing_shares.shared_with_id == user_id)
        )

        # Get unique drawing IDs
        shares = db(query).select(db.drawing_shares.drawing_id, distinct=True)
        drawing_ids = [s.drawing_id for s in shares]

        if not drawing_ids:
            return [], 0

        # Get drawings
        drawings = db(db.drawings.id.belongs(drawing_ids)).select(
            orderby=~db.drawings.updated_at,
            limitby=(offset, offset + per_page),
        )

        total = db(db.drawings.id.belongs(drawing_ids)).count()

        return [d.as_dict() for d in drawings], total

    @staticmethod
    def get_drawing_by_token(
        token: str, user_id: Optional[int] = None, log_access: bool = True
    ) -> Optional[dict]:
        """
        Access drawing via public share token.

        This method verifies that the token exists and is not expired,
        then checks share permissions (link_only vs registered_users).
        If permitted, it logs the access and returns the drawing data.

        Args:
            token: Public share token
            user_id: ID of the accessing user (None if unauthenticated)
            log_access: Whether to log access to share_analytics table

        Returns:
            Dictionary containing drawing data if permission allows, None otherwise

        Raises:
            ValueError: If token format is invalid or other validation fails
        """
        db = get_db()

        # Get share by token
        share = db(db.drawing_shares.share_token == token).select().first()
        if not share:
            return None

        # Check if share is public
        if not share.is_public:
            return None

        # Check if expired
        if share.expires_at:
            if share.expires_at < datetime.datetime.now(datetime.timezone.utc):
                return None

        # Get drawing
        drawing = db(db.drawings.id == share.drawing_id).select().first()
        if not drawing:
            return None

        # Determine share mode (default to link_only for backwards compatibility)
        share_mode = (
            share.get("share_mode", "link_only")
            if hasattr(share, "get")
            else "link_only"
        )

        # Check access permissions
        if share_mode == "registered_users" and user_id is None:
            # Registered users mode requires authentication
            return None

        # Log access if requested
        if log_access:
            try:
                # Get client IP address (handle proxy headers)
                client_ip = request.remote_addr
                if request.headers.getlist("X-Forwarded-For"):
                    client_ip = request.headers.getlist("X-Forwarded-For")[0]
                elif request.headers.get("X-Real-IP"):
                    client_ip = request.headers.get("X-Real-IP")

                # Get user agent
                user_agent = request.headers.get("User-Agent", "")[:500]

                # Log to share_analytics table
                db.share_analytics.insert(
                    share_type="drawing",
                    share_id=share.drawing_id,
                    share_token=token,
                    accessed_by_id=user_id,
                    access_ip=client_ip,
                    user_agent=user_agent,
                    accessed_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.commit()
            except Exception as e:
                # Log errors but don't fail the request if analytics logging fails
                db.rollback()
                # In production, you might want to log this error properly

        # Return drawing with permission info
        drawing_dict = drawing.as_dict()
        drawing_dict["share_permission"] = share.permission
        drawing_dict["share_mode"] = share_mode
        return drawing_dict
