"""PyDAL table definitions for IceCharts application."""

import datetime

from pydal import Field
from pydal.validators import IS_EMAIL, IS_IN_SET, IS_NOT_EMPTY, IS_URL


def define_all_tables(db):
    """
    Define all database tables using PyDAL for IceCharts.

    Tables are defined in dependency order to satisfy foreign key references.

    IceCharts Tables (23 total):
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
            requires=IS_IN_SET(["local", "s3", "gcs", "azure_blob", "minio", "gdrive", "onedrive"]),
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
        Field("created_by_id", "reference identities", notnull=True, ondelete="CASCADE"),
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
        Field("tags", "list:string"),
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
        Field("created_by_id", "reference identities", notnull=True, ondelete="CASCADE"),
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
        Field("joined_at", "datetime", default=lambda: datetime.datetime.now(datetime.timezone.utc)),
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
        Field("library_id", "reference shape_libraries", notnull=True, ondelete="CASCADE"),
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
        Field("collection_id", "reference collections", notnull=True, ondelete="CASCADE"),
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
        Field("collection_id", "reference collections", notnull=True, ondelete="CASCADE"),
        Field("shared_with_id", "reference identities", ondelete="CASCADE"),
        Field("shared_with_group_id", "reference groups", ondelete="CASCADE"),
        Field(
            "permission",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["viewer", "editor", "admin"]),
        ),
        Field("created_by_id", "reference identities", notnull=True, ondelete="SET NULL"),
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
        Field("login_type", "string", length=50, default="password"),  # password, google, sso
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
        Field("user_id", "reference identities", ondelete="SET NULL"),  # User who made the change
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
        Field("changes", "json"),  # Detailed change data (old_value, new_value for each field)
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
        Field("content", "json", notnull=True),  # Template drawing content (nodes, edges, viewport)
        Field("category", "string", length=100, default="custom"),
        Field("thumbnail_url", "string", length=1024),
        Field("is_public", "boolean", default=False, notnull=True),
        Field("created_by_id", "reference identities", notnull=True, ondelete="CASCADE"),
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
        Field("scopes", "json"),  # Array of scope strings e.g., ["drawings:read", "exports:create"]
        Field("rate_limit", "integer", default=1000),  # Requests per hour
        Field("is_active", "boolean", default=True, notnull=True),
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
                ["pending", "in_progress", "completed", "completed_with_errors", "failed", "rolled_back", "rollback_failed"]
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
    # Create indexes for performance
    # ==========================================
    # Note: PyDAL will create these indexes automatically after tables are created
    # Explicitly creating indexes here would cause errors if tables don't exist yet
    # The indexes will be created when the tables are first accessed

    # ==========================================
    # Note: Default system settings initialization moved to get_db() function
    # to avoid transaction issues during table definition

    # Create alias for identities table as users
    db.users = db.identities
