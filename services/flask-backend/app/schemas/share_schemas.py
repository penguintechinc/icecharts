"""Share schemas for API validation."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateShareRequest(BaseModel):
    """Schema for creating a share (drawing or collection)."""

    share_type: str = Field(
        ..., description="Type of share: 'drawing' or 'collection'"
    )
    shared_with_id: Optional[int] = Field(
        None, gt=0, description="ID of user to share with (for user sharing)"
    )
    shared_with_group_id: Optional[int] = Field(
        None, gt=0, description="ID of group to share with (for group sharing)"
    )
    permission: Optional[str] = Field(
        default="viewer", description="Permission level: 'viewer', 'editor', or 'admin'"
    )
    share_mode: Optional[str] = Field(
        None,
        description="Share mode for public links: 'private', 'link_only', or 'registered_users'",
    )

    @field_validator("share_type")
    @classmethod
    def validate_share_type(cls, v: str) -> str:
        """Validate share type."""
        v = v.lower()
        if v not in ["drawing", "collection"]:
            raise ValueError("share_type must be 'drawing' or 'collection'")
        return v

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, v: Optional[str]) -> str:
        """Validate permission level."""
        if v is None:
            return "viewer"
        v = v.lower()
        if v not in ["viewer", "editor", "admin"]:
            raise ValueError("permission must be 'viewer', 'editor', or 'admin'")
        return v

    @field_validator("share_mode")
    @classmethod
    def validate_share_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate share mode."""
        if v is not None:
            v = v.lower()
            if v not in ["private", "link_only", "registered_users"]:
                raise ValueError(
                    "share_mode must be 'private', 'link_only', or 'registered_users'"
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "share_type": "drawing",
                    "shared_with_id": 123,
                    "permission": "viewer",
                },
                {
                    "share_type": "collection",
                    "shared_with_group_id": 456,
                    "permission": "editor",
                },
                {
                    "share_type": "drawing",
                    "share_mode": "link_only",
                },
            ]
        }
    }


class UpdateShareRequest(BaseModel):
    """Schema for updating a share."""

    permission: str = Field(
        ..., description="Permission level: 'viewer', 'editor', or 'admin'"
    )

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, v: str) -> str:
        """Validate permission level."""
        v = v.lower()
        if v not in ["viewer", "editor", "admin"]:
            raise ValueError("permission must be 'viewer', 'editor', or 'admin'")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "permission": "editor",
                }
            ]
        }
    }


class GenerateShareTokenRequest(BaseModel):
    """Schema for generating a public share token."""

    share_mode: Optional[str] = Field(
        default="link_only",
        description="Share mode: 'link_only' or 'registered_users'",
    )

    @field_validator("share_mode")
    @classmethod
    def validate_share_mode(cls, v: Optional[str]) -> str:
        """Validate share mode."""
        if v is None:
            return "link_only"
        v = v.lower()
        if v not in ["link_only", "registered_users"]:
            raise ValueError("share_mode must be 'link_only' or 'registered_users'")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "share_mode": "link_only",
                }
            ]
        }
    }


class RevokeShareRequest(BaseModel):
    """Schema for revoking a share."""

    share_id: int = Field(..., gt=0, description="ID of the share to revoke")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "share_id": 123,
                }
            ]
        }
    }
