"""User schemas for API validation."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UpdateUserRequest(BaseModel):
    """Schema for updating user profile."""

    email: Optional[EmailStr] = Field(None, description="User email address")
    full_name: Optional[str] = Field(
        None, max_length=255, description="User's full name"
    )
    role: Optional[str] = Field(
        None, description="User role: 'viewer', 'editor', 'admin', or 'global_admin'"
    )
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    avatar_url: Optional[str] = Field(
        None, max_length=500, description="URL to user's avatar"
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean full name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Validate user role."""
        if v is not None:
            v = v.lower()
            if v not in ["viewer", "editor", "admin", "global_admin"]:
                raise ValueError(
                    "role must be 'viewer', 'editor', 'admin', or 'global_admin'"
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "full_name": "John Doe",
                    "avatar_url": "https://example.com/avatar.jpg",
                }
            ]
        }
    }


class UpdatePasswordRequest(BaseModel):
    """Schema for updating user password."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (8-128 characters with complexity requirements)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_password": "OldPass123",
                    "new_password": "NewSecurePass456",
                }
            ]
        }
    }


class CreateUserRequest(BaseModel):
    """Schema for creating a new user (admin only)."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters with complexity requirements)",
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="User's full name"
    )
    role: Optional[str] = Field(
        default="viewer",
        description="User role: 'viewer', 'editor', 'admin', or 'global_admin'",
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean full name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> str:
        """Validate user role."""
        if v is None:
            return "viewer"
        v = v.lower()
        if v not in ["viewer", "editor", "admin", "global_admin"]:
            raise ValueError(
                "role must be 'viewer', 'editor', 'admin', or 'global_admin'"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "newuser@example.com",
                    "password": "SecurePass123",
                    "full_name": "Jane Smith",
                    "role": "editor",
                }
            ]
        }
    }
