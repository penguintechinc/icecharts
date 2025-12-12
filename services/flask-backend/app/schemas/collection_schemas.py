"""Collection schemas for API validation."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CreateCollectionRequest(BaseModel):
    """Schema for creating a new collection."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Collection name/title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Collection description"
    )
    is_public: Optional[bool] = Field(
        default=False, description="Whether this collection is public"
    )
    share_mode: Optional[str] = Field(
        default="private",
        description="Share mode: 'private', 'link_only', or 'registered_users'",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean collection name."""
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Collection name cannot be empty or whitespace only")
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

    @field_validator("share_mode")
    @classmethod
    def validate_share_mode(cls, v: Optional[str]) -> str:
        """Validate share mode."""
        if v is None:
            return "private"
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
                    "name": "My Architecture Collection",
                    "description": "Cloud infrastructure diagrams",
                    "is_public": False,
                    "share_mode": "private",
                }
            ]
        }
    }


class UpdateCollectionRequest(BaseModel):
    """Schema for updating an existing collection."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Collection name/title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Collection description"
    )
    is_public: Optional[bool] = Field(
        None, description="Whether this collection is public"
    )
    share_mode: Optional[str] = Field(
        None,
        description="Share mode: 'private', 'link_only', or 'registered_users'",
    )
    thumbnail_url: Optional[str] = Field(
        None, max_length=500, description="URL to collection thumbnail"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean collection name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Collection name cannot be empty or whitespace only")
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
                    "name": "Updated Collection Name",
                    "description": "Updated description",
                    "share_mode": "link_only",
                }
            ]
        }
    }


class AddDrawingToCollectionRequest(BaseModel):
    """Schema for adding a drawing to a collection."""

    drawing_id: int = Field(..., gt=0, description="ID of the drawing to add")
    order_index: Optional[int] = Field(
        default=0, ge=0, description="Order index for the drawing in the collection"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "drawing_id": 123,
                    "order_index": 0,
                }
            ]
        }
    }


class RemoveDrawingFromCollectionRequest(BaseModel):
    """Schema for removing a drawing from a collection."""

    drawing_id: int = Field(..., gt=0, description="ID of the drawing to remove")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "drawing_id": 123,
                }
            ]
        }
    }


class ReorderCollectionDrawingsRequest(BaseModel):
    """Schema for reordering drawings in a collection."""

    drawing_orders: List[dict] = Field(
        ...,
        description="List of {drawing_id, order_index} objects",
        min_length=1,
    )

    @field_validator("drawing_orders")
    @classmethod
    def validate_drawing_orders(cls, v: List[dict]) -> List[dict]:
        """Validate drawing order entries."""
        for item in v:
            if "drawing_id" not in item:
                raise ValueError("Each entry must have 'drawing_id'")
            if "order_index" not in item:
                raise ValueError("Each entry must have 'order_index'")
            if not isinstance(item["drawing_id"], int) or item["drawing_id"] <= 0:
                raise ValueError("drawing_id must be a positive integer")
            if not isinstance(item["order_index"], int) or item["order_index"] < 0:
                raise ValueError("order_index must be a non-negative integer")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "drawing_orders": [
                        {"drawing_id": 123, "order_index": 0},
                        {"drawing_id": 456, "order_index": 1},
                        {"drawing_id": 789, "order_index": 2},
                    ]
                }
            ]
        }
    }
