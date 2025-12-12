"""Authentication schemas for API validation."""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    email: str = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters with complexity requirements)",
    )
    full_name: Optional[str] = Field(
        None, max_length=255, description="User's full name"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (allows localhost for development)."""
        v = v.strip().lower()
        # Basic email regex that allows localhost
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements.

        Requirements:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePass123",
                    "full_name": "John Doe",
                }
            ]
        }
    }


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (allows localhost for development)."""
        v = v.strip().lower()
        # Basic email regex that allows localhost
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "password": "SecurePass123",
                }
            ]
        }
    }


class VerifyEmailRequest(BaseModel):
    """Schema for email verification request."""

    token: str = Field(
        ..., min_length=1, max_length=255, description="Email verification token"
    )

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate and clean token."""
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "token": "abc123def456",
                }
            ]
        }
    }


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., min_length=1, description="Refresh token")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                }
            ]
        }
    }


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: str = Field(..., description="User email address")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format (allows localhost for development)."""
        v = v.strip().lower()
        # Basic email regex that allows localhost
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?$'
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                }
            ]
        }
    }


class PasswordResetConfirmRequest(BaseModel):
    """Schema for password reset confirmation."""

    token: str = Field(
        ..., min_length=1, max_length=255, description="Password reset token"
    )
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
                    "token": "abc123def456",
                    "new_password": "NewSecurePass123",
                }
            ]
        }
    }


class MFAVerifyRequest(BaseModel):
    """Schema for MFA verification request."""

    code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit MFA code"
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code is numeric and properly formatted."""
        v = v.strip()
        if not v.isdigit():
            raise ValueError("MFA code must contain only digits")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "123456",
                }
            ]
        }
    }


class MFADisableRequest(BaseModel):
    """Schema for MFA disable request."""

    password: str = Field(
        ..., min_length=1, description="User password for verification"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "password": "SecurePass123",
                }
            ]
        }
    }


class GoogleCallbackRequest(BaseModel):
    """Schema for Google OAuth callback request."""

    code: str = Field(
        ..., min_length=1, description="Authorization code from Google OAuth"
    )
    state: Optional[str] = Field(
        None, description="CSRF state parameter for security"
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate and clean authorization code."""
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "4/0AX4XfWh...",
                    "state": "random_state_value",
                }
            ]
        }
    }
