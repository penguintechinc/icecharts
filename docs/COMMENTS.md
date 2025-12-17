# IceCharts Comments and Metadata System

## Overview

A comprehensive comments system for IceCharts that enables collaborative feedback on drawings with threaded replies, shape-specific comments, and resolution tracking.

## Quick Reference

### Backend Quick Start

```python
from app.services.comment_service import CommentService

# Create comment
CommentService.create_comment(
    drawing_id=123,
    author_id=456,
    content="Your comment",
    shape_id="node-1",           # Optional
    parent_comment_id=None       # Optional
)

# Get comments
CommentService.get_comments_for_drawing(
    drawing_id=123,
    shape_id="node-1",          # Optional
    filter_type="all"           # "all", "open", "resolved"
)

# Get threaded tree structure
CommentService.get_comments_tree(drawing_id=123)

# Update comment
CommentService.update_comment(comment_id=123, content="New text")

# Delete comment (cascades to replies)
CommentService.delete_comment(comment_id=123)

# Resolve/Unresolve
CommentService.resolve_comment(comment_id=123, resolved_by_id=456)
CommentService.unresolve_comment(comment_id=123)

# Statistics
CommentService.get_comment_summary(drawing_id=123)
```

### Frontend Quick Start

```typescript
import { useCommentsStore } from './store/commentsStore';
import { CommentsPanel } from './components/canvas/CommentsPanel';
import { CommentMarker } from './components/canvas/CommentMarker';

// Zustand Store
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

// UI Components
<CommentsPanel
  drawingId={drawingId}
  selectedShapeId={nodeId}
  isOpen={true}
  onClose={() => setOpen(false)}
/>

<CommentMarker
  shapeId={node.id}
  drawingId={drawingId}
  onClickMarker={(shapeId) => selectShape(shapeId)}
/>
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

## Backend Architecture

### Database Schema

#### Comments Table
Stores all comments with threading and resolution support:
- `id` - Primary key
- `drawing_id` - Reference to drawing
- `author_id` - Reference to user who created
- `content` - Comment text (max 5000 chars)
- `shape_id` - Optional reference to specific shape
- `parent_comment_id` - For threaded replies
- `is_resolved` - Resolution status
- `resolved_by_id` - User who marked resolved
- `resolved_at` - When marked resolved
- `created_at` - Timestamp
- `updated_at` - Timestamp

#### Drawings Table
Canvas drawings with ownership and metadata:
- `id` - Primary key
- `owner_id` - Reference to owner
- `name` - Drawing name
- `description` - Optional description
- `data` - JSON containing nodes, edges, viewport
- `thumbnail_url` - Cached thumbnail
- `is_public` - Public access flag
- `created_at` - Timestamp
- `updated_at` - Timestamp

#### Drawing Metadata Table
Version and configuration tracking:
- `id` - Primary key
- `drawing_id` - Reference to drawing (unique)
- `version` - Version string (e.g., "1.0.0")
- `tags` - JSON array of tags
- `grid_size` - Grid size setting
- `snap_to_grid` - Snap to grid enabled
- `last_modified_by_id` - Last editor
- `created_at` - Timestamp
- `updated_at` - Timestamp

### API Endpoints (Detailed)

#### List Comments
```
GET /api/v1/drawings/<drawing_id>/comments?shape_id=node-1&filter=all&thread=false
```
Query Parameters:
- `shape_id` - Filter by specific shape (optional)
- `filter` - "all" (default), "open", "resolved"
- `thread` - "true" for tree structure, "false" for flat

#### Create Comment
```
POST /api/v1/drawings/<drawing_id>/comments
{
  "content": "Comment text",
  "shape_id": "node-1",
  "parent_comment_id": 5
}
```

#### Update Comment
```
PUT /api/v1/drawings/<drawing_id>/comments/<comment_id>
{
  "content": "Updated text"
}
```

#### Delete Comment
```
DELETE /api/v1/drawings/<drawing_id>/comments/<comment_id>
```
Cascades delete to all replies.

#### Resolve/Unresolve
```
POST /api/v1/drawings/<drawing_id>/comments/<comment_id>/resolve
POST /api/v1/drawings/<drawing_id>/comments/<comment_id>/unresolve
```

#### Comment Summary
```
GET /api/v1/drawings/<drawing_id>/comments/summary
```
Returns statistics on comment counts and breakdown by shape.

### Backend Files

**`/services/flask-backend/app/models.py`**
- Database table definitions
- CRUD helper functions for drawings, comments, and metadata
- Access control utilities
- Query builders for filtering and sorting

**`/services/flask-backend/app/services/comment_service.py`**
- `CommentService` class with business logic
- Validation and error handling
- Threaded comment tree building
- Comment statistics calculation

**`/services/flask-backend/app/api/v1/comments.py`**
- Flask blueprint with all comment endpoints
- Request validation and response formatting
- Authorization checks
- Error responses

## Frontend Architecture

### TypeScript Types

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
  resolved_by?: {
    id: string;
    email: string;
    full_name: string;
  };
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  replies?: Comment[];
}

interface CommentSummary {
  total_comments: number;
  resolved_comments: number;
  unresolved_comments: number;
  comments_by_shape: Record<string, number>;
}
```

### State Management

**Zustand Store (`src/store/commentsStore.ts`)**
Global state for application-wide comment management:
- `commentsByDrawing` - Cache by drawing ID
- `summaryByDrawing` - Statistics cache
- `filterType` - Current filter preference
- `selectedShapeId` - For UI state
- All CRUD actions

**Custom Hook (`src/hooks/useComments.ts`)**
Local component-level state:
- Simpler for single-component use
- No global state pollution
- Independent loading/error states

