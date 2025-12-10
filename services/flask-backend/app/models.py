"""PyDAL Database Models."""

from datetime import datetime
from typing import Optional

from flask import Flask, g
from pydal import DAL, Field
from pydal.validators import IS_EMAIL, IS_IN_SET, IS_NOT_EMPTY

from .config import Config

# Valid roles for the application
VALID_ROLES = ["admin", "maintainer", "viewer"]


def init_db(app: Flask) -> DAL:
    """Initialize database connection and define tables."""
    db_uri = Config.get_db_uri()

    db = DAL(
        db_uri,
        pool_size=Config.DB_POOL_SIZE,
        migrate=True,
        check_reserved=["all"],
        lazy_tables=False,
    )

    # Define users table
    db.define_table(
        "users",
        Field("email", "string", length=255, unique=True, requires=[
            IS_NOT_EMPTY(error_message="Email is required"),
            IS_EMAIL(error_message="Invalid email format"),
        ]),
        Field("password_hash", "string", length=255, requires=IS_NOT_EMPTY()),
        Field("full_name", "string", length=255),
        Field("role", "string", length=50, default="viewer", requires=IS_IN_SET(
            VALID_ROLES,
            error_message=f"Role must be one of: {', '.join(VALID_ROLES)}"
        )),
        Field("is_active", "boolean", default=True),
        # OAuth fields
        Field("google_id", "string", length=255, unique=True),
        Field("oauth_provider", "string", length=50),  # 'google', 'github', etc.
        Field("profile_picture_url", "string", length=500),
        Field("created_at", "datetime", default=datetime.utcnow),
        Field("updated_at", "datetime", default=datetime.utcnow, update=datetime.utcnow),
    )

    # Define refresh tokens table for token invalidation
    db.define_table(
        "refresh_tokens",
        Field("user_id", "reference users", requires=IS_NOT_EMPTY()),
        Field("token_hash", "string", length=255, unique=True),
        Field("expires_at", "datetime"),
        Field("revoked", "boolean", default=False),
        Field("created_at", "datetime", default=datetime.utcnow),
    )

    # Commit table definitions
    db.commit()

    # Store db instance in app
    app.config["db"] = db

    return db


def get_db() -> DAL:
    """Get database connection for current request context."""
    from flask import current_app

    if "db" not in g:
        g.db = current_app.config.get("db")
    return g.db


def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email address."""
    db = get_db()
    user = db(db.users.email == email).select().first()
    return user.as_dict() if user else None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user by ID."""
    db = get_db()
    user = db(db.users.id == user_id).select().first()
    return user.as_dict() if user else None


def get_user_by_google_id(google_id: str) -> Optional[dict]:
    """Get user by Google ID."""
    db = get_db()
    user = db(db.users.google_id == google_id).select().first()
    return user.as_dict() if user else None


def create_user(email: str, password_hash: str, full_name: str = "",
                role: str = "viewer", google_id: str = None,
                oauth_provider: str = None) -> dict:
    """Create a new user."""
    db = get_db()
    user_id = db.users.insert(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        is_active=True,
        google_id=google_id,
        oauth_provider=oauth_provider,
    )
    db.commit()
    return get_user_by_id(user_id)


def update_user(user_id: int, **kwargs) -> Optional[dict]:
    """Update user by ID."""
    db = get_db()

    # Filter allowed fields
    allowed_fields = {"email", "password_hash", "full_name", "role", "is_active",
                      "google_id", "oauth_provider", "profile_picture_url"}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_data:
        return get_user_by_id(user_id)

    db(db.users.id == user_id).update(**update_data)
    db.commit()
    return get_user_by_id(user_id)


def delete_user(user_id: int) -> bool:
    """Delete user by ID."""
    db = get_db()
    deleted = db(db.users.id == user_id).delete()
    db.commit()
    return deleted > 0


def list_users(page: int = 1, per_page: int = 20) -> tuple[list[dict], int]:
    """List users with pagination."""
    db = get_db()
    offset = (page - 1) * per_page

    users = db(db.users).select(
        orderby=db.users.created_at,
        limitby=(offset, offset + per_page),
    )
    total = db(db.users).count()

    return [u.as_dict() for u in users], total


