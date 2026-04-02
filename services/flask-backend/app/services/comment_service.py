"""Comment Service - Business logic for drawing comments."""

from datetime import datetime
from typing import Optional

from ..models import (create_comment, delete_comment, get_comment_by_id,
                      get_comments_by_drawing, get_comments_tree,
                      resolve_comment, unresolve_comment, update_comment)


class CommentService:
    """Service class for comment operations."""

    @staticmethod
    def create_comment(
        drawing_id: int,
        author_id: int,
        content: str,
        shape_id: Optional[str] = None,
        parent_comment_id: Optional[int] = None,
    ) -> dict:
        """Create a new comment on a drawing.

        Args:
            drawing_id: ID of the drawing
            author_id: ID of the comment author
            content: Comment text content
            shape_id: Optional ID of the shape being commented on
            parent_comment_id: Optional parent comment ID for replies

        Returns:
            Created comment dict with author info
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        if len(content) > 5000:
            raise ValueError(
                "Comment content exceeds maximum length of 5000 characters"
            )

        return create_comment(
            drawing_id=drawing_id,
            author_id=author_id,
            content=content.strip(),
            shape_id=shape_id,
            parent_comment_id=parent_comment_id,
        )

    @staticmethod
    def get_comments_for_drawing(
        drawing_id: int, shape_id: Optional[str] = None, filter_type: str = "all"
    ) -> list[dict]:
        """Get comments for a drawing with optional filtering.

        Args:
            drawing_id: ID of the drawing
            shape_id: Optional shape ID to filter by
            filter_type: "all", "open", or "resolved"

        Returns:
            List of comments with author and resolved_by info
        """
        if filter_type == "open":
            return get_comments_by_drawing(
                drawing_id=drawing_id,
                shape_id=shape_id,
                only_unresolved=True,
            )
        elif filter_type == "resolved":
            comments = get_comments_by_drawing(drawing_id=drawing_id, shape_id=shape_id)
            return [c for c in comments if c.get("is_resolved")]
        else:  # "all"
            return get_comments_by_drawing(drawing_id=drawing_id, shape_id=shape_id)

    @staticmethod
    def get_comments_tree(drawing_id: int) -> list[dict]:
        """Get comments organized as a threaded tree.

        Args:
            drawing_id: ID of the drawing

        Returns:
            List of root comments with nested replies
        """
        return get_comments_tree(drawing_id=drawing_id)

    @staticmethod
    def get_comment_with_replies(comment_id: int) -> Optional[dict]:
        """Get a comment and all its replies.

        Args:
            comment_id: ID of the comment

        Returns:
            Comment dict with replies array
        """
        comment = get_comment_by_id(comment_id)
        if not comment:
            return None

        # Get all replies to this comment
        replies = []

        def collect_replies(parent_id: int):
            """Recursively collect all nested replies."""
            from ..models import get_db

            db = get_db()

            direct_replies = db(db.comments.parent_comment_id == parent_id).select(
                orderby=db.comments.created_at
            )

            for reply in direct_replies:
                reply_dict = get_comment_by_id(reply.id)
                if reply_dict:
                    reply_dict["replies"] = []
                    replies.append(reply_dict)
                    collect_replies(reply.id)

        collect_replies(comment_id)
        comment["replies"] = replies
        return comment

    @staticmethod
    def update_comment(comment_id: int, content: str) -> Optional[dict]:
        """Update comment content.

        Args:
            comment_id: ID of the comment to update
            content: New comment content

        Returns:
            Updated comment dict
        """
        if not content or not content.strip():
            raise ValueError("Comment content cannot be empty")

        if len(content) > 5000:
            raise ValueError(
                "Comment content exceeds maximum length of 5000 characters"
            )

        return update_comment(comment_id=comment_id, content=content.strip())

    @staticmethod
    def delete_comment(comment_id: int) -> bool:
        """Delete a comment and all its replies.

        Args:
            comment_id: ID of the comment to delete

        Returns:
            True if deleted successfully
        """
        return delete_comment(comment_id=comment_id)

    @staticmethod
    def resolve_comment(comment_id: int, resolved_by_id: int) -> Optional[dict]:
        """Mark a comment as resolved.

        Args:
            comment_id: ID of the comment
            resolved_by_id: ID of the user marking it resolved

        Returns:
            Updated comment dict with resolved info
        """
        return resolve_comment(comment_id=comment_id, resolved_by_id=resolved_by_id)

    @staticmethod
    def unresolve_comment(comment_id: int) -> Optional[dict]:
        """Mark a comment as unresolved.

        Args:
            comment_id: ID of the comment

        Returns:
            Updated comment dict
        """
        return unresolve_comment(comment_id=comment_id)

    @staticmethod
    def get_unresolved_count(drawing_id: int, shape_id: Optional[str] = None) -> int:
        """Get count of unresolved comments.

        Args:
            drawing_id: ID of the drawing
            shape_id: Optional shape ID to filter by

        Returns:
            Count of unresolved comments
        """
        from ..models import get_db

        db = get_db()

        query = db.comments.drawing_id == drawing_id
        if shape_id:
            query = query & (db.comments.shape_id == shape_id)
        query = query & (db.comments.is_resolved == False)

        return db(query).count()

    @staticmethod
    def get_comment_summary(drawing_id: int) -> dict:
        """Get comment statistics for a drawing.

        Args:
            drawing_id: ID of the drawing

        Returns:
            Dictionary with comment counts and metadata
        """
        from ..models import get_db

        db = get_db()

        all_comments = db(db.comments.drawing_id == drawing_id).select()
        total = len(all_comments)
        resolved = len([c for c in all_comments if c.is_resolved])
        unresolved = total - resolved

        # Count comments by shape
        shape_counts = {}
        for comment in all_comments:
            if comment.shape_id:
                shape_counts[comment.shape_id] = (
                    shape_counts.get(comment.shape_id, 0) + 1
                )

        return {
            "total_comments": total,
            "resolved_comments": resolved,
            "unresolved_comments": unresolved,
            "comments_by_shape": shape_counts,
        }
