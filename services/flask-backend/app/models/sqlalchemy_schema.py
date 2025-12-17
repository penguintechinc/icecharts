"""SQLAlchemy schema definitions for table initialization.

This module is used ONLY for initializing database tables.
After initialization, PyDAL is used for all database operations.
"""

import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
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
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
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
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
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
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
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
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
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
    identity_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Drawing(Base):
    """Drawings table."""

    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    created_by_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
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
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    created_by_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    content_json = Column(JSON, nullable=False)
    change_summary = Column(Text)
    storage_provider_id = Column(Integer, ForeignKey("storage_providers.id", ondelete="SET NULL"))
    storage_path = Column(String(1024))
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class Shape(Base):
    """Shapes table."""

    __tablename__ = "shapes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
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
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
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
    shape_id = Column(Integer, ForeignKey("shapes.id", ondelete="CASCADE"), nullable=False, unique=True)
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
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
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
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
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
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
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
    identity_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
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
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member")
    joined_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class CommentReply(Base):
    """Comment replies table."""

    __tablename__ = "comment_replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    text_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class ShapeLibrary(Base):
    """Shape libraries table."""

    __tablename__ = "shape_libraries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False, nullable=False)
    owner_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
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
    library_id = Column(Integer, ForeignKey("shape_libraries.id", ondelete="CASCADE"), nullable=False)
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
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, default=1)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
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
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    drawing_id = Column(Integer, ForeignKey("drawings.id", ondelete="CASCADE"), nullable=False)
    added_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=False)
    order_index = Column(Integer, default=0)
    added_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class CollectionShare(Base):
    """Collection shares table."""

    __tablename__ = "collection_shares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"))
    shared_with_group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))
    permission = Column(String(50), default="viewer")
    created_by_id = Column(Integer, ForeignKey("identities.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))


class EmailVerification(Base):
    """Email verifications table."""

    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
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
    accessed_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False)


class LoginEvent(Base):
    """Login events table for tracking login history."""

    __tablename__ = "login_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("identities.id", ondelete="CASCADE"), nullable=False)
    login_type = Column(String(50), default="password")  # password, google, sso
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    country_code = Column(String(2))  # ISO 3166-1 alpha-2
    country_name = Column(String(100))
    city = Column(String(100))
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc), nullable=False)


def initialize_database(db_uri: str):
    """Initialize database tables using SQLAlchemy.

    Args:
        db_uri: Database connection URI (PyDAL format)
    """
    # Convert PyDAL postgres:// to SQLAlchemy postgresql://
    sqlalchemy_uri = db_uri
    if db_uri.startswith("postgres://"):
        sqlalchemy_uri = db_uri.replace("postgres://", "postgresql://", 1)

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