def store_refresh_token(user_id: int, token_hash: str, expires_at: datetime) -> int:
    """Store a refresh token."""
    db = get_db()
    token_id = db.refresh_tokens.insert(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.commit()
    return token_id


def revoke_refresh_token(token_hash: str) -> bool:
    """Revoke a refresh token."""
    db = get_db()
    updated = db(db.refresh_tokens.token_hash == token_hash).update(revoked=True)
    db.commit()
    return updated > 0


def is_refresh_token_valid(token_hash: str) -> bool:
    """Check if refresh token is valid (not revoked and not expired)."""
    db = get_db()
    token = db(
        (db.refresh_tokens.token_hash == token_hash) &
        (db.refresh_tokens.revoked == False) &
        (db.refresh_tokens.expires_at > datetime.utcnow())
    ).select().first()
    return token is not None


def revoke_all_user_tokens(user_id: int) -> int:
    """Revoke all refresh tokens for a user."""
    db = get_db()
    updated = db(db.refresh_tokens.user_id == user_id).update(revoked=True)
    db.commit()
    return updated


# ============================================================================
# DRAWINGS, COMMENTS, AND METADATA MODELS
# ============================================================================

def init_drawing_tables(db: DAL) -> None:
    """Initialize drawing-related tables (drawings, comments, metadata)."""

    # Define drawings table
    db.define_table(
        "drawings",
        Field("owner_id", "reference users", requires=IS_NOT_EMPTY()),
        Field("name", "string", length=255, requires=IS_NOT_EMPTY()),
        Field("description", "text"),
        Field("data", "json"),  # Stores drawing data (nodes, edges, viewport)
        Field("thumbnail_url", "string", length=500),
        Field("is_public", "boolean", default=False),
        Field("created_at", "datetime", default=datetime.utcnow),
        Field("updated_at", "datetime", default=datetime.utcnow, update=datetime.utcnow),
    )

    # Define comments table
    db.define_table(
        "comments",
        Field("drawing_id", "reference drawings", requires=IS_NOT_EMPTY()),
        Field("author_id", "reference users", requires=IS_NOT_EMPTY()),
        Field("content", "text", requires=IS_NOT_EMPTY()),
        Field("shape_id", "string", length=255),  # Optional: reference to specific shape/node
        Field("parent_comment_id", "reference comments"),  # For threaded replies
        Field("is_resolved", "boolean", default=False),
        Field("resolved_by_id", "reference users"),
        Field("resolved_at", "datetime"),
        Field("created_at", "datetime", default=datetime.utcnow),
        Field("updated_at", "datetime", default=datetime.utcnow, update=datetime.utcnow),
    )

    # Define drawing metadata table
    db.define_table(
        "drawing_metadata",
        Field("drawing_id", "reference drawings", unique=True, requires=IS_NOT_EMPTY()),
        Field("version", "string", length=50, default="1.0.0"),
        Field("tags", "json"),  # List of tags
        Field("grid_size", "integer", default=10),
        Field("snap_to_grid", "boolean", default=True),
        Field("last_modified_by_id", "reference users"),
        Field("created_at", "datetime", default=datetime.utcnow),
        Field("updated_at", "datetime", default=datetime.utcnow, update=datetime.utcnow),
    )

    db.commit()


# ============================================================================
# DRAWING HELPERS
# ============================================================================

def get_drawing_by_id(drawing_id: int) -> Optional[dict]:
    """Get drawing by ID with access control check."""
    db = get_db()
    drawing = db(db.drawings.id == drawing_id).select().first()
    return drawing.as_dict() if drawing else None


def create_drawing(owner_id: int, name: str, description: str = "",
                   data: dict = None) -> dict:
    """Create a new drawing."""
    db = get_db()
    drawing_id = db.drawings.insert(
        owner_id=owner_id,
        name=name,
        description=description,
        data=data or {"nodes": [], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}},
        is_public=False,
    )
    db.commit()

    # Create associated metadata record
    db.drawing_metadata.insert(
        drawing_id=drawing_id,
        version="1.0.0",
        tags=[],
        last_modified_by_id=owner_id,
    )
    db.commit()

    return get_drawing_by_id(drawing_id)


def update_drawing(drawing_id: int, **kwargs) -> Optional[dict]:
    """Update drawing by ID."""
    db = get_db()

    allowed_fields = {"name", "description", "data", "is_public"}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_data:
        return get_drawing_by_id(drawing_id)

    db(db.drawings.id == drawing_id).update(**update_data)
    db.commit()
    return get_drawing_by_id(drawing_id)


def delete_drawing(drawing_id: int) -> bool:
    """Delete drawing by ID and cascade delete related records."""
    db = get_db()

    # Delete associated comments
    db(db.comments.drawing_id == drawing_id).delete()
    # Delete metadata
    db(db.drawing_metadata.drawing_id == drawing_id).delete()
    # Delete drawing
    deleted = db(db.drawings.id == drawing_id).delete()
    db.commit()
    return deleted > 0


def list_drawings(owner_id: int = None, page: int = 1,
                  per_page: int = 20) -> tuple[list[dict], int]:
    """List drawings owned by user or public drawings."""
    db = get_db()
    offset = (page - 1) * per_page

    query = db.drawings
    if owner_id:
        query = query.owner_id == owner_id

    drawings = db(query).select(
        orderby=~db.drawings.updated_at,
        limitby=(offset, offset + per_page),
    )
    total = db(query).count()

    return [d.as_dict() for d in drawings], total


# ============================================================================
# COMMENT HELPERS
# ============================================================================

