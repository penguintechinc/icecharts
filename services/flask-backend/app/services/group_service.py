"""Group management service for IceCharts."""

import datetime
from dataclasses import dataclass
from typing import Optional

from app.models import get_db


@dataclass(slots=True)
class GroupData:
    """Data class for group information."""

    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime


@dataclass(slots=True)
class MembershipData:
    """Data class for group membership information."""

    identity_id: int
    group_id: int
    expires_at: Optional[datetime.datetime]
    created_at: datetime.datetime


class GroupService:
    """Service for managing groups and memberships."""

    @staticmethod
    def create_group(
        owner_id: int, name: str, description: Optional[str] = None, tenant_id: int = 1
    ) -> dict:
        """
        Create a new group.

        Args:
            owner_id: ID of the user creating the group
            name: Name of the group
            description: Optional description
            tenant_id: Tenant ID (defaults to 1)

        Returns:
            Dictionary containing group data

        Raises:
            ValueError: If name is empty or group creation fails
        """
        if not name or not name.strip():
            raise ValueError("Group name cannot be empty")

        db = get_db()

        try:
            # Create group
            group_id = db.groups.insert(
                tenant_id=tenant_id,
                name=name.strip(),
                description=description.strip() if description else None,
                is_active=True,
            )
            db.commit()

            # Add owner as admin member
            db.group_memberships.insert(
                identity_id=owner_id,
                group_id=group_id,
            )
            db.commit()

            return GroupService.get_group_by_id(group_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to create group: {str(e)}")

    @staticmethod
    def get_group_by_id(group_id: int) -> Optional[dict]:
        """
        Get group by ID.

        Args:
            group_id: ID of the group

        Returns:
            Dictionary containing group data or None if not found
        """
        db = get_db()
        group = db(db.groups.id == group_id).select().first()

        if not group:
            return None

        return group.as_dict()

    @staticmethod
    def update_group(
        group_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[dict]:
        """
        Update group information.

        Args:
            group_id: ID of the group
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Updated group dictionary or None if not found

        Raises:
            ValueError: If update fails
        """
        db = get_db()

        # Check if group exists
        if not GroupService.get_group_by_id(group_id):
            return None

        update_data = {}
        if name is not None:
            if not name.strip():
                raise ValueError("Group name cannot be empty")
            update_data["name"] = name.strip()

        if description is not None:
            update_data["description"] = description.strip() if description else None

        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            return GroupService.get_group_by_id(group_id)

        try:
            db(db.groups.id == group_id).update(**update_data)
            db.commit()
            return GroupService.get_group_by_id(group_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update group: {str(e)}")

    @staticmethod
    def delete_group(group_id: int) -> bool:
        """
        Delete a group and all its memberships.

        Args:
            group_id: ID of the group

        Returns:
            True if deleted, False if group not found

        Raises:
            ValueError: If deletion fails
        """
        db = get_db()

        # Check if group exists
        if not GroupService.get_group_by_id(group_id):
            return False

        try:
            # Delete all memberships (cascade should handle this)
            db(db.group_memberships.group_id == group_id).delete()

            # Delete group
            deleted = db(db.groups.id == group_id).delete()
            db.commit()

            return deleted > 0

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to delete group: {str(e)}")

    @staticmethod
    def add_member(
        group_id: int, user_id: int, expires_at: Optional[datetime.datetime] = None
    ) -> dict:
        """
        Add a member to a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user to add
            expires_at: Optional expiration date for membership

        Returns:
            Dictionary containing membership data

        Raises:
            ValueError: If group or user not found, or member already exists
        """
        db = get_db()

        # Check if group exists
        if not GroupService.get_group_by_id(group_id):
            raise ValueError("Group not found")

        # Check if user exists
        user = db(db.identities.id == user_id).select().first()
        if not user:
            raise ValueError("User not found")

        # Check if already a member
        existing = (
            db(
                (db.group_memberships.group_id == group_id)
                & (db.group_memberships.identity_id == user_id)
            )
            .select()
            .first()
        )

        if existing:
            raise ValueError("User is already a member of this group")

        try:
            membership_id = db.group_memberships.insert(
                identity_id=user_id,
                group_id=group_id,
                expires_at=expires_at,
            )
            db.commit()

            return GroupService.get_membership(group_id, user_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to add member: {str(e)}")

    @staticmethod
    def remove_member(group_id: int, user_id: int) -> bool:
        """
        Remove a member from a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user to remove

        Returns:
            True if removed, False if membership not found

        Raises:
            ValueError: If removal fails
        """
        db = get_db()

        try:
            deleted = db(
                (db.group_memberships.group_id == group_id)
                & (db.group_memberships.identity_id == user_id)
            ).delete()
            db.commit()

            return deleted > 0

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to remove member: {str(e)}")

    @staticmethod
    def update_member_role(
        group_id: int, user_id: int, expires_at: Optional[datetime.datetime] = None
    ) -> Optional[dict]:
        """
        Update a member's role or expiration in a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user
            expires_at: New expiration date (or None for no expiration)

        Returns:
            Updated membership dictionary or None if not found

        Raises:
            ValueError: If update fails
        """
        db = get_db()

        # Check if membership exists
        membership = GroupService.get_membership(group_id, user_id)
        if not membership:
            return None

        try:
            db(
                (db.group_memberships.group_id == group_id)
                & (db.group_memberships.identity_id == user_id)
            ).update(expires_at=expires_at)
            db.commit()

            return GroupService.get_membership(group_id, user_id)

        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to update member role: {str(e)}")

    @staticmethod
    def get_membership(group_id: int, user_id: int) -> Optional[dict]:
        """
        Get membership information for a user in a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user

        Returns:
            Dictionary containing membership data or None if not found
        """
        db = get_db()
        membership = (
            db(
                (db.group_memberships.group_id == group_id)
                & (db.group_memberships.identity_id == user_id)
            )
            .select()
            .first()
        )

        if not membership:
            return None

        return membership.as_dict()

    @staticmethod
    def list_group_members(group_id: int) -> list[dict]:
        """
        List all members of a group with user details.

        Args:
            group_id: ID of the group

        Returns:
            List of dictionaries containing member and user data
        """
        db = get_db()

        # Join with identities to get user details
        members = db(
            (db.group_memberships.group_id == group_id)
            & (db.group_memberships.identity_id == db.identities.id)
        ).select(
            db.group_memberships.ALL,
            db.identities.id,
            db.identities.username,
            db.identities.email,
            db.identities.full_name,
            orderby=db.group_memberships.created_at,
        )

        result = []
        for m in members:
            result.append(
                {
                    "identity_id": m.identities.id,
                    "username": m.identities.username,
                    "email": m.identities.email,
                    "full_name": m.identities.full_name,
                    "expires_at": (
                        m.group_memberships.expires_at.isoformat()
                        if m.group_memberships.expires_at
                        else None
                    ),
                    "created_at": (
                        m.group_memberships.created_at.isoformat()
                        if m.group_memberships.created_at
                        else None
                    ),
                }
            )

        return result

    @staticmethod
    def list_user_groups(user_id: int) -> list[dict]:
        """
        List all groups a user is a member of.

        Args:
            user_id: ID of the user

        Returns:
            List of dictionaries containing group data
        """
        db = get_db()

        # Join with groups to get group details
        memberships = db(
            (db.group_memberships.identity_id == user_id)
            & (db.group_memberships.group_id == db.groups.id)
        ).select(
            db.groups.ALL,
            orderby=db.groups.name,
        )

        return [g.groups.as_dict() for g in memberships]

    @staticmethod
    def is_member(group_id: int, user_id: int) -> bool:
        """
        Check if a user is a member of a group.

        Args:
            group_id: ID of the group
            user_id: ID of the user

        Returns:
            True if user is a member
        """
        membership = GroupService.get_membership(group_id, user_id)
        if not membership:
            return False

        # Check if membership has expired
        if membership.get("expires_at"):
            expires_at = membership["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.datetime.fromisoformat(expires_at)
            if expires_at < datetime.datetime.now(datetime.timezone.utc):
                return False

        return True

    @staticmethod
    def get_member_count(group_id: int) -> int:
        """
        Get the number of members in a group.

        Args:
            group_id: ID of the group

        Returns:
            Number of members
        """
        db = get_db()
        return db(db.group_memberships.group_id == group_id).count()