### Components

**CommentsPanel (`src/components/canvas/CommentsPanel.tsx`)**
Right sidebar UI with:
- Comment list with threaded display
- Filter buttons (All/Open/Resolved)
- Comment statistics
- New comment form
- Real-time updates

**CommentThread (`src/components/common/CommentThread.tsx`)**
Recursive comment display with:
- Author avatar and info
- Timestamps
- Edit/delete buttons
- Resolve/unresolve toggle
- Reply form
- Nested replies (collapsible)

**CommentMarker (`src/components/canvas/CommentMarker.tsx`)**
Visual indicators on shapes:
- Badge showing comment count
- Red (unresolved) or green (resolved) color
- Click handler to filter panel
- Hover tooltip

### API Integration (`src/lib/api.ts`)

```typescript
api.comments.list(drawingId, params)
api.comments.create(drawingId, data)
api.comments.update(drawingId, commentId, data)
api.comments.delete(drawingId, commentId)
api.comments.resolve(drawingId, commentId)
api.comments.unresolve(drawingId, commentId)
api.comments.getSummary(drawingId)
```

## Usage Examples

### Backend Examples

#### Get Threaded Comments
```python
comments_tree = CommentService.get_comments_tree(drawing_id=123)

for root_comment in comments_tree:
    print(f"{root_comment['author']['full_name']}: {root_comment['content']}")
    for reply in root_comment.get('replies', []):
        print(f"  {reply['author']['full_name']}: {reply['content']}")
```

#### Get Statistics
```python
summary = CommentService.get_comment_summary(drawing_id=123)
# {
#   "total_comments": 10,
#   "resolved_comments": 7,
#   "unresolved_comments": 3,
#   "comments_by_shape": {"node-1": 5, "node-2": 3}
# }
```

### Frontend Examples

#### Using Zustand Store
```typescript
import { useCommentsStore } from './store/commentsStore';

function MyComponent() {
  const { comments, createComment, resolveComment } = useCommentsStore();

  const handleNewComment = async () => {
    const comment = await createComment(drawingId, "Needs review");
  };

  const unresolvedCount = comments.filter(c => !c.is_resolved).length;
}
```

#### Using Hook
```typescript
import { useComments } from './hooks/useComments';

function MyComponent() {
  const { comments, fetchComments, createComment } = useComments();

  useEffect(() => {
    fetchComments(drawingId);
  }, [drawingId]);
}
```

#### Component Integration
```tsx
import { CommentsPanel } from './components/canvas/CommentsPanel';
import { CommentMarker } from './components/canvas/CommentMarker';

export function Canvas() {
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [selectedShape, setSelectedShape] = useState<string>();

  return (
    <>
      <div className="canvas">
        {nodes.map(node => (
          <div key={node.id} onClick={() => setSelectedShape(node.id)}>
            <CommentMarker
              shapeId={node.id}
              drawingId={drawingId}
              onClickMarker={() => setIsPanelOpen(true)}
            />
          </div>
        ))}
      </div>

      <CommentsPanel
        drawingId={drawingId}
        selectedShapeId={selectedShape}
        isOpen={isPanelOpen}
        onClose={() => setIsPanelOpen(false)}
      />
    </>
  );
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

### Handle Errors
```typescript
const { error, clearError } = useCommentsStore();

if (error) {
  console.error('Comment error:', error);
  clearError();
}
```

## Security

All endpoints include:
- Authentication requirement (`@auth_required`)
- Authorization checks (owner or public access)
- Comment ownership validation
- Input validation and sanitization
- SQL injection protection via PyDAL

## Performance Features

- Comments indexed by drawing ID
- Lazy loading of reply threads
- Summary statistics separate from full comments
- Efficient database queries with proper indexing
- Zustand store for client-side caching
- React component memoization

## Features

- Unlimited threaded comments
- Shape-specific comments
- Comment resolution tracking
- User mention support (ready)
- Edit and delete with history (ready)
- Rich text (ready for markdown)
- Comment avatars and author info
- Visual indicators for unresolved
- Advanced filtering
- Statistics dashboard

## Database Initialization

Add to Flask app initialization:
```python
from app.models import init_db, init_drawing_tables

app = Flask(__name__)
db = init_db(app)
init_drawing_tables(db)
```

## File Structure

### Backend
```
services/flask-backend/app/
     models.py                      # Database models
     services/comment_service.py    # Comment business logic
     api/v1/comments.py             # API endpoints
```

### Frontend
```
services/webui/src/
     types/index.ts                 # TypeScript interfaces
     lib/api.ts                     # API client
     store/commentsStore.ts         # Zustand store
     hooks/useComments.ts           # Custom hook
     components/
       canvas/
          CommentsPanel.tsx         # Comments sidebar
          CommentMarker.tsx         # Shape indicators
       common/
         CommentThread.tsx          # Comment display
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

## Testing

Recommended test cases:
- Create/read/update/delete comments
- Thread operations (nested replies)
- Resolution status changes
- Filter operations (by shape, by status)
- Access control (unauthorized users)
- Cascade deletes (parent comment with replies)
- Comment statistics accuracy
- Concurrent updates
- Large comment trees (performance)

## Future Enhancements

1. **Rich Text** - Markdown/HTML support
2. **Mentions** - @user tagging and notifications
3. **Attachments** - Images and files
4. **Real-time WebSocket** - Collaborative updates
5. **Reactions** - Emoji reactions
6. **Templates** - Pre-built formats
7. **Search** - Full-text search
8. **Export** - PDF/CSV export
9. **Analytics** - Activity metrics
10. **Approval** - Comment moderation workflow
11. **Email** - Notification emails
12. **Audit Log** - Change history
