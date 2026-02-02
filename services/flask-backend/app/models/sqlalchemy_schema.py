"""SQLAlchemy schema definitions for table initialization.

This module is used ONLY for initializing database tables.
After initialization, PyDAL is used for all database operations.
"""

import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Tenant(Base):
    """Tenants table."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    tenant_domain = Column(String(255))
    subscription_tier = Column(String(50), default="community")
    license_key = Column(String(255))
    settings = Column(JSON)
    feature_flags = Column(JSON)
    data_retention_days = Column(Integer, default=90)
    storage_quota_gb = Column(Integer, default=10)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class Identity(Base):
    """Identities (users) table."""

    __tablename__ = "identities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255))
    full_name = Column(String(255))
    password_hash = Column(String(255))
    role = Column(String(50), default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255))
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class Group(Base):
    """Groups table."""

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class IdpConfiguration(Base):
    """IDP configurations table."""

    __tablename__ = "idp_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    provider_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    entity_id = Column(String(512))
    metadata_url = Column(String(1024))
    sso_url = Column(String(1024))
    certificate = Column(Text)
    oidc_client_id = Column(String(512))
    oidc_client_secret = Column(String(512))
    oidc_issuer_url = Column(String(1024))
    attribute_mappings = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class StorageProvider(Base):
    """Storage providers table."""

    __tablename__ = "storage_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=False)
    config_json = Column(JSON, nullable=False)
    storage_config = Column(JSON)
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class GroupMembership(Base):
    """Group memberships table."""

    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    identity_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Drawing(Base):
    """Drawings table."""

    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    updated_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    owner_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    is_public = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="draft")
    tags = Column(JSON)
    thumbnail_url = Column(String(1024))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class DrawingVersion(Base):
    """Drawing versions table."""

    __tablename__ = "drawing_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    content_json = Column(JSON, nullable=False)
    change_summary = Column(Text)
    storage_provider_id = Column(
        Integer, ForeignKey("storage_providers.id", ondelete="SET NULL")
    )
    storage_path = Column(String(1024))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Shape(Base):
    """Shapes table."""

    __tablename__ = "shapes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    shape_type = Column(String(50), nullable=False)
    x_position = Column(Integer)
    y_position = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    style_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class Connector(Base):
    """Connectors table."""

    __tablename__ = "connectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    start_shape_id = Column(Integer, ForeignKey("shapes.id", ondelete="CASCADE"))
    end_shape_id = Column(Integer, ForeignKey("shapes.id", ondelete="CASCADE"))
    connector_type = Column(String(50))
    style_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class ShapeMetadata(Base):
    """Shape metadata table."""

    __tablename__ = "shape_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shape_id = Column(
        Integer,
        ForeignKey("shapes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    label = Column(String(255))
    description = Column(Text)
    custom_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class Comment(Base):
    """Comments table."""

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    text_content = Column(Text, nullable=False)
    x_position = Column(Integer)
    y_position = Column(Integer)
    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class DrawingShare(Base):
    """Drawing shares table."""

    __tablename__ = "drawing_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    shared_with_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    shared_with_group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    shared_by = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    permission = Column(String(50), default="viewer")
    expires_at = Column(DateTime)
    share_token = Column(String(255), unique=True)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class CollaborationSession(Base):
    """Collaboration sessions table."""

    __tablename__ = "collaboration_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    identity_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    session_id = Column(String(255), nullable=False)
    socket_id = Column(String(255))
    cursor_position_json = Column(JSON)
    last_cursor_x = Column(Integer)
    last_cursor_y = Column(Integer)
    permission = Column(String(50), default="viewer")
    is_active = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    left_at = Column(DateTime)
    last_active_at = Column(DateTime)


class GroupMember(Base):
    """Group members table."""

    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(50), default="member")
    joined_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class CommentReply(Base):
    """Comment replies table."""

    __tablename__ = "comment_replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class ShapeLibrary(Base):
    """Shape libraries table."""

    __tablename__ = "shape_libraries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False, nullable=False)
    owner_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class LibraryShape(Base):
    """Library shapes table."""

    __tablename__ = "library_shapes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    library_id = Column(
        Integer, ForeignKey("shape_libraries.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    shape_type = Column(String(50), nullable=False)
    default_width = Column(Integer)
    default_height = Column(Integer)
    svg_content = Column(Text)
    shape_metadata = Column("metadata", JSON)  # Renamed to avoid reserved word
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Collection(Base):
    """Collections table."""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    thumbnail_url = Column(String(500))
    is_public = Column(Boolean, default=False, nullable=False)
    share_token = Column(String(255), unique=True)
    share_mode = Column(String(50), default="private")
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class CollectionItem(Base):
    """Collection items table."""

    __tablename__ = "collection_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(
        Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False
    )
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    added_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=False
    )
    order_index = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class CollectionShare(Base):
    """Collection shares table."""

    __tablename__ = "collection_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(
        Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False
    )
    shared_with_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    shared_with_group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    permission = Column(String(50), default="viewer")
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class EmailVerification(Base):
    """Email verifications table."""

    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    email = Column(String(255), nullable=False)
    verification_token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class SystemSetting(Base):
    """System settings table."""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    setting_key = Column(String(255), nullable=False, unique=True)
    setting_value = Column(Text)
    setting_type = Column(String(50), default="string")
    description = Column(Text)
    updated_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class ShareAnalytic(Base):
    """Share analytics table."""

    __tablename__ = "share_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    share_type = Column(String(50), nullable=False)
    share_id = Column(Integer, nullable=False)
    share_token = Column(String(255))
    accessed_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    access_ip = Column(String(50))
    user_agent = Column(String(500))
    accessed_at = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )


class LoginEvent(Base):
    """Login events table for tracking login history."""

    __tablename__ = "login_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    login_type = Column(String(50), default="password")  # password, google, sso
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    country_code = Column(String(2))  # ISO 3166-1 alpha-2
    country_name = Column(String(100))
    city = Column(String(100))
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )


class ActivityLog(Base):
    """Activity logs table for tracking user actions."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    resource_name = Column(String(255))
    details = Column(JSON)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )


