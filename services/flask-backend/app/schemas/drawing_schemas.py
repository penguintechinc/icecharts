"""Drawing schemas for API validation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CreateDrawingRequest(BaseModel):
    """Schema for creating a new drawing."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Drawing name/title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Drawing description"
    )
    content: Optional[Dict[str, Any]] = Field(
        None, description="Drawing content (nodes, edges, etc.)"
    )
    visibility: Optional[str] = Field(
        default="private", description="Drawing visibility: 'private' or 'public'"
    )
    is_template: Optional[bool] = Field(
        default=False, description="Whether this drawing is a template"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="List of tags for the drawing"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean drawing name."""
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Drawing name cannot be empty or whitespace only")
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

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: Optional[str]) -> str:
        """Validate visibility is either 'private' or 'public'."""
        if v is None:
            return "private"
        v = v.lower()
        if v not in ["private", "public"]:
            raise ValueError("visibility must be 'private' or 'public'")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate content structure."""
        if v is None:
            return {"nodes": [], "edges": []}
        # Ensure basic structure
        if not isinstance(v, dict):
            raise ValueError("content must be a dictionary")
        # Add default nodes/edges if not present
        if "nodes" not in v:
            v["nodes"] = []
        if "edges" not in v:
            v["edges"] = []
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if v is not None:
            # Remove empty strings and duplicates, strip whitespace
            cleaned = list(set([tag.strip() for tag in v if tag.strip()]))
            return cleaned if cleaned else None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "My Architecture Diagram",
                    "description": "Cloud infrastructure design",
                    "content": {"nodes": [], "edges": []},
                    "visibility": "private",
                    "is_template": False,
                    "tags": ["cloud", "aws"],
                }
            ]
        }
    }


class UpdateDrawingRequest(BaseModel):
    """Schema for updating an existing drawing."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Drawing name/title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Drawing description"
    )
    content: Optional[Dict[str, Any]] = Field(
        None, description="Drawing content (nodes, edges, etc.)"
    )
    visibility: Optional[str] = Field(
        None, description="Drawing visibility: 'private' or 'public'"
    )
    is_template: Optional[bool] = Field(
        None, description="Whether this drawing is a template"
    )
    tags: Optional[List[str]] = Field(None, description="List of tags for the drawing")
    status: Optional[str] = Field(
        None, description="Drawing status (e.g., 'draft', 'published')"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean drawing name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Drawing name cannot be empty or whitespace only")
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

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: Optional[str]) -> Optional[str]:
        """Validate visibility is either 'private' or 'public'."""
        if v is not None:
            v = v.lower()
            if v not in ["private", "public"]:
                raise ValueError("visibility must be 'private' or 'public'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status."""
        if v is not None:
            v = v.lower()
            if v not in ["draft", "published", "archived"]:
                raise ValueError("status must be 'draft', 'published', or 'archived'")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if v is not None:
            # Remove empty strings and duplicates, strip whitespace
            cleaned = list(set([tag.strip() for tag in v if tag.strip()]))
            return cleaned if cleaned else None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Architecture Diagram",
                    "description": "Updated cloud infrastructure design",
                    "visibility": "public",
                    "tags": ["cloud", "aws", "serverless"],
                }
            ]
        }
    }


