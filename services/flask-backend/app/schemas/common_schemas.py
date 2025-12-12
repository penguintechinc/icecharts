"""Common schemas used across multiple API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    )
    sort_by: Optional[str] = Field(
        default=None, description="Field to sort by (e.g., 'created_at', 'updated_at')"
    )
    sort_order: Optional[str] = Field(
        default="desc", description="Sort order: 'asc' or 'desc'"
    )

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: Optional[str]) -> Optional[str]:
        """Validate sort order is either 'asc' or 'desc'."""
        if v is not None and v.lower() not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower() if v else None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page": 1,
                    "per_page": 20,
                    "sort_by": "created_at",
                    "sort_order": "desc",
                }
            ]
        }
    }
