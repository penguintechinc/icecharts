"""Service account schemas for API validation."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from ..auth.scopes import AVAILABLE_SCOPES, validate_scopes


class CreateServiceAccountRequest(BaseModel):
    """Schema for creating a new service account."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the service account",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional description of the service account's purpose",
    )
    scopes: List[str] = Field(
        ...,
        min_length=1,
        description="List of permission scopes for this service account",
    )
    rate_limit: Optional[int] = Field(
        default=1000,
        ge=1,
        le=100000,
        description="Rate limit in requests per hour (default: 1000)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name."""
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Name cannot be empty or whitespace only")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: List[str]) -> List[str]:
        """Validate scopes are valid."""
        if not v:
            raise ValueError("At least one scope is required")

        # Remove duplicates and validate
        v = list(set(v))
        is_valid, invalid_scopes = validate_scopes(v)

        if not is_valid:
            raise ValueError(
                f"Invalid scopes: {', '.join(invalid_scopes)}. "
                f"Available scopes: {', '.join(AVAILABLE_SCOPES.keys())}"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Elder Integration",
                    "description": "Service account for Elder app integration",
                    "scopes": ["drawings:read", "drawings:write", "exports:create"],
                    "rate_limit": 1000,
                }
            ]
        }
    }


class UpdateServiceAccountRequest(BaseModel):
    """Schema for updating a service account."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Updated name",
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Updated description",
    )
    scopes: Optional[List[str]] = Field(
        None,
        description="Updated list of permission scopes",
    )
    rate_limit: Optional[int] = Field(
        None,
        ge=1,
        le=100000,
        description="Updated rate limit in requests per hour",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the service account is active",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Name cannot be empty or whitespace only")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate scopes are valid."""
        if v is not None:
            if not v:
                raise ValueError("At least one scope is required")

            # Remove duplicates and validate
            v = list(set(v))
            is_valid, invalid_scopes = validate_scopes(v)

            if not is_valid:
                raise ValueError(
                    f"Invalid scopes: {', '.join(invalid_scopes)}. "
                    f"Available scopes: {', '.join(AVAILABLE_SCOPES.keys())}"
                )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Elder Integration",
                    "scopes": ["drawings:read", "exports:create"],
                    "is_active": True,
                }
            ]
        }
    }


class GenerateTokenRequest(BaseModel):
    """Schema for generating a new service account token."""

    name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional name/label for this token",
    )
    expires_days: int = Field(
        default=365,
        ge=1,
        le=365,
        description="Number of days until token expires (1-365)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Production Token",
                    "expires_days": 365,
                }
            ]
        }
    }


class ServiceAccountResponse(BaseModel):
    """Response schema for service account data."""

    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    client_id: str
    scopes: List[str]
    rate_limit: int
    is_active: bool
    created_by_id: int
    last_used_at: Optional[str]
    created_at: str
    updated_at: Optional[str]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "tenant_id": 1,
                    "name": "Elder Integration",
                    "description": "Service account for Elder app",
                    "client_id": "sa_abc123def456",
                    "scopes": ["drawings:read", "exports:create"],
                    "rate_limit": 1000,
                    "is_active": True,
                    "created_by_id": 1,
                    "last_used_at": None,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Response schema for service account token data."""

    id: int
    service_account_id: int
    token_jti: str
    name: Optional[str]
    expires_at: str
    last_used_at: Optional[str]
    last_used_ip: Optional[str]
    revoked_at: Optional[str]
    created_at: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "service_account_id": 1,
                    "token_jti": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Production Token",
                    "expires_at": "2025-01-01T00:00:00Z",
                    "last_used_at": "2024-06-15T10:30:00Z",
                    "last_used_ip": "192.168.1.1",
                    "revoked_at": None,
                    "created_at": "2024-01-01T00:00:00Z",
                }
            ]
        }
    }


class GeneratedTokenResponse(BaseModel):
    """Response schema for a newly generated token (includes the actual token)."""

    token: str = Field(
        ...,
        description="The JWT token. Store this securely - it cannot be retrieved again.",
    )
    token_info: TokenResponse

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_info": {
                        "id": 1,
                        "service_account_id": 1,
                        "token_jti": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Production Token",
                        "expires_at": "2025-01-01T00:00:00Z",
                        "last_used_at": None,
                        "last_used_ip": None,
                        "revoked_at": None,
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                }
            ]
        }
    }


class AvailableScopesResponse(BaseModel):
    """Response schema for available scopes."""

    scopes: dict = Field(
        ...,
        description="Dictionary of scope names to descriptions",
    )
    scope_groups: dict = Field(
        ...,
        description="Dictionary of scope group names to their included scopes",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scopes": {
                        "drawings:read": "Read drawing metadata and content",
                        "drawings:write": "Create and update drawings",
                    },
                    "scope_groups": {
                        "readonly": ["drawings:read", "exports:read"],
                    },
                }
            ]
        }
    }
