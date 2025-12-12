"""Pydantic schemas for API request validation.

This module provides comprehensive validation schemas for all API endpoints
using Pydantic v2. Each schema includes proper type hints, field validators,
and constraints to ensure data integrity and security.
"""

# Common schemas
from .common_schemas import PaginationParams

# Authentication schemas
from .auth_schemas import (
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    VerifyEmailRequest,
)

# Drawing schemas
from .drawing_schemas import (
    CreateDrawingRequest,
    ExportDrawingRequest,
    UpdateDrawingRequest,
)

# Collection schemas
from .collection_schemas import (
    AddDrawingToCollectionRequest,
    CreateCollectionRequest,
    RemoveDrawingFromCollectionRequest,
    ReorderCollectionDrawingsRequest,
    UpdateCollectionRequest,
)

# Share schemas
from .share_schemas import (
    CreateShareRequest,
    GenerateShareTokenRequest,
    RevokeShareRequest,
    UpdateShareRequest,
)

# User schemas
from .user_schemas import (
    CreateUserRequest,
    UpdatePasswordRequest,
    UpdateUserRequest,
)

__all__ = [
    # Common
    "PaginationParams",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "VerifyEmailRequest",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirmRequest",
    # Drawing
    "CreateDrawingRequest",
    "UpdateDrawingRequest",
    "ExportDrawingRequest",
    # Collection
    "CreateCollectionRequest",
    "UpdateCollectionRequest",
    "AddDrawingToCollectionRequest",
    "RemoveDrawingFromCollectionRequest",
    "ReorderCollectionDrawingsRequest",
    # Share
    "CreateShareRequest",
    "UpdateShareRequest",
    "GenerateShareTokenRequest",
    "RevokeShareRequest",
    # User
    "UpdateUserRequest",
    "UpdatePasswordRequest",
    "CreateUserRequest",
]