def create_comment(drawing_id: int, author_id: int, content: str,
                   shape_id: str = None, parent_comment_id: int = None) -> dict:
    """Create a new comment."""
    db = get_db()
    comment_id = db.comments.insert(
        drawing_id=drawing_id,
        author_id=author_id,
        content=content,
        shape_id=shape_id,
        parent_comment_id=parent_comment_id,
        is_resolved=False,
    )
    db.commit()
    return get_comment_by_id(comment_id)


def get_comment_by_id(comment_id: int) -> Optional[dict]:
    """Get comment by ID with author info."""
    db = get_db()
    comment = db(db.comments.id == comment_id).select().first()
    if not comment:
        return None

    comment_dict = comment.as_dict()
    # Add author info
    author = get_user_by_id(comment_dict["author_id"])
    if author:
        comment_dict["author"] = {
            "id": author["id"],
            "email": author["email"],
            "full_name": author.get("full_name", ""),
            "profile_picture_url": author.get("profile_picture_url"),
        }

    # Add resolved_by info if applicable
    if comment_dict.get("resolved_by_id"):
        resolved_by = get_user_by_id(comment_dict["resolved_by_id"])
        if resolved_by:
            comment_dict["resolved_by"] = {
                "id": resolved_by["id"],
                "email": resolved_by["email"],
                "full_name": resolved_by.get("full_name", ""),
            }

    return comment_dict


def get_comments_by_drawing(drawing_id: int, shape_id: str = None,
                            only_unresolved: bool = False) -> list[dict]:
    """Get all comments for a drawing, optionally filtered by shape."""
    db = get_db()

    query = db.comments.drawing_id == drawing_id
    if shape_id:
        query = query & (db.comments.shape_id == shape_id)
    if only_unresolved:
        query = query & (db.comments.is_resolved == False)

    comments = db(query).select(orderby=db.comments.created_at)

    result = []
    for comment in comments:
        comment_dict = get_comment_by_id(comment.id)
        if comment_dict:
            result.append(comment_dict)

    return result


def get_comments_tree(drawing_id: int) -> list[dict]:
    """Get comments organized as a threaded tree structure."""
    db = get_db()

    # Get all comments for drawing
    comments = db(db.comments.drawing_id == drawing_id).select(
        orderby=db.comments.created_at
    )

    # Build tree structure
    comment_map = {}
    root_comments = []

    for comment in comments:
        comment_dict = get_comment_by_id(comment.id)
        if comment_dict:
            comment_dict["replies"] = []
            comment_map[comment_dict["id"]] = comment_dict

            if comment_dict.get("parent_comment_id"):
                # Add to parent's replies
                parent_id = comment_dict["parent_comment_id"]
                if parent_id in comment_map:
                    comment_map[parent_id]["replies"].append(comment_dict)
            else:
                # Root comment
                root_comments.append(comment_dict)

    return root_comments


def update_comment(comment_id: int, **kwargs) -> Optional[dict]:
    """Update comment by ID."""
    db = get_db()

    allowed_fields = {"content"}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_data:
        return get_comment_by_id(comment_id)

    db(db.comments.id == comment_id).update(**update_data)
    db.commit()
    return get_comment_by_id(comment_id)


def delete_comment(comment_id: int) -> bool:
    """Delete comment and cascade delete replies."""
    db = get_db()

    # Delete all replies (child comments)
    db(db.comments.parent_comment_id == comment_id).delete()
    # Delete the comment itself
    deleted = db(db.comments.id == comment_id).delete()
    db.commit()
    return deleted > 0


def resolve_comment(comment_id: int, resolved_by_id: int) -> Optional[dict]:
    """Mark a comment as resolved."""
    db = get_db()
    db(db.comments.id == comment_id).update(
        is_resolved=True,
        resolved_by_id=resolved_by_id,
        resolved_at=datetime.utcnow(),
    )
    db.commit()
    return get_comment_by_id(comment_id)


def unresolve_comment(comment_id: int) -> Optional[dict]:
    """Mark a comment as unresolved."""
    db = get_db()
    db(db.comments.id == comment_id).update(
        is_resolved=False,
        resolved_by_id=None,
        resolved_at=None,
    )
    db.commit()
    return get_comment_by_id(comment_id)


# ============================================================================
# DRAWING METADATA HELPERS
# ============================================================================

def get_drawing_metadata(drawing_id: int) -> Optional[dict]:
    """Get metadata for a drawing."""
    db = get_db()
    metadata = db(db.drawing_metadata.drawing_id == drawing_id).select().first()
    return metadata.as_dict() if metadata else None


def update_drawing_metadata(drawing_id: int, **kwargs) -> Optional[dict]:
    """Update drawing metadata."""
    db = get_db()

    allowed_fields = {"version", "tags", "grid_size", "snap_to_grid", "last_modified_by_id"}
    update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not update_data:
        return get_drawing_metadata(drawing_id)

    db(db.drawing_metadata.drawing_id == drawing_id).update(**update_data)
    db.commit()
    return get_drawing_metadata(drawing_id)
