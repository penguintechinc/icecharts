# IceCharts Comments System - Quick Reference

## Backend

### Import & Use
```python
from app.services.comment_service import CommentService
from app.models import get_comments_by_drawing, create_comment, resolve_comment
```

### Key Methods

**Create Comment**
```python
CommentService.create_comment(
    drawing_id=123,
    author_id=456,
    content="Your comment",
    shape_id="node-1",           # Optional
    parent_comment_id=None       # Optional
)
```

**Get Comments**
```python
# Flat list with filters
CommentService.get_comments_for_drawing(
    drawing_id=123,
    shape_id="node-1",          # Optional
    filter_type="all"           # "all", "open", "resolved"
)

# Threaded tree structure
CommentService.get_comments_tree(drawing_id=123)
```

**Update Comment**
```python
CommentService.update_comment(comment_id=123, content="New text")
```

**Delete Comment**
```python
CommentService.delete_comment(comment_id=123)  # Cascades to replies
```

**Resolve/Unresolve**
```python
CommentService.resolve_comment(comment_id=123, resolved_by_id=456)
CommentService.unresolve_comment(comment_id=123)
```

**Statistics**
```python
CommentService.get_comment_summary(drawing_id=123)
# Returns: total, resolved, unresolved, by-shape breakdown
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/drawings/<id>/comments` | List comments |
| POST | `/api/v1/drawings/<id>/comments` | Create comment |
| PUT | `/api/v1/drawings/<id>/comments/<id>` | Update comment |
| DELETE | `/api/v1/drawings/<id>/comments/<id>` | Delete comment |
| POST | `/api/v1/drawings/<id>/comments/<id>/resolve` | Mark resolved |
| POST | `/api/v1/drawings/<id>/comments/<id>/unresolve` | Mark unresolved |
| GET | `/api/v1/drawings/<id>/comments/summary` | Get stats |

## Frontend

### Import & Use
```typescript
import { useCommentsStore } from './store/commentsStore';
import { useComments } from './hooks/useComments';
import { CommentsPanel } from './components/canvas/CommentsPanel';
import { CommentMarker } from './components/canvas/CommentMarker';
import { CommentThread } from './components/common/CommentThread';
```

### Zustand Store
```typescript
const { comments, createComment, updateComment } = useCommentsStore();

// Fetch comments
await useCommentsStore.getState().fetchComments(drawingId);

// Create comment
const comment = await createComment(
  drawingId,
  "Comment text",
  "node-1",  // shape_id
  null       // parent_comment_id
);

// Filter comments by status
const unresolved = useCommentsStore((state) =>
  state.commentsByDrawing[drawingId]?.filter(c => !c.is_resolved)
);
```

### Custom Hook
```typescript
const { comments, isLoading, error, createComment } = useComments();

useEffect(() => {
  useComments().fetchComments(drawingId, { filter: 'open' });
}, [drawingId]);
```

### UI Components

**CommentsPanel**
```tsx
<CommentsPanel
  drawingId={drawingId}
  selectedShapeId={nodeId}
  isOpen={true}
  onClose={() => setOpen(false)}
/>
```

**CommentMarker**
```tsx
<CommentMarker
  shapeId={node.id}
  drawingId={drawingId}
  onClickMarker={(shapeId) => selectShape(shapeId)}
/>
```

**CommentThread**
```tsx
<CommentThread
  comment={comment}
  isAuthor={comment.author.id === userId}
  onUpdate={handleUpdate}
  onDelete={handleDelete}
  onReply={handleReply}
  onResolve={handleResolve}
/>
```

## Database Tables

### comments
```
id                  INT PRIMARY KEY
drawing_id          INT REFERENCE drawings
author_id           INT REFERENCE users
content             TEXT
shape_id            VARCHAR(255)
parent_comment_id   INT REFERENCE comments
is_resolved         BOOLEAN
resolved_by_id      INT REFERENCE users
resolved_at         DATETIME
created_at          DATETIME
updated_at          DATETIME
```

### drawings
```
id              INT PRIMARY KEY
owner_id        INT REFERENCE users
name            VARCHAR(255)
description     TEXT
data            JSON
thumbnail_url   VARCHAR(500)
is_public       BOOLEAN
created_at      DATETIME
updated_at      DATETIME
```

### drawing_metadata
```
id                  INT PRIMARY KEY
drawing_id          INT UNIQUE REFERENCE drawings
version             VARCHAR(50)
tags                JSON
grid_size           INT
snap_to_grid        BOOLEAN
last_modified_by_id INT REFERENCE users
created_at          DATETIME
updated_at          DATETIME
```

## Type Definitions

### Comment
```typescript
interface Comment {
  id: string;
  drawing_id: string;
  author: {
    id: string;
    email: string;
    full_name: string;
    profile_picture_url?: string;
  };
  content: string;
  shape_id?: string;
  parent_comment_id?: string;
  is_resolved: boolean;
  resolved_by?: { id: string; email: string; full_name: string };
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  replies?: Comment[];
}
```

### CommentSummary
```typescript
interface CommentSummary {
  total_comments: number;
  resolved_comments: number;
  unresolved_comments: number;
  comments_by_shape: Record<string, number>;
}
```

## Common Patterns

### Show Comments for Shape
```typescript
const shapeComments = comments.filter(c => c.shape_id === shapeId);
const unresolvedCount = shapeComments.filter(c => !c.is_resolved).length;
```

### Create Nested Reply
```typescript
await createComment(
  drawingId,
  "Reply text",
  shapeId,
  parentCommentId  // Makes it a reply
);
```

### Filter by Status
```typescript
// Unresolved only
const open = comments.filter(c => !c.is_resolved);

// Resolved only
const resolved = comments.filter(c => c.is_resolved);

// By shape
const forShape = comments.filter(c => c.shape_id === shapeId);
```

### Update UI After Action
```typescript
// Zustand handles this automatically
const comment = await createComment(drawingId, text);
// Comments are auto-updated in store
```

### Handle Errors
```typescript
const { error, clearError } = useCommentsStore();

if (error) {
  console.error('Comment error:', error);
  clearError();
}
```

## Integration Checklist

- [x] Database models (comments, drawings, metadata)
- [x] Backend API endpoints
- [x] Comment service with business logic
- [x] Frontend types and interfaces
- [x] Zustand store for state
- [x] Custom hook for components
- [x] CommentsPanel sidebar UI
- [x] CommentThread display
- [x] CommentMarker badges
- [ ] WebSocket real-time updates
- [ ] Rich text editor
- [ ] User mentions
- [ ] Email notifications
- [ ] Comment search
- [ ] Comment analytics

## Files Created

Backend:
- `/services/flask-backend/app/models.py` - Updated with drawing/comment models
- `/services/flask-backend/app/services/comment_service.py` - New
- `/services/flask-backend/app/api/v1/comments.py` - New

Frontend:
- `/services/webui/src/types/index.ts` - Updated with Comment types
- `/services/webui/src/lib/api.ts` - Updated with comment endpoints
- `/services/webui/src/store/commentsStore.ts` - New
- `/services/webui/src/hooks/useComments.ts` - New
- `/services/webui/src/components/canvas/CommentsPanel.tsx` - New
- `/services/webui/src/components/canvas/CommentMarker.tsx` - New
- `/services/webui/src/components/common/CommentThread.tsx` - New

Documentation:
- `/COMMENTS_SYSTEM.md` - Full documentation
- `/COMMENTS_QUICK_REFERENCE.md` - This file
