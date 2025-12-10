"""Services module for IceCharts Flask Backend."""

from .comment_service import CommentService
from .content_service import ContentService
from .drawing_service import DrawingService
from .group_service import GroupService
from .permission_service import PermissionService
from .share_service import ShareService

# Optional: ExportService requires weasyprint which has heavy dependencies
try:
    from .export_service import ExportService
except ImportError:
    ExportService = None  # type: ignore

__all__ = [
    "CommentService",
    "ContentService",
    "DrawingService",
    "ExportService",
    "GroupService",
    "PermissionService",
    "ShareService",
]