class ExportDrawingRequest(BaseModel):
    """Schema for exporting a drawing."""

    format: str = Field(
        ..., description="Export format: 'png', 'jpg', 'svg', 'pdf', or 'json'"
    )
    width: Optional[int] = Field(
        default=800, ge=100, le=8000, description="Export width in pixels"
    )
    height: Optional[int] = Field(
        default=600, ge=100, le=8000, description="Export height in pixels"
    )
    include_background: Optional[bool] = Field(
        default=True, description="Include background (for PNG/JPG)"
    )
    background_color: Optional[str] = Field(
        default="#ffffff", description="Background color (hex format)"
    )
    quality: Optional[int] = Field(
        default=85, ge=1, le=100, description="Quality for JPG export (1-100)"
    )
    scale: Optional[float] = Field(
        default=1.0, ge=0.1, le=5.0, description="Scale factor for export"
    )
    page_size: Optional[str] = Field(
        default="A4",
        description="PDF page size (A0, A1, A2, A3, A4, A5, A6, Letter, Legal, Tabloid, Ledger)",
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate export format."""
        v = v.lower()
        if v not in ["png", "jpg", "jpeg", "svg", "pdf", "json"]:
            raise ValueError("format must be 'png', 'jpg', 'svg', 'pdf', or 'json'")
        # Normalize jpeg to jpg
        if v == "jpeg":
            v = "jpg"
        return v

    @field_validator("background_color")
    @classmethod
    def validate_background_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate background color is a valid hex color."""
        if v is not None:
            v = v.strip()
            if not v.startswith("#"):
                v = f"#{v}"
            # Basic hex color validation
            if len(v) not in [4, 7, 9]:  # #RGB, #RRGGBB, #RRGGBBAA
                raise ValueError(
                    "background_color must be a valid hex color (e.g., #ffffff)"
                )
            try:
                int(v[1:], 16)
            except ValueError:
                raise ValueError(
                    "background_color must be a valid hex color (e.g., #ffffff)"
                )
        return v

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: Optional[str]) -> str:
        """Validate PDF page size."""
        if v is None:
            return "A4"
        v = v.upper()
        valid_sizes = [
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "LETTER",
            "LEGAL",
            "TABLOID",
            "LEDGER",
        ]
        if v not in valid_sizes:
            raise ValueError(f"page_size must be one of: {', '.join(valid_sizes)}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "format": "png",
                    "width": 1920,
                    "height": 1080,
                    "include_background": True,
                    "background_color": "#ffffff",
                    "scale": 1.0,
                },
                {
                    "format": "jpg",
                    "width": 1920,
                    "height": 1080,
                    "quality": 90,
                },
                {
                    "format": "pdf",
                    "page_size": "A4",
                    "include_background": True,
                },
            ]
        }
    }


class ExportPngRequest(BaseModel):
    """Schema for PNG export query parameters."""

    width: Optional[int] = Field(
        default=800, ge=100, le=8000, description="Export width in pixels"
    )
    height: Optional[int] = Field(
        default=600, ge=100, le=8000, description="Export height in pixels"
    )
    quality: Optional[int] = Field(
        default=95, ge=1, le=100, description="Quality for PNG export (1-100)"
    )
    include_background: Optional[bool] = Field(
        default=True, description="Include background"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "width": 1920,
                    "height": 1080,
                    "quality": 95,
                    "include_background": True,
                }
            ]
        }
    }


class ExportPdfRequest(BaseModel):
    """Schema for PDF export query parameters."""

    page_size: Optional[str] = Field(
        default="A4",
        description="PDF page size (A0, A1, A2, A3, A4, A5, A6, Letter, Legal, Tabloid, Ledger)",
    )
    include_background: Optional[bool] = Field(
        default=True, description="Include background"
    )

    @field_validator("page_size")
    @classmethod
    def validate_page_size(cls, v: Optional[str]) -> str:
        """Validate PDF page size."""
        if v is None:
            return "A4"
        v = v.upper()
        valid_sizes = [
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "LETTER",
            "LEGAL",
            "TABLOID",
            "LEDGER",
        ]
        if v not in valid_sizes:
            raise ValueError(f"page_size must be one of: {', '.join(valid_sizes)}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_size": "A4",
                    "include_background": True,
                }
            ]
        }
    }


class ExportJobIdRequest(BaseModel):
    """Schema for export job ID validation."""

    job_id: str = Field(..., min_length=1, max_length=255, description="Celery task ID")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "abc123def456-789-xyz",
                }
            ]
        }
    }
