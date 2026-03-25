"""Playbook schemas for API validation - IceStreams workflow automation."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class CreatePlaybookRequest(BaseModel):
    """Schema for creating a new playbook (workflow)."""

    name: str = Field(
        ..., min_length=1, max_length=255, description="Playbook name/title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Playbook description"
    )
    canvas_data: Optional[Dict[str, Any]] = Field(
        None, description="Playbook canvas data (nodes, edges, etc.)"
    )
    trigger_type: Optional[str] = Field(
        default="manual",
        description="Trigger type: 'manual', 'webhook', 'schedule', 'grpc'",
    )
    visibility: Optional[str] = Field(
        default="private", description="Playbook visibility: 'private' or 'public'"
    )
    is_template: Optional[bool] = Field(
        default=False, description="Whether this playbook is a template"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="List of tags for the playbook"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean playbook name."""
        v = v.strip()
        if len(v) == 0:
            raise ValueError("Playbook name cannot be empty or whitespace only")
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

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, v: Optional[str]) -> str:
        """Validate trigger type."""
        if v is None:
            return "manual"
        v = v.lower()
        if v not in ["manual", "webhook", "schedule", "grpc"]:
            raise ValueError(
                "trigger_type must be 'manual', 'webhook', 'schedule', or 'grpc'"
            )
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

    @field_validator("canvas_data")
    @classmethod
    def validate_canvas_data(cls, v: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate canvas data structure."""
        if v is None:
            return {"nodes": [], "edges": []}
        if not isinstance(v, dict):
            raise ValueError("canvas_data must be a dictionary")
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
            cleaned = list(set([tag.strip() for tag in v if tag.strip()]))
            return cleaned if cleaned else None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "My Workflow",
                    "description": "Automated data processing pipeline",
                    "canvas_data": {"nodes": [], "edges": []},
                    "trigger_type": "webhook",
                    "visibility": "private",
                    "is_template": False,
                    "tags": ["automation", "etl"],
                }
            ]
        }
    }


class UpdatePlaybookRequest(BaseModel):
    """Schema for updating an existing playbook."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Playbook name/title"
    )
    description: Optional[str] = Field(
        None, max_length=2000, description="Playbook description"
    )
    canvas_data: Optional[Dict[str, Any]] = Field(
        None, description="Playbook canvas data (nodes, edges, etc.)"
    )
    trigger_type: Optional[str] = Field(
        None, description="Trigger type: 'manual', 'webhook', 'schedule', 'grpc'"
    )
    visibility: Optional[str] = Field(
        None, description="Playbook visibility: 'private' or 'public'"
    )
    is_template: Optional[bool] = Field(
        None, description="Whether this playbook is a template"
    )
    tags: Optional[List[str]] = Field(None, description="List of tags for the playbook")
    status: Optional[str] = Field(
        None,
        description="Playbook status (e.g., 'draft', 'active', 'paused', 'archived')",
    )
    is_enabled: Optional[bool] = Field(
        None, description="Whether the playbook is enabled for execution"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean playbook name."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError("Playbook name cannot be empty or whitespace only")
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

    @field_validator("trigger_type")
    @classmethod
    def validate_trigger_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate trigger type."""
        if v is not None:
            v = v.lower()
            if v not in ["manual", "webhook", "schedule", "grpc"]:
                raise ValueError(
                    "trigger_type must be 'manual', 'webhook', 'schedule', or 'grpc'"
                )
        return v

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: Optional[str]) -> Optional[str]:
        """Validate visibility."""
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
            if v not in ["draft", "active", "paused", "archived"]:
                raise ValueError(
                    "status must be 'draft', 'active', 'paused', or 'archived'"
                )
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and clean tags."""
        if v is not None:
            cleaned = list(set([tag.strip() for tag in v if tag.strip()]))
            return cleaned if cleaned else None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Updated Workflow",
                    "description": "Updated data processing pipeline",
                    "visibility": "public",
                    "status": "active",
                    "is_enabled": True,
                    "tags": ["automation", "etl", "production"],
                }
            ]
        }
    }


class ExecutePlaybookRequest(BaseModel):
    """Schema for manually executing a playbook."""

    input_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Input data to pass to the playbook"
    )
    dry_run: Optional[bool] = Field(
        default=False, description="If true, validate without executing"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "input_data": {"message": "Hello, world!"},
                    "dry_run": False,
                }
            ]
        }
    }


class PlaybookNodeMetadataRequest(BaseModel):
    """Schema for updating node metadata (comments, key/value pairs)."""

    comments: Optional[str] = Field(
        None, max_length=10000, description="Node comments/documentation"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Key/value metadata pairs"
    )

    @field_validator("comments")
    @classmethod
    def validate_comments(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean comments."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "comments": "This node transforms the incoming data...",
                    "metadata": {"author": "john", "version": "1.0"},
                }
            ]
        }
    }


class CreateScheduleRequest(BaseModel):
    """Schema for creating a playbook schedule."""

    cron_expression: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Cron expression (e.g., '0 * * * *')",
    )
    timezone: Optional[str] = Field(
        default="UTC", description="Timezone for the schedule"
    )
    is_enabled: Optional[bool] = Field(
        default=True, description="Whether the schedule is enabled"
    )
    input_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Default input data for scheduled executions"
    )

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Basic cron expression validation."""
        v = v.strip()
        parts = v.split()
        if len(parts) not in [5, 6]:
            raise ValueError("cron_expression must have 5 or 6 fields")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cron_expression": "0 * * * *",
                    "timezone": "America/New_York",
                    "is_enabled": True,
                }
            ]
        }
    }


class CreateWebhookRequest(BaseModel):
    """Schema for creating a playbook webhook."""

    name: Optional[str] = Field(
        None, max_length=255, description="Webhook name for reference"
    )
    allowed_methods: Optional[List[str]] = Field(
        default=["POST"], description="Allowed HTTP methods"
    )
    validate_signature: Optional[bool] = Field(
        default=False, description="Whether to validate HMAC signature"
    )
    signature_secret: Optional[str] = Field(
        None, max_length=255, description="HMAC secret for signature validation"
    )

    @field_validator("allowed_methods")
    @classmethod
    def validate_methods(cls, v: Optional[List[str]]) -> List[str]:
        """Validate HTTP methods."""
        if v is None:
            return ["POST"]
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        cleaned = [m.upper() for m in v]
        for m in cleaned:
            if m not in valid_methods:
                raise ValueError(f"Invalid HTTP method: {m}")
        return cleaned

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "GitHub Webhook",
                    "allowed_methods": ["POST"],
                    "validate_signature": True,
                    "signature_secret": "my-secret-key",
                }
            ]
        }
    }


class AcquireLockRequest(BaseModel):
    """Schema for acquiring an editor lock."""

    socket_id: Optional[str] = Field(
        None, max_length=255, description="WebSocket session ID for real-time release"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "socket_id": "abc123",
                }
            ]
        }
    }
