"""PyDAL table definitions for IceCharts application."""

import datetime

from pydal import Field
from pydal.validators import IS_EMAIL, IS_IN_SET, IS_NOT_EMPTY, IS_URL


def define_all_tables(db):
    """
    Define all database tables using PyDAL for IceCharts.

    Tables are defined in dependency order to satisfy foreign key references.

    IceCharts Tables (14 total):
    1. tenants - Multi-tenant organizations
    2. identities - User accounts
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
    13. collaboration_sessions - Real-time collaboration
    14. idp_configurations - Identity provider (SSO) settings
    """

    # ==========================================
    # LEVEL 0: Tenant table (foundation)
    # ==========================================

    db.define_table(
        "tenants",
        Field("name", "string", length=255, notnull=True, requires=IS_NOT_EMPTY()),
        Field("slug", "string", length=100, notnull=True, unique=True),
        Field("domain", "string", length=255),
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
            "idp_type",
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
            requires=IS_IN_SET(["local", "s3", "gcs", "azure_blob"]),
        ),
        Field("config_json", "json", notnull=True),
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
        Field("key", "string", length=255, notnull=True),
        Field("value", "text"),
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
        Field("content", "text", notnull=True, requires=IS_NOT_EMPTY()),
        Field("x", "double"),  # Position on canvas
        Field("y", "double"),
        Field("shape_id", "string", length=100"),  # Associated shape (optional)
        Field("is_resolved", "boolean", default=False, notnull=True),
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
        Field(
            "permission",
            "string",
            length=50,
            default="viewer",
            requires=IS_IN_SET(["viewer", "editor", "admin"]),
        ),
        Field("expires_at", "datetime"),
        Field("share_token", "string", length=255, unique=True),
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
        Field("is_active", "boolean", default=True, notnull=True),
        Field(
            "joined_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        Field("left_at", "datetime"),
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

    # Add owner_id field to groups table
    db.groups._extra_fields.append(Field("owner_id", "reference identities", ondelete="CASCADE"))

    # Add owner_id and user_id fields to drawings table for API compatibility
    db.drawings._extra_fields.append(Field("owner_id", "reference identities", ondelete="CASCADE"))
    db.drawings._extra_fields.append(Field("user_id", "reference identities", ondelete="CASCADE"))

    # Update comments table to add user_id, x_position, y_position fields and other missing fields
    db.comments._extra_fields.append(Field("user_id", "reference identities", ondelete="CASCADE"))
    db.comments._extra_fields.append(Field("x_position", "double"))
    db.comments._extra_fields.append(Field("y_position", "double"))
    db.comments._extra_fields.append(Field("resolved_by", "reference identities", ondelete="SET NULL"))
    db.comments._extra_fields.append(Field("resolved_at", "datetime"))

    # Add comment_replies table
    db.define_table(
        "comment_replies",
        Field("comment_id", "reference comments", notnull=True, ondelete="CASCADE"),
        Field("user_id", "reference identities", notnull=True, ondelete="CASCADE"),
        Field("content", "text", notnull=True, requires=IS_NOT_EMPTY()),
        Field(
            "created_at",
            "datetime",
            default=lambda: datetime.datetime.now(datetime.timezone.utc),
        ),
        migrate=True,
    )

    # Update drawing_shares table for API compatibility
    db.drawing_shares._extra_fields.append(Field("user_id", "reference identities", ondelete="CASCADE"))
    db.drawing_shares._extra_fields.append(Field("group_id", "reference groups", ondelete="CASCADE"))
    db.drawing_shares._extra_fields.append(Field("is_public", "boolean", default=False, notnull=True))
    db.drawing_shares._extra_fields.append(Field("shared_by", "reference identities", ondelete="SET NULL"))

    # Update storage_providers table for API compatibility
    db.storage_providers._extra_fields.append(Field("user_id", "reference identities", ondelete="CASCADE"))
    db.storage_providers._extra_fields.append(Field("config", "json"))
    db.storage_providers._extra_fields.append(Field("is_system_default", "boolean", default=False, notnull=True"))

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

    # Create alias for identities table as users
    db.users = db.identities