class AuditLog(Base):
    """Audit logs table for tracking admin/sensitive actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(Integer)
    resource_name = Column(String(255))
    changes = Column(JSON)
    reason = Column(Text)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    status = Column(String(50), default="success")
    error_message = Column(Text)
    timestamp = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )


class Template(Base):
    """Templates table for drawing templates."""

    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(JSON, nullable=False)
    category = Column(String(100), default="custom")
    thumbnail_url = Column(String(1024))
    is_public = Column(Boolean, default=False, nullable=False)
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class ServiceAccount(Base):
    """Service accounts table for machine-to-machine authentication."""

    __tablename__ = "service_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    client_id = Column(String(50), nullable=False, unique=True)
    scopes = Column(JSON)
    rate_limit = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class ServiceAccountToken(Base):
    """Service account tokens table."""

    __tablename__ = "service_account_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_account_id = Column(
        Integer, ForeignKey("service_accounts.id", ondelete="CASCADE"), nullable=False
    )
    token_jti = Column(String(100), nullable=False, unique=True)
    name = Column(String(255))
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime)
    last_used_ip = Column(String(50))
    revoked_at = Column(DateTime)
    revoked_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class MigrationJob(Base):
    """Migration jobs table for async migration tracking."""

    __tablename__ = "migration_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    source_provider_id = Column(
        Integer, ForeignKey("storage_providers.id", ondelete="CASCADE"), nullable=False
    )
    target_provider_id = Column(
        Integer, ForeignKey("storage_providers.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    migrated_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    error_message = Column(Text)
    celery_task_id = Column(String(255))
    result_json = Column(JSON)
    status_json = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class Playbook(Base):
    """Playbooks table for workflow automation."""

    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    updated_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    status = Column(String(50), default="draft")
    is_enabled = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    trigger_type = Column(String(50))
    trigger_config = Column(JSON)
    error_handling = Column(JSON)
    tags = Column(JSON)
    canvas_data = Column(JSON)
    execution_count = Column(Integer, default=0)
    last_execution_at = Column(DateTime)
    next_run_at = Column(DateTime)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class PlaybookNode(Base):
    """Playbook nodes table for individual workflow steps."""

    __tablename__ = "playbook_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    node_id = Column(String(100), nullable=False)
    node_type = Column(String(50), nullable=False)
    node_category = Column(String(50), default="transform")
    label = Column(String(255))
    position_x = Column(Integer, nullable=False)
    position_y = Column(Integer, nullable=False)
    config = Column(JSON, nullable=False)
    data_schema = Column(JSON)
    is_enabled = Column(Boolean, default=True, nullable=False)
    execution_order = Column(Integer, default=0)
    comments = Column(Text)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class PlaybookEdge(Base):
    """Playbook edges table for connections between nodes."""

    __tablename__ = "playbook_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    edge_id = Column(String(100), nullable=False)
    source_node_id = Column(String(100), nullable=False)
    target_node_id = Column(String(100), nullable=False)
    source_handle = Column(String(50))
    target_handle = Column(String(50))
    condition = Column(JSON)
    label = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class PlaybookVersion(Base):
    """Playbook versions table for rollback capability."""

    __tablename__ = "playbook_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    nodes_json = Column(JSON, nullable=False)
    edges_json = Column(JSON, nullable=False)
    canvas_json = Column(JSON)
    change_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class PlaybookWebhook(Base):
    """Playbook webhooks table for webhook triggers."""

    __tablename__ = "playbook_webhooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255))
    token = Column(String(255), nullable=False, unique=True)
    signature_secret = Column(String(255))
    validate_signature = Column(Boolean, default=False, nullable=False)
    allowed_methods = Column(JSON)
    ip_whitelist = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class PlaybookExecution(Base):
    """Playbook executions table for individual workflow runs."""

    __tablename__ = "playbook_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    execution_id = Column(String(100), nullable=False, unique=True)
    status = Column(String(50), default="pending")
    trigger_type = Column(String(50))
    triggered_by = Column(String(50))
    triggered_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    input_json = Column(JSON)
    output_json = Column(JSON)
    error_message = Column(Text)
    error_details = Column(JSON)
    retry_count = Column(Integer, default=0)
    parent_execution_id = Column(String(100))
    worker_id = Column(String(100))
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class PlaybookNodeExecution(Base):
    """Playbook node executions table for per-node execution details."""

    __tablename__ = "playbook_node_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(100), nullable=False)
    node_id = Column(String(100), nullable=False)
    node_type = Column(String(50))
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(50), default="pending")
    input_json = Column(JSON)
    output_json = Column(JSON)
    error_message = Column(Text)
    error_details = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class PlaybookSchedule(Base):
    """Playbook schedules table for cron-like scheduling."""

    __tablename__ = "playbook_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(100), default="UTC")
    is_active = Column(Boolean, default=True, nullable=False)
    next_run_at = Column(DateTime)
    last_run_at = Column(DateTime)
    run_count = Column(Integer, default=0)
    static_input = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class PlaybookShare(Base):
    """Playbook shares table for sharing permissions."""

    __tablename__ = "playbook_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    identity_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    shared_with_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    shared_with_group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    shared_by = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    permission = Column(String(50), default="viewer")
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class PlaybookEditorLock(Base):
    """Playbook editor locks table for single-editor enforcement."""

    __tablename__ = "playbook_editor_locks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer,
        ForeignKey("playbooks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    locked_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    locked_by_name = Column(String(255))
    locked_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    socket_id = Column(String(255))


class PlaybookTemplate(Base):
    """Playbook templates table for reusable workflow templates."""

    __tablename__ = "playbook_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), default="custom")
    created_by_id = Column(
        Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False
    )
    nodes_json = Column(JSON, nullable=False)
    edges_json = Column(JSON, nullable=False)
    canvas_data = Column(JSON)
    is_public = Column(Boolean, default=False, nullable=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class PlaybookForm(Base):
    """Playbook forms table for dynamic forms."""

    __tablename__ = "playbook_forms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(255), nullable=False)
    description = Column(Text)
    fields_json = Column(JSON, nullable=False)
    form_token = Column(String(255), unique=True)
    access_type = Column(String(50), default="registered")
    allowed_users = Column(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    submission_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class PlaybookFormSubmission(Base):
    """Playbook form submissions table."""

    __tablename__ = "playbook_form_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    form_id = Column(
        Integer, ForeignKey("playbook_forms.id", ondelete="CASCADE"), nullable=False
    )
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    submitted_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    submission_data = Column(JSON, nullable=False)
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    execution_id = Column(String(100))
    submitted_at = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )


class CustomModule(Base):
    """Custom modules table for uploadable trigger/action modules."""

    __tablename__ = "custom_modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(
        Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1
    )
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255))
    description = Column(Text)
    module_type = Column(String(50), nullable=False)
    version = Column(String(50), default="1.0.0")
    code_blob = Column(Text)
    config_schema = Column(JSON)
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    is_validated = Column(Boolean, default=False, nullable=False)
    validation_errors = Column(JSON)
    is_enabled = Column(Boolean, default=True, nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )


class PlaybookNodeMetadata(Base):
    """Playbook node metadata table for comments and key/value pairs."""

    __tablename__ = "playbook_node_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    playbook_id = Column(
        Integer, ForeignKey("playbooks.id", ondelete="CASCADE"), nullable=False
    )
    node_id = Column(String(100), nullable=False)
    comments = Column(Text)
    metadata_json = Column(JSON)
    updated_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class DiagramNodeMetadata(Base):
    """Diagram node metadata table for comments and key/value pairs."""

    __tablename__ = "diagram_node_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(
        Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False
    )
    node_id = Column(String(100), nullable=False)
    comments = Column(Text)
    metadata_json = Column(JSON)
    updated_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"))
    updated_at = Column(
        DateTime,
        default=datetime.datetime.now(datetime.timezone.utc),
        onupdate=datetime.datetime.now(datetime.timezone.utc),
    )
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


def initialize_database(db_uri: str):
    """Initialize database tables using SQLAlchemy.

    Args:
        db_uri: Database connection URI (PyDAL format)
    """
    # Convert PyDAL URI format to SQLAlchemy format
    sqlalchemy_uri = db_uri
    if db_uri.startswith("postgres://"):
        sqlalchemy_uri = db_uri.replace("postgres://", "postgresql://", 1)
    elif db_uri == "sqlite:memory":
        sqlalchemy_uri = "sqlite:///:memory:"
    elif db_uri.startswith("sqlite://") and not db_uri.startswith("sqlite:///"):
        # Convert PyDAL sqlite://filename to SQLAlchemy sqlite:///filename
        sqlalchemy_uri = "sqlite:///" + db_uri[len("sqlite://"):]

    engine = create_engine(sqlalchemy_uri)

    # Create all tables
    Base.metadata.create_all(engine)

    print("✓ Database tables initialized successfully")


if __name__ == "__main__":
    import os

    from dotenv import load_dotenv

    load_dotenv()

    # Build database URI from environment variables
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "icecharts")
    db_user = os.getenv("DB_USER", "icecharts_user")
    db_password = os.getenv("DB_PASSWORD", "changeme")

    db_uri = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    initialize_database(db_uri)
