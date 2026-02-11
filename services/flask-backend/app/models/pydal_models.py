"""PyDAL table definitions for IceCharts application."""

import datetime

from pydal import Field
from pydal.validators import IS_EMAIL, IS_IN_SET, IS_NOT_EMPTY, IS_URL


def define_all_tables(db):
    """
    Define all database tables using PyDAL for IceCharts.

    Tables are defined in dependency order to satisfy foreign key references.

    IceCharts Tables (27 total):
    Core Tables:
    1. tenants - Multi-tenant organizations
    2. identities - User accounts (updated: email_verified fields)
    3. groups - User groups for access control
    4. group_memberships - Links users to groups
    5. drawings - Drawing documents
    6. drawing_versions - Version history for drawings
    7. storage_providers - Cloud storage configuration
    8. shapes - Individual diagram shapes
    9. connectors - Lines connecting shapes
    10. shape_metadata - Additional shape properties
    11. comments - Drawing annotations
    12. drawing_shares - Sharing permissions
    13. collaboration_sessions - Real-time collaboration (updated: cursor tracking, permissions)
    14. idp_configurations - Identity provider (SSO) settings

    Additional Tables:
    15. group_members - Group membership with roles
    16. comment_replies - Replies to comments
    17. shape_libraries - Custom shape libraries
    18. library_shapes - Shapes in libraries

    v0.2.0 Tables (Collections, Email, Analytics):
    19. collections - Drawing collections/albums
    20. collection_items - Drawings in collections
    21. collection_shares - Collection sharing permissions
    22. email_verifications - Email verification tracking
    23. system_settings - System-wide configuration
    24. share_analytics - Access tracking for shares

    IceRuns Tables (v1.4.0 - Serverless Function Platform):
    25. iceruns - Function definitions and configurations
    26. iceruns_executions - Execution history and results
    27. iceruns_schedules - Cron scheduling for functions
    28. iceruns_versions - Function versioning and rollback support

    IceFlows Tables (v1.5.0 - CI/CD Pipeline Orchestration):
    29. iceflows - Pipeline definitions
    30. iceflows_stages - Ordered branch stages
    31. iceflows_stage_approvers - Approval authority per stage
    32. iceflows_stage_tests - Test execution per stage
    33. iceflows_stage_calls - IceStreams/IceRuns triggers
    34. iceflows_stage_reviews - Darwin code review config
    35. iceflows_darwin_config - Darwin API settings per flow
    36. iceflows_promotions - Promotion requests between stages
    37. iceflows_approvals - Individual approval votes
    38. iceflows_executions - Pipeline execution runs
    39. iceflows_execution_steps - Individual step results
    40. iceflows_webhooks - Registered git webhooks
    41. iceflows_notifications - Notification channel configs
    42. iceflows_notification_log - Sent notification history

    IceStreams Approval Tables (v1.6.0 - Human Approval Gates):
    43. playbook_approval_gates - Approval gate node configurations
    44. playbook_execution_approvals - Approval decisions for paused executions
    """

    # ==========================================
    # LEVEL 0: Tenant table (foundation)
    # ==========================================

    db.define_table(
        "tenants",
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("slug", "string", length=100, notnull=True, unique=True),
        Field("tenant_domain", "string", length=255),
        Field(
            "subscription_tier",
            "string",
            length=50,
            default="community",
            requires=IS_IN_SET(["community", "professional", "enterprise"]),
        ),
        Field("license_key", "string", length=255),
        Field("settings", "json"),
        Field("feature_flags", "json"),
        Field("data_retention_days", "integer", default=90),
        Field("storage_quota_gb", "integer", default=10),
        Field("is_active", "boolean", default=True, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # LEVEL 1: Base tables
    # ==========================================

    db.define_table(
        "identities",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field(
            "username",
            "string",
            length=255,
            notnull=True,
            unique=True,
            requires=IS_NOT_EMPTY(),
        ),
        Field("email", "string", length=255, requires=IS_EMAIL()),
        Field("full_name", "string", length=255),
        Field("password_hash", "string", length=255),
        Field(
            "role",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["admin", "maintainer", "viewer"]),
        ),
        Field("is_active", "boolean", default=True, notnull=True),
        Field("is_superuser", "boolean", default=False, notnull=True),
        Field("mfa_enabled", "boolean", default=False, notnull=True),
        Field("mfa_secret", "string", length=255),
        Field("email_verified", "boolean", default=False, notnull=True),
        Field("email_verified_at", "datetime"),
        Field("last_login_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "groups",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("owner_id", "reference identities", ondelete="CASCADE"),
        Field("is_active", "boolean", default=True, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "idp_configurations",
        Field("tenant_id", "reference tenants", ondelete="CASCADE"),
        Field(
            "provider_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["saml", "oidc"]),
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("entity_id", "string", length=512),
        Field("metadata_url", "string", length=1024),
        Field("sso_url", "string", length=1024),
        Field("certificate", "text"),
        Field("oidc_client_id", "string", length=512),
        Field("oidc_client_secret", "string", length=512),
        Field("oidc_issuer_url", "string", length=1024),
        Field("attribute_mappings", "json"),
        Field("is_active", "boolean", default=True, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "storage_providers",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field(
            "provider_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(
                ["local", "s3", "gcs", "azure_blob", "minio", "gdrive", "onedrive"]
            ),
        ),
        Field("config_json", "json", notnull=True),
        Field("storage_config", "json"),  # Alias for API compatibility
        Field("user_id", "reference identities", ondelete="CASCADE"),
        Field("is_active", "boolean", default=True, notnull=True),
        Field("is_system_default", "boolean", default=False, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # LEVEL 2: Tables with Level 1 dependencies
    # ==========================================

    db.define_table(
        "group_memberships",
        Field("identity_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("group_id", "reference groups", notnull=True, ondelete="CASCADE"),
        Field("expires_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "drawings",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("title", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field("updated_by_id", "reference identities", ondelete="SET NULL"),
        Field("owner_id", "reference identities", ondelete="CASCADE"),
        Field("user_id", "reference identities", ondelete="CASCADE"),
        Field("is_public", "boolean", default=False, notnull=True),
        Field("is_template", "boolean", default=False, notnull=True),
        Field(
            "status",
            "string",
            length=50,
            default="draft",
            requires=IS_IN_SET(["draft", "published", "archived"]),
        ),
        Field("tags", "json"),  # Store as JSON array for PostgreSQL compatibility
        Field("thumbnail_url", "string", length=1024),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # LEVEL 3: Tables with Level 2 dependencies
    # ==========================================

    db.define_table(
        "drawing_versions",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("version_number", "integer", notnull=True),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field("content_json", "json", notnull=True),
        Field("change_summary", "text"),
        Field(
            "storage_provider_id",
            "reference storage_providers",
            ondelete="SET NULL",
        ),
        Field("storage_path", "string", length=1024),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "shapes",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("shape_id", "string", length=100, notnull=True),  # UUID
        Field(
            "shape_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(
                ["rectangle", "circle", "triangle", "text", "image", "custom"]
            ),
        ),
        Field("x", "double", notnull=True),
        Field("y", "double", notnull=True),
        Field("width", "double", notnull=True),
        Field("height", "double", notnull=True),
        Field("rotation", "double", default=0.0),
        Field("fill_color", "string", length=50),
        Field("stroke_color", "string", length=50),
        Field("stroke_width", "double", default=1.0),
        Field("text_content", "text"),
        Field("properties_json", "json"),
        Field("z_index", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "connectors",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("connector_id", "string", length=100, notnull=True),  # UUID
        Field("source_shape_id", "string", length=100, notnull=True),
        Field("target_shape_id", "string", length=100, notnull=True),
        Field(
            "connector_type",
            "string",
            length=50,
            default="line",
            requires=IS_IN_SET(["line", "arrow", "curved", "orthogonal"]),
        ),
        Field("stroke_color", "string", length=50),
        Field("stroke_width", "double", default=1.0),
        Field("properties_json", "json"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "shape_metadata",
        Field("shape_id", "string", length=100, notnull=True),
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("meta_key", "string", length=255, notnull=True),
        Field("meta_value", "text"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "comments",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("author_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("user_id", "reference identities", ondelete="CASCADE"),
        Field("comment_text", "text", notnull=True, requires=IS_NOT_EMPTY()),
        Field("x", "double"),  # Position on canvas
        Field("y", "double"),
        Field("x_position", "double"),  # Alias for API compatibility
        Field("y_position", "double"),  # Alias for API compatibility
        Field("shape_id", "string", length=100),  # Associated shape (optional)
        Field("is_resolved", "boolean", default=False, notnull=True),
        Field("resolved_by", "reference identities", ondelete="SET NULL"),
        Field("resolved_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "drawing_shares",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("shared_with_id", "reference identities", ondelete="CASCADE"),
        Field("shared_with_group_id", "reference groups", ondelete="CASCADE"),
        Field("user_id", "reference identities", ondelete="CASCADE"),
        Field("group_id", "reference groups", ondelete="CASCADE"),
        Field("shared_by", "reference identities", ondelete="SET NULL"),
        Field(
            "permission",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["viewer", "editor", "admin"]),
        ),
        Field("expires_at", "datetime"),
        Field("share_token", "string", length=255, unique=True),
        Field("is_public", "boolean", default=False, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    db.define_table(
        "collaboration_sessions",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("identity_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("session_id", "string", length=255, notnull=True),
        Field("socket_id", "string", length=255),
        Field("cursor_position_json", "json"),
        Field("last_cursor_x", "double"),
        Field("last_cursor_y", "double"),
        Field(
            "permission",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["viewer", "editor", "admin"]),
        ),
        Field("is_active", "boolean", default=True, notnull=True),
        Field(
            "joined_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field("left_at", "datetime"),
        Field("last_active_at", "datetime"),
        migrate=True,
    )

    # ==========================================
    # Additional tables for API compatibility
    # ==========================================

    # Group members table (similar to group_memberships but with role field)
    db.define_table(
        "group_members",
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("group_id", "reference groups", notnull=True, ondelete="CASCADE"),
        Field(
            "role",
            "string",
            length=50,
            default="member",
            requires=IS_IN_SET(["admin", "member"]),
        ),
        Field(
            "joined_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Comment replies table
    db.define_table(
        "comment_replies",
        Field("comment_id", "reference comments", notnull=True, ondelete="CASCADE"),
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("reply_text", "text", notnull=True, requires=IS_NOT_EMPTY()),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Shape libraries table
    db.define_table(
        "shape_libraries",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("owner_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("is_public", "boolean", default=False, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Library shapes table
    db.define_table(
        "library_shapes",
        Field(
            "library_id", "reference shape_libraries", notnull=True, ondelete="CASCADE"
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("shape_data", "json", notnull=True),
        Field("category", "string", length=100, default="custom"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # v0.2.0: Collections, Email Verification, and Analytics
    # ==========================================

    # Collections table for organizing drawings
    db.define_table(
        "collections",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("owner_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("thumbnail_url", "string", length=500),
        Field("is_public", "boolean", default=False, notnull=True),
        Field("share_token", "string", length=255, unique=True),
        Field(
            "share_mode",
            "string",
            length=50,
            default="private",
            requires=IS_IN_SET(["private", "link_only", "registered_users"]),
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Collection items (drawings in a collection)
    db.define_table(
        "collection_items",
        Field(
            "collection_id", "reference collections", notnull=True, ondelete="CASCADE"
        ),
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("added_by_id", "reference identities", notnull=True, ondelete="SET NULL"),
        Field("order_index", "integer", default=0),
        Field(
            "added_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Collection sharing (user/group level permissions)
    db.define_table(
        "collection_shares",
        Field(
            "collection_id", "reference collections", notnull=True, ondelete="CASCADE"
        ),
        Field("shared_with_id", "reference identities", ondelete="CASCADE"),
        Field("shared_with_group_id", "reference groups", ondelete="CASCADE"),
        Field(
            "permission",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["viewer", "editor", "admin"]),
        ),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="SET NULL"
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Email verification tracking
    db.define_table(
        "email_verifications",
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("email", "string", length=255, notnull=True),
        Field("verification_token", "string", length=255, unique=True, notnull=True),
        Field("expires_at", "datetime", notnull=True),
        Field("verified_at", "datetime"),
        Field("is_verified", "boolean", default=False, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # System-wide settings (configurable by admin)
    db.define_table(
        "system_settings",
        Field("setting_key", "string", length=255, unique=True, notnull=True),
        Field("setting_value", "text"),
        Field(
            "setting_type",
            "string",
            length=50,
            default="string",
            requires=IS_IN_SET(["string", "boolean", "integer", "json"]),
        ),
        Field("description", "text"),
        Field("updated_by_id", "reference identities", ondelete="SET NULL"),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Share analytics tracking
    db.define_table(
        "share_analytics",
        Field(
            "share_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["drawing", "collection"]),
        ),
        Field("share_id", "integer", notnull=True),  # drawing_id or collection_id
        Field("share_token", "string", length=255),
        Field("accessed_by_id", "reference identities", ondelete="SET NULL"),
        Field("access_ip", "string", length=50),
        Field("user_agent", "string", length=500),
        Field(
            "accessed_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
            notnull=True,
        ),
        migrate=True,
    )

    # Login events tracking for time series analytics
    db.define_table(
        "login_events",
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field(
            "login_type", "string", length=50, default="password"
        ),  # password, google, sso
        Field("ip_address", "string", length=50),
        Field("user_agent", "string", length=500),
        Field("country_code", "string", length=2),  # ISO 3166-1 alpha-2
        Field("country_name", "string", length=100),
        Field("city", "string", length=100),
        Field("success", "boolean", default=True, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
            notnull=True,
        ),
        migrate=True,
    )

    # ==========================================
    # Activity and Audit Logging (v1.0+)
    # ==========================================

    # Activity logs for tracking user actions (logins, drawing edits, sharing, etc.)
    db.define_table(
        "activity_logs",
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("tenant_id", "reference tenants", notnull=True, ondelete="CASCADE"),
        Field(
            "action",
            "string",
            length=100,
            notnull=True,
            requires=IS_NOT_EMPTY(),
        ),  # e.g., "login", "drawing_created", "drawing_shared", "comment_added"
        Field(
            "resource_type",
            "string",
            length=100,
        ),  # e.g., "drawing", "comment", "user", "group", "share"
        Field("resource_id", "integer"),  # ID of the resource being acted upon
        Field("resource_name", "string", length=255),  # Human-readable name of resource
        Field("details", "json"),  # Additional context-specific data
        Field("ip_address", "string", length=50),
        Field("user_agent", "string", length=500),
        Field(
            "timestamp",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
            notnull=True,
        ),
        migrate=True,
    )

    # Audit logs for tracking admin/sensitive actions with change history
    db.define_table(
        "audit_logs",
        Field(
            "user_id", "reference identities", ondelete="SET NULL"
        ),  # User who made the change
        Field("tenant_id", "reference tenants", notnull=True, ondelete="CASCADE"),
        Field(
            "action",
            "string",
            length=100,
            notnull=True,
            requires=IS_NOT_EMPTY(),
        ),  # e.g., "user_created", "user_updated", "user_deleted", "settings_changed"
        Field(
            "resource_type",
            "string",
            length=100,
            notnull=True,
        ),  # e.g., "user", "group", "settings", "system"
        Field("resource_id", "integer"),  # ID of the resource being modified
        Field("resource_name", "string", length=255),  # Human-readable name
        Field(
            "changes", "json"
        ),  # Detailed change data (old_value, new_value for each field)
        Field("reason", "text"),  # Why the action was taken
        Field("ip_address", "string", length=50),
        Field("user_agent", "string", length=500),
        Field("status", "string", length=50, default="success"),  # success, failed
        Field("error_message", "text"),  # If status is failed
        Field(
            "timestamp",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
            notnull=True,
        ),
        migrate=True,
    )

    # ==========================================
    # Templates Table
    # ==========================================

    # Templates for creating drawings from predefined layouts
    db.define_table(
        "templates",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "content", "json", notnull=True
        ),  # Template drawing content (nodes, edges, viewport)
        Field("category", "string", length=100, default="custom"),
        Field("thumbnail_url", "string", length=1024),
        Field("is_public", "boolean", default=False, notnull=True),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # Service Account Tables for External App Integration
    # ==========================================

    # Service accounts for machine-to-machine authentication
    db.define_table(
        "service_accounts",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "client_id",
            "string",
            length=50,
            notnull=True,
            unique=True,
        ),  # Format: sa_xxxxxxxxxxxx
        Field(
            "scopes", "json"
        ),  # Array of scope strings e.g., ["drawings:read", "exports:create"]
        Field("rate_limit", "integer", default=1000),  # Requests per hour
        Field("is_active", "boolean", default=True, notnull=True),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field("last_used_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Service account tokens (long-lived JWT tokens)
    db.define_table(
        "service_account_tokens",
        Field(
            "service_account_id",
            "reference service_accounts",
            notnull=True,
            ondelete="CASCADE",
        ),
        Field(
            "token_jti",
            "string",
            length=100,
            notnull=True,
            unique=True,
        ),  # JWT ID for revocation
        Field("name", "string", length=255),  # Optional label for the token
        Field("expires_at", "datetime", notnull=True),
        Field("last_used_at", "datetime"),
        Field("last_used_ip", "string", length=50),
        Field("revoked_at", "datetime"),
        Field("revoked_by_id", "reference identities", ondelete="SET NULL"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # Storage Migration Jobs (for async migration tracking)
    # ==========================================

    db.define_table(
        "migration_jobs",
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field(
            "source_provider_id",
            "reference storage_providers",
            notnull=True,
            ondelete="CASCADE",
        ),
        Field(
            "target_provider_id",
            "reference storage_providers",
            notnull=True,
            ondelete="CASCADE",
        ),
        Field(
            "status",
            "string",
            length=50,
            default="pending",
            requires=IS_IN_SET(
                [
                    "pending",
                    "in_progress",
                    "completed",
                    "completed_with_errors",
                    "failed",
                    "rolled_back",
                    "rollback_failed",
                ]
            ),
        ),
        Field("progress", "integer", default=0),  # 0-100
        Field("total_count", "integer", default=0),  # Total drawings to migrate
        Field("migrated_count", "integer", default=0),  # Successfully migrated
        Field("failed_count", "integer", default=0),  # Failed migrations
        Field("skipped_count", "integer", default=0),  # Skipped (no versions, etc.)
        Field("error_message", "text"),  # Error message if status is failed
        Field("celery_task_id", "string", length=255),  # Celery task ID for monitoring
        Field("result_json", "json"),  # Detailed results including failed drawings
        Field("status_json", "json"),  # Current status metadata
        Field(
            "started_at",
            "datetime",
        ),
        Field(
            "completed_at",
            "datetime",
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # IceStreams: Playbook Tables (Workflow Automation)
    # ==========================================

    # Main playbook/workflow definitions
    db.define_table(
        "playbooks",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field("updated_by_id", "reference identities", ondelete="SET NULL"),
        Field(
            "status",
            "string",
            length=50,
            default="draft",
            requires=IS_IN_SET(["draft", "active", "paused", "archived"]),
        ),
        Field("is_enabled", "boolean", default=False, notnull=True),
        Field("is_public", "boolean", default=False, notnull=True),
        Field("is_template", "boolean", default=False, notnull=True),
        Field(
            "trigger_type",
            "string",
            length=50,
        ),  # webhook, schedule, grpc, manual
        Field("trigger_config", "json"),  # Trigger-specific configuration
        Field("error_handling", "json"),  # Retry settings, failure notifications
        Field("tags", "json"),  # Array of tag strings
        Field("canvas_data", "json"),  # ReactFlow viewport, zoom, etc.
        Field("last_execution_at", "datetime"),
        Field("next_run_at", "datetime"),  # For scheduled playbooks
        Field("execution_count", "integer", default=0),
        Field("success_count", "integer", default=0),
        Field("failure_count", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook nodes (individual steps in the workflow)
    db.define_table(
        "playbook_nodes",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field(
            "node_id", "string", length=100, notnull=True
        ),  # ReactFlow node ID (UUID)
        Field(
            "node_type",
            "string",
            length=50,
            notnull=True,
        ),  # trigger_*, transform_*, action_*
        Field(
            "node_category",
            "string",
            length=50,
            default="transform",
            requires=IS_IN_SET(["trigger", "transform", "action"]),
        ),
        Field("label", "string", length=255),
        Field("position_x", "double", notnull=True),
        Field("position_y", "double", notnull=True),
        Field("config", "json", notnull=True),  # Node-specific configuration
        Field("data_schema", "json"),  # Expected input/output schema
        Field("is_enabled", "boolean", default=True, notnull=True),
        Field("execution_order", "integer", default=0),  # Computed execution order
        Field("comments", "text"),  # User comments on this node
        Field("metadata_json", "json"),  # Key/value metadata
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook edges (connections between nodes)
    db.define_table(
        "playbook_edges",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("edge_id", "string", length=100, notnull=True),  # ReactFlow edge ID
        Field("source_node_id", "string", length=100, notnull=True),
        Field("target_node_id", "string", length=100, notnull=True),
        Field("source_handle", "string", length=50),  # For nodes with multiple outputs
        Field("target_handle", "string", length=50),  # For nodes with multiple inputs
        Field("condition", "json"),  # Optional condition for conditional edges
        Field("label", "string", length=255),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook versions (for rollback capability)
    db.define_table(
        "playbook_versions",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("version_number", "integer", notnull=True),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field("nodes_json", "json", notnull=True),
        Field("edges_json", "json", notnull=True),
        Field("canvas_json", "json"),
        Field("change_summary", "text"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Webhook tokens for playbook triggers
    db.define_table(
        "playbook_webhooks",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("name", "string", length=255),
        Field("token", "string", length=255, unique=True, notnull=True),
        Field(
            "signature_secret", "string", length=255
        ),  # For HMAC signature validation
        Field("validate_signature", "boolean", default=False, notnull=True),
        Field("allowed_methods", "list:string"),  # Default: ['POST']
        Field("ip_whitelist", "list:string"),  # Optional IP restriction
        Field("is_active", "boolean", default=True, notnull=True),
        Field("is_enabled", "boolean", default=True, notnull=True),
        Field("last_triggered_at", "datetime"),
        Field("trigger_count", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook executions (individual runs)
    db.define_table(
        "playbook_executions",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("execution_id", "string", length=100, unique=True, notnull=True),  # UUID
        Field(
            "status",
            "string",
            length=50,
            default="pending",
            requires=IS_IN_SET(
                [
                    "pending",
                    "running",
                    "paused_for_approval",
                    "completed",
                    "failed",
                    "cancelled",
                    "timeout",
                    "partial_success",
                ]
            ),
        ),
        Field("trigger_type", "string", length=50),  # webhook, schedule, manual, api
        Field("triggered_by", "string", length=50),  # webhook, schedule, manual, api
        Field(
            "triggered_by_id", "reference identities", ondelete="SET NULL"
        ),  # If manual
        Field("input_json", "json"),  # Initial trigger payload
        Field("output_json", "json"),  # Final output after completion
        Field("error_message", "text"),
        Field("error_details", "json"),  # Stack trace, node that failed
        Field("retry_count", "integer", default=0),
        Field("parent_execution_id", "string", length=100),  # For retry chains
        Field("worker_id", "string", length=100),  # Which worker processed this
        Field("started_at", "datetime"),
        Field("completed_at", "datetime"),
        Field("duration_ms", "integer"),  # Execution time in milliseconds
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Node execution logs (per-node execution details)
    db.define_table(
        "playbook_node_executions",
        Field(
            "execution_id", "string", length=100, notnull=True
        ),  # FK to playbook_executions
        Field("node_id", "string", length=100, notnull=True),
        Field("node_type", "string", length=50),
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field(
            "status",
            "string",
            length=50,
            default="pending",
            requires=IS_IN_SET(
                ["pending", "running", "completed", "failed", "skipped"]
            ),
        ),
        Field("input_json", "json"),
        Field("output_json", "json"),
        Field("error_message", "text"),
        Field("error_details", "json"),
        Field("started_at", "datetime"),
        Field("completed_at", "datetime"),
        Field("duration_ms", "integer"),
        Field("retry_count", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook schedules (cron-like scheduling)
    db.define_table(
        "playbook_schedules",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field(
            "cron_expression", "string", length=100, notnull=True
        ),  # e.g., "0 9 * * 1-5"
        Field("timezone", "string", length=100, default="UTC"),
        Field("is_active", "boolean", default=True, notnull=True),
        Field("next_run_at", "datetime"),
        Field("last_run_at", "datetime"),
        Field("run_count", "integer", default=0),
        Field("static_input", "json"),  # Optional static payload for scheduled runs
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook sharing (similar to drawing_shares pattern)
    db.define_table(
        "playbook_shares",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("identity_id", "reference identities", ondelete="CASCADE"),
        Field("shared_with_id", "reference identities", ondelete="CASCADE"),
        Field("shared_with_group_id", "reference groups", ondelete="CASCADE"),
        Field("shared_by", "reference identities", ondelete="SET NULL"),
        Field(
            "permission",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["viewer", "editor"]),
        ),
        Field("expires_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook editor locks (only 1 editor at a time)
    db.define_table(
        "playbook_editor_locks",
        Field(
            "playbook_id",
            "reference playbooks",
            unique=True,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("locked_by_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("locked_by_name", "string", length=255),
        Field("locked_at", "datetime", notnull=True),
        Field("expires_at", "datetime", notnull=True),  # Auto-release after timeout
        Field(
            "socket_id", "string", length=255
        ),  # WebSocket session for real-time release
        migrate=True,
    )

    # Playbook templates (reusable workflow templates)
    db.define_table(
        "playbook_templates",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("category", "string", length=100, default="custom"),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field("nodes_json", "json", notnull=True),
        Field("edges_json", "json", notnull=True),
        Field("canvas_data", "json"),
        Field("is_public", "boolean", default=False, notnull=True),
        Field("usage_count", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Dynamic forms for playbooks
    db.define_table(
        "playbook_forms",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("fields_json", "json", notnull=True),  # Form field definitions
        Field("form_token", "string", length=255, unique=True),  # Public access token
        Field(
            "access_type",
            "string",
            length=50,
            default="registered",
            requires=IS_IN_SET(["public", "registered", "specific"]),
        ),
        Field("allowed_users", "list:reference identities"),  # For 'specific' access
        Field("is_active", "boolean", default=True, notnull=True),
        Field("submission_count", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Form submissions
    db.define_table(
        "playbook_form_submissions",
        Field("form_id", "reference playbook_forms", notnull=True, ondelete="CASCADE"),
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("submitted_by_id", "reference identities", ondelete="SET NULL"),
        Field("submission_data", "json", notnull=True),
        Field("ip_address", "string", length=50),
        Field("user_agent", "string", length=500),
        Field("execution_id", "string", length=100),  # If it triggered an execution
        Field(
            "submitted_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
            notnull=True,
        ),
        migrate=True,
    )

    # Custom modules (uploadable trigger/action modules)
    db.define_table(
        "custom_modules",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field(
            "name",
            "string",
            length=255,
            notnull=True,
            unique=True,
            requires=IS_NOT_EMPTY(),
        ),
        Field("display_name", "string", length=255),
        Field("description", "text"),
        Field(
            "module_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["trigger", "action"]),
        ),
        Field("version", "string", length=50, default="1.0.0"),
        Field("code_blob", "blob"),  # Python module file
        Field("config_schema", "json"),  # JSON Schema for configuration
        Field("input_schema", "json"),  # Expected input data schema
        Field("output_schema", "json"),  # Expected output data schema
        Field("is_validated", "boolean", default=False, notnull=True),
        Field("validation_errors", "json"),  # Errors from validation
        Field("is_enabled", "boolean", default=True, notnull=True),
        Field("uploaded_by_id", "reference identities", ondelete="SET NULL"),
        Field("usage_count", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook node metadata (comments and key/value for playbook nodes)
    db.define_table(
        "playbook_node_metadata",
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("node_id", "string", length=100, notnull=True),
        Field("comments", "text"),
        Field("metadata_json", "json"),
        Field("updated_by_id", "reference identities", ondelete="SET NULL"),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Diagram node metadata (comments and key/value for Charts)
    db.define_table(
        "diagram_node_metadata",
        Field("drawing_id", "reference drawings", notnull=True, ondelete="CASCADE"),
        Field("node_id", "string", length=100, notnull=True),
        Field("comments", "text"),
        Field("metadata_json", "json"),  # Key/value pairs
        Field("updated_by_id", "reference identities", ondelete="SET NULL"),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # IceRuns: Serverless Function Platform Tables (v1.4.0)
    # ==========================================

    # IceRuns function definitions
    db.define_table(
        "iceruns",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("function_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "runtime",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(
                [
                    "python3.13",
                    "nodejs",
                    "go",
                    "ruby",
                    "bash",
                    "powershell",
                    "rust",
                ]
            ),
        ),
        Field("entrypoint", "string", length=500),  # main.py|index.js|main.go|etc
        Field("handler", "string", length=255),  # Function name to invoke
        Field("package_key", "string", length=1024),  # S3 key: iceruns/{id}/package.zip
        Field("package_size", "integer"),  # Bytes
        Field("package_hash", "string", length=64),  # SHA256 for integrity
        Field("env_vars", "json"),  # Environment variables (encrypted)
        Field("secrets", "json"),  # Encrypted secrets
        Field("memory_limit_mb", "integer", default=128),  # 128-4096 MB
        Field("timeout_seconds", "integer", default=60),  # 1-900 seconds
        Field("cpu_limit", "double", default=0.5),  # 0.1-4.0 CPUs
        Field(
            "status",
            "string",
            length=50,
            default="draft",
            requires=IS_IN_SET(["draft", "active", "paused", "archived"]),
        ),
        Field("is_public", "boolean", default=False),
        Field("webhook_token", "string", length=64, unique=True),  # Bearer token
        Field("webhook_secret", "string", length=128),  # HMAC signature secret
        Field("validate_signature", "boolean", default=False),
        Field("allowed_methods", "list:string"),  # GET, POST, PUT, etc.
        Field("ip_whitelist", "list:string"),  # CIDR blocks
        Field("rate_limit", "integer", default=100),  # Requests per hour
        Field("tags", "list:string"),
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field("last_executed_at", "datetime"),
        Field("execution_count", "integer", default=0),
        migrate=True,
    )

    # IceRuns execution history
    db.define_table(
        "iceruns_executions",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("execution_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field("function_id", "reference iceruns", notnull=True, ondelete="CASCADE"),
        Field(
            "status",
            "string",
            length=50,
            requires=IS_IN_SET(
                ["queued", "running", "completed", "failed", "timeout", "cancelled"]
            ),
        ),
        Field(
            "trigger_type",
            "string",
            length=50,
            requires=IS_IN_SET(["webhook", "api", "schedule", "manual"]),
        ),
        Field("triggered_by", "string", length=255),  # User ID, service account, or IP
        Field("input_json", "json"),  # Request payload
        Field("output_json", "json"),  # Response data
        Field("stdout", "text"),  # Captured stdout
        Field("stderr", "text"),  # Captured stderr
        Field("exit_code", "integer"),
        Field("error_message", "text"),
        Field("error_details", "json"),
        Field("worker_id", "string", length=255),  # Which worker processed it
        Field("container_id", "string", length=255),  # Docker container ID
        Field("started_at", "datetime"),
        Field("completed_at", "datetime"),
        Field("duration_ms", "integer"),
        Field("memory_used_mb", "integer"),  # Peak memory usage
        Field("cpu_time_ms", "integer"),  # CPU time consumed
        Field("retry_count", "integer", default=0),
        Field("parent_execution_id", "string", length=36),  # For retries
        Field("webhook_headers", "json"),  # For debugging
        Field("webhook_ip", "string", length=45),  # IPv4/IPv6
        Field("logs_key", "string", length=1024),  # S3 key for full logs
        Field("artifacts_key", "string", length=1024),  # S3 key for output files
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceRuns cron scheduling
    db.define_table(
        "iceruns_schedules",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("schedule_id", "string", length=36, unique=True, notnull=True),
        Field("function_id", "reference iceruns", notnull=True, ondelete="CASCADE"),
        Field("cron_expression", "string", length=255, notnull=True),
        Field("timezone", "string", length=100, default="UTC"),
        Field("is_active", "boolean", default=True),
        Field("next_run_at", "datetime"),
        Field("last_run_at", "datetime"),
        Field("run_count", "integer", default=0),
        Field("static_input", "json"),  # Payload for scheduled runs
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceRuns function versioning
    db.define_table(
        "iceruns_versions",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("version_id", "string", length=36, unique=True, notnull=True),
        Field("function_id", "reference iceruns", notnull=True, ondelete="CASCADE"),
        Field("version_number", "integer", notnull=True),
        Field("package_key", "string", length=1024),
        Field("package_hash", "string", length=64),
        Field("entrypoint", "string", length=500),
        Field("handler", "string", length=255),
        Field("env_vars", "json"),
        Field("change_summary", "text"),
        Field("is_active", "boolean", default=False),  # Current version flag
        Field(
            "created_by_id", "reference identities", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # IceStreams/Playbook Approval Gates (v1.6.0 - Human Approval System)
    # ==========================================

    # Playbook approval gates (human approval nodes in workflows)
    db.define_table(
        "playbook_approval_gates",
        Field("gate_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field("playbook_id", "reference playbooks", notnull=True, ondelete="CASCADE"),
        Field("node_id", "string", length=255, notnull=True),  # ReactFlow node ID
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("require_approval", "boolean", default=True, notnull=True),
        Field("min_approvers", "integer", default=1),  # Minimum approvals required
        Field("approvers", "list:reference identities"),  # List of user IDs who can approve
        Field("approver_groups", "list:reference groups"),  # List of group IDs
        Field("timeout_minutes", "integer"),  # Auto-reject after timeout (optional)
        Field("is_enabled", "boolean", default=True, notnull=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Playbook execution approvals (individual approval decisions)
    db.define_table(
        "playbook_execution_approvals",
        Field("approval_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "execution_id",
            "string",
            length=100,
            notnull=True,
        ),  # FK to playbook_executions.execution_id
        Field(
            "gate_id",
            "reference playbook_approval_gates",
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("approver_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field(
            "decision",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["approve", "reject"]),
        ),
        Field("comment", "text"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
            notnull=True,
        ),
        migrate=True,
    )

    # ==========================================
    # IceRuns Indexes for Performance Optimization
    # ==========================================
    # Note: Indexes are created via safe_create_index helper which uses
    # raw SQL with IF NOT EXISTS to handle idempotent index creation.
    # PyDAL automatically creates indexes for reference fields and unique fields.
    # Additional performance indexes are optional and created below.

    # ==========================================
    # IceFlows: CI/CD Pipeline Orchestration (Phase 1)
    # ==========================================

    # Main IceFlows pipeline definitions
    db.define_table(
        "iceflows",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("flow_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "repository_url", "string", length=1024, notnull=True, requires=IS_NOT_EMPTY()
        ),
        Field(
            "repository_provider",
            "string",
            length=50,
            requires=IS_IN_SET(["github", "gitlab"]),
        ),
        Field("repository_name", "string", length=255),
        Field("default_branch", "string", length=255, default="main"),
        Field(
            "credential_id",
            "reference iceflows_credentials",
            ondelete="SET NULL",
        ),  # Git provider access token
        Field("gitops_enabled", "boolean", default=False),
        Field("gitops_repo_url", "string", length=1024),
        Field("gitops_branch", "string", length=255, default="main"),
        Field("gitops_path", "string", length=1024),
        Field("webhook_secret", "string", length=128),
        Field(
            "status",
            "string",
            length=50,
            default="draft",
            requires=IS_IN_SET(["draft", "active", "paused", "archived"]),
        ),
        Field("is_enabled", "boolean", default=True),
        Field("created_by_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("tags", "list:string"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows credentials (secure Git provider tokens)
    db.define_table(
        "iceflows_credentials",
        Field(
            "tenant_id",
            "reference tenants",
            default=1,
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("credential_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field(
            "provider",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["github", "gitlab"]),
        ),
        Field("access_token", "password", length=512, notnull=True),  # Encrypted
        Field("token_type", "string", length=50, default="personal"),  # personal, oauth, app
        Field("scopes", "list:string"),  # Token permissions/scopes
        Field("expires_at", "datetime"),  # Token expiration (optional)
        Field("is_active", "boolean", default=True),
        Field("created_by_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("last_used_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows stages (ordered branch stages)
    db.define_table(
        "iceflows_stages",
        Field("stage_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field("stage_order", "integer", notnull=True),
        Field("branch_name", "string", length=255, notnull=True),
        Field("display_name", "string", length=255),
        Field("description", "text"),
        Field("is_production", "boolean", default=False),
        Field("auto_promote", "boolean", default=False),
        Field("require_approval", "boolean", default=True),
        Field("min_approvers", "integer", default=1),
        Field("override_min_approvers", "integer", default=2),
        Field("day_restrictions", "json"),  # {"blocked_days": [5, 6, 0]}
        Field("time_restrictions", "json"),  # {"start_hour": 9, "end_hour": 17, ...}
        Field("notification_config", "json"),
        Field("is_enabled", "boolean", default=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows stage approvers (users/groups who can approve promotions)
    db.define_table(
        "iceflows_stage_approvers",
        Field("approver_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "stage_id", "reference iceflows_stages", notnull=True, ondelete="CASCADE"
        ),
        Field("identity_id", "reference identities", ondelete="CASCADE"),
        Field("group_id", "reference groups", ondelete="CASCADE"),
        Field(
            "role",
            "string",
            length=50,
            default="approver",
            requires=IS_IN_SET(["approver", "admin", "reviewer"]),
        ),
        Field("can_override", "boolean", default=False),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows stage tests (unit, integration, e2e, custom tests)
    db.define_table(
        "iceflows_stage_tests",
        Field("test_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "stage_id", "reference iceflows_stages", notnull=True, ondelete="CASCADE"
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field(
            "test_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["unit", "integration", "e2e", "custom"]),
        ),
        Field(
            "path_mode",
            "string",
            length=50,
            default="repo_relative",
            requires=IS_IN_SET(["centralized", "repo_relative"]),
        ),
        Field("centralized_path", "string", length=1024),
        Field("repo_relative_path", "string", length=1024),
        Field("command", "string", length=1024),
        Field("timeout_seconds", "integer", default=600),
        Field("is_blocking", "boolean", default=True),
        Field("is_required", "boolean", default=True),
        Field("execution_order", "integer", default=0),
        Field("env_vars", "json"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows stage calls (IceStreams/IceRuns triggers)
    db.define_table(
        "iceflows_stage_calls",
        Field("call_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "stage_id", "reference iceflows_stages", notnull=True, ondelete="CASCADE"
        ),
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field(
            "call_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["icestreams", "iceruns"]),
        ),
        Field("target_id", "string", length=36),
        Field(
            "trigger_on",
            "string",
            length=50,
            requires=IS_IN_SET(
                ["pre_merge", "post_merge", "on_approval", "on_promotion"]
            ),
        ),
        Field("input_template", "json"),
        Field("timeout_seconds", "integer", default=300),
        Field("is_blocking", "boolean", default=True),
        Field("retry_count", "integer", default=0),
        Field("execution_order", "integer", default=0),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows stage reviews (Darwin code review requirements)
    db.define_table(
        "iceflows_stage_reviews",
        Field("review_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "stage_id", "reference iceflows_stages", notnull=True, ondelete="CASCADE"
        ),
        Field("is_required", "boolean", default=True),
        Field(
            "review_type",
            "string",
            default="inherit",
            requires=IS_IN_SET(
                ["inherit", "standard", "security", "performance", "full"]
            ),
        ),
        Field("min_score", "integer", default=70),
        Field("block_on_critical", "boolean", default=True),
        Field("allowed_issue_types", "list:string"),
        Field("reviewers_notified", "boolean", default=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows Darwin API configuration per flow
    db.define_table(
        "iceflows_darwin_config",
        Field("config_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field("darwin_api_url", "string", length=1024),
        Field("darwin_api_key", "password"),
        Field("default_review_type", "string", default="standard"),
        Field("auto_approve_threshold", "integer", default=0),
        Field("block_on_critical", "boolean", default=True),
        Field("is_enabled", "boolean", default=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows promotion requests (between stages)
    db.define_table(
        "iceflows_promotions",
        Field("promotion_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "source_stage_id", "reference iceflows_stages", notnull=True
        ),
        Field(
            "target_stage_id", "reference iceflows_stages", notnull=True
        ),
        Field("source_branch", "string", length=255, notnull=True),
        Field("target_branch", "string", length=255, notnull=True),
        Field("source_commit", "string", length=40),
        Field("target_commit", "string", length=40),
        Field(
            "status",
            "string",
            length=50,
            default="pending",
            requires=IS_IN_SET(
                ["pending", "approved", "rejected", "merged", "failed"]
            ),
        ),
        Field("requested_by_id", "reference identities", ondelete="SET NULL"),
        Field("git_pr_url", "string", length=1024),
        Field("git_pr_number", "integer"),
        Field("override_reason", "text"),
        Field("override_by_id", "reference identities", ondelete="SET NULL"),
        Field("merged_by_id", "reference identities", ondelete="SET NULL"),
        Field("merged_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field(
            "updated_at",
            "datetime",
            update=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows individual approval votes
    db.define_table(
        "iceflows_approvals",
        Field("approval_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "promotion_id",
            "reference iceflows_promotions",
            notnull=True,
            ondelete="CASCADE",
        ),
        Field("approver_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field(
            "decision",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["approve", "reject", "request_changes"]),
        ),
        Field("comment", "text"),
        Field("is_override", "boolean", default=False),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows execution runs
    db.define_table(
        "iceflows_executions",
        Field("execution_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field("promotion_id", "reference iceflows_promotions", ondelete="CASCADE"),
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "stage_id", "reference iceflows_stages", notnull=True
        ),
        Field(
            "trigger_type",
            "string",
            length=50,
            requires=IS_IN_SET(
                ["git_push", "promotion", "manual", "webhook"]
            ),
        ),
        Field("git_event_type", "string", length=50),
        Field("git_ref", "string", length=255),
        Field("git_commit", "string", length=40),
        Field("git_commit_message", "text"),
        Field("git_author", "string", length=255),
        Field(
            "status",
            "string",
            length=50,
            default="pending",
            requires=IS_IN_SET(
                ["pending", "running", "completed", "failed", "cancelled"]
            ),
        ),
        Field("started_at", "datetime"),
        Field("completed_at", "datetime"),
        Field("duration_ms", "integer"),
        Field("error_message", "text"),
        Field("result_json", "json"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows execution steps (individual step results)
    db.define_table(
        "iceflows_execution_steps",
        Field("step_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "execution_id",
            "reference iceflows_executions",
            notnull=True,
            ondelete="CASCADE",
        ),
        Field(
            "step_type",
            "string",
            length=50,
            requires=IS_IN_SET(
                ["test", "call", "approval_check", "merge", "darwin_review"]
            ),
        ),
        Field("step_name", "string", length=255),
        Field("reference_id", "string", length=36),
        Field(
            "status",
            "string",
            length=50,
            default="pending",
            requires=IS_IN_SET(
                ["pending", "running", "completed", "failed", "skipped"]
            ),
        ),
        Field("input_json", "json"),
        Field("output_json", "json"),
        Field("logs", "text"),
        Field("logs_key", "string", length=1024),
        Field("started_at", "datetime"),
        Field("completed_at", "datetime"),
        Field("duration_ms", "integer"),
        Field("error_message", "text"),
        Field("retry_count", "integer", default=0),
        migrate=True,
    )

    # IceFlows registered git webhooks
    db.define_table(
        "iceflows_webhooks",
        Field("webhook_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "provider",
            "string",
            length=50,
            requires=IS_IN_SET(["github", "gitlab"]),
        ),
        Field("webhook_url", "string", length=1024),
        Field("webhook_secret", "string", length=128),
        Field("events", "list:string"),
        Field("is_active", "boolean", default=True),
        Field("last_received_at", "datetime"),
        Field("last_status", "string", length=50),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows notification channel configurations
    db.define_table(
        "iceflows_notifications",
        Field("notification_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field(
            "channel_type",
            "string",
            length=50,
            notnull=True,
            requires=IS_IN_SET(["email", "slack", "webhook"]),
        ),
        Field("name", "string", length=255),
        Field("config", "json"),
        Field("events", "list:string"),
        Field("is_enabled", "boolean", default=True),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # IceFlows sent notification history
    db.define_table(
        "iceflows_notification_log",
        Field("log_id", "string", length=36, unique=True, notnull=True),  # UUID
        Field(
            "notification_id",
            "reference iceflows_notifications",
            ondelete="SET NULL",
        ),
        Field(
            "flow_id", "reference iceflows", notnull=True, ondelete="CASCADE"
        ),
        Field("event_type", "string", length=100),
        Field("channel_type", "string", length=50),
        Field("recipient", "string", length=500),
        Field("subject", "string", length=500),
        Field("body", "text"),
        Field(
            "status",
            "string",
            length=50,
            requires=IS_IN_SET(["sent", "failed", "pending"]),
        ),
        Field("error_message", "text"),
        Field("sent_at", "datetime"),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # ==========================================
    # IceFlows Indexes for Performance Optimization
    # ==========================================
    # Note: Indexes are automatically created by PyDAL for:
    # - Primary keys (id field)
    # - Foreign key references (reference fields)
    # - Unique fields (unique=True)
    # Additional performance indexes can be added via database migrations
    # or by using executesql with CREATE INDEX IF NOT EXISTS syntax.

    # ==========================================
    # Note: Default system settings initialization moved to get_db() function
    # to avoid transaction issues during table definition

    # Create alias for identities table as users
    db.users = db.identities
