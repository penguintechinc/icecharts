# IceCharts Architecture

## System Overview

IceCharts is built on a modern, scalable microservices architecture with three primary components working together to deliver a collaborative diagramming platform.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Users' Web Browsers                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   React WebUI (Node.js/React)                      │
│  ├─ Canvas Editor       ├─ User Dashboard    ├─ Settings          │
│  ├─ Collaboration UI    ├─ Comments Panel    ├─ Export Dialog     │
│  └─ Real-time Updates   └─ Share Management  └─ User Management   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ WebSocket + REST API
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Flask API Backend (Python/PyDAL)                       │
│  ├─ Authentication      ├─ Drawing Service  ├─ Comment Service    │
│  ├─ User Management     ├─ Export Service   ├─ Permission Service │
│  ├─ WebSocket Handler   ├─ Elder Integration├─ Share Service      │
│  └─ Monitoring          └─ License Validation└─ File Upload       │
└────────────────────────────┬────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────────┐
    │PostgreSQL│      │  Redis   │      │MinIO (S3)    │
    │ Database │      │  Cache   │      │ Storage      │
    └──────────┘      └──────────┘      └──────────────┘
          │                  │
          └──────┬───────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Prometheus     │
        │ Monitoring     │
        └────────────────┘
```

## Architecture Components

### 1. Frontend Layer (React WebUI)

**Technology Stack**: Node.js 18+, React 18+, TypeScript, Tailwind CSS

**Purpose**: Provides the user interface for diagram creation and collaboration

**Key Features**:
- Single Page Application (SPA) architecture
- Real-time WebSocket communication
- State management with Zustand and React Context
- Component-based UI design
- Responsive design for desktop and tablet

**Main Components**:
```
services/webui/
├── public/              # Static assets
├── src/
│   ├── client/          # Main app
│   │   ├── App.tsx      # Root component
│   │   ├── pages/       # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Profile.tsx
│   │   │   └── Users.tsx
│   │   ├── components/  # Reusable components
│   │   │   ├── canvas/
│   │   │   │   ├── Canvas.tsx
│   │   │   │   ├── CommentsPanel.tsx
│   │   │   │   └── ExportDialog.tsx
│   │   │   ├── drawing/
│   │   │   │   └── ElderImportDialog.tsx
│   │   │   ├── common/
│   │   │   └── Layout.tsx
│   │   ├── hooks/       # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useComments.ts
│   │   │   ├── useDrawing.ts
│   │   │   └── useElderImport.ts
│   │   ├── lib/         # Utilities
│   │   │   ├── api.ts   # API client
│   │   │   └── websocket.ts
│   │   ├── store/       # State management
│   │   │   ├── commentsStore.ts
│   │   │   └── drawingsStore.ts
│   │   └── types/       # TypeScript interfaces
│   └── index.tsx        # Entry point
└── package.json
```

**Key Responsibilities**:
- User authentication and session management
- Diagram canvas rendering and manipulation
- Real-time collaboration UI
- Export functionality interface
- User profile and settings management

### 2. Backend API Layer (Flask)

**Technology Stack**: Python 3.12+, Flask, PyDAL, SQLAlchemy

**Purpose**: Core application logic and data management

**Architecture Pattern**: Three-tier service layer

```
services/flask-backend/
├── app/
│   ├── __init__.py      # Flask app initialization
│   ├── models.py        # PyDAL database models
│   ├── config.py        # Configuration management
│   ├── api/
│   │   └── v1/          # API version 1
│   │       ├── __init__.py
│   │       ├── auth.py  # Authentication endpoints
│   │       ├── users.py # User management
│   │       ├── drawings.py
│   │       ├── comments.py
│   │       ├── export.py
│   │       ├── elder.py # Elder integration
│   │       ├── share.py # Sharing endpoints
│   │       └── health.py
│   ├── services/        # Business logic
│   │   ├── comment_service.py
│   │   ├── drawing_service.py
│   │   ├── export_service.py
│   │   ├── permission_service.py
│   │   ├── share_service.py
│   │   ├── elder_service.py
│   │   ├── group_service.py
│   │   └── content_service.py
│   ├── websocket/       # Real-time communication
│   │   ├── handlers.py
│   │   ├── collaboration.py
│   │   └── __init__.py
│   ├── middleware/      # Request processing
│   │   └── auth.py
│   └── utils/           # Utilities
│       └── helpers.py
├── tests/               # Test suite
│   ├── test_auth.py
│   ├── test_drawings.py
│   ├── test_comments.py
│   └── conftest.py
├── run.py              # Development server
├── run_socketio.py     # WebSocket server
├── requirements.txt    # Python dependencies
└── Dockerfile          # Container definition
```

**Key Services**:

1. **Authentication Service** (`api/v1/auth.py`)
   - User login/logout
   - Token generation and validation
   - Password reset
   - OAuth/SSO integration

2. **Drawing Service** (`services/drawing_service.py`)
   - Create, read, update, delete drawings
   - Version management
   - Thumbnail generation
   - Metadata handling

3. **Comment Service** (`services/comment_service.py`)
   - Comment CRUD operations
   - Thread management
   - Resolution tracking
   - Statistics calculation

4. **Export Service** (`services/export_service.py`)
   - PNG/SVG/PDF generation
   - Format conversion
   - File streaming

5. **Permission Service** (`services/permission_service.py`)
   - Access control checks
   - Role-based authorization
   - Resource ownership validation

6. **Elder Integration** (`services/elder_service.py`)
   - Entity mapping and import
   - Dependency visualization
   - Layout algorithms

7. **Share Service** (`services/share_service.py`)
   - Public link generation
   - Access token management
   - Share settings

8. **WebSocket Handler** (`websocket/handlers.py`)
   - Real-time event broadcasting
   - Collaborative editing sync
   - Presence tracking

### 3. Data Layer

#### Database (PostgreSQL)

**Primary Purpose**: Persistent data storage

**Key Tables**:

```sql
-- Users and Authentication
users
  ├─ id (PRIMARY KEY)
  ├─ email (UNIQUE, indexed)
  ├─ password (hashed)
  ├─ full_name
  ├─ role (admin/maintainer/viewer)
  ├─ is_active
  └─ created_at

-- Drawings
drawings
  ├─ id (PRIMARY KEY)
  ├─ owner_id (FOREIGN KEY → users)
  ├─ name
  ├─ description
  ├─ data (JSON: nodes, edges, viewport)
  ├─ thumbnail_url
  ├─ is_public
  ├─ created_at
  └─ updated_at

-- Drawing Metadata
drawing_metadata
  ├─ id (PRIMARY KEY)
  ├─ drawing_id (UNIQUE, FOREIGN KEY)
  ├─ version
  ├─ tags (JSON array)
  ├─ grid_size
  ├─ snap_to_grid
  └─ last_modified_by_id

-- Comments
comments
  ├─ id (PRIMARY KEY)
  ├─ drawing_id (FOREIGN KEY)
  ├─ author_id (FOREIGN KEY → users)
  ├─ content
  ├─ shape_id (optional)
  ├─ parent_comment_id (self-reference for threading)
  ├─ is_resolved
  ├─ resolved_by_id
  ├─ created_at
  └─ updated_at

-- Sharing
drawing_shares
  ├─ id (PRIMARY KEY)
  ├─ drawing_id (FOREIGN KEY)
  ├─ shared_with_user_id (FOREIGN KEY)
  ├─ permission_level (view/edit)
  ├─ created_at
  └─ expires_at

-- Groups
groups
  ├─ id (PRIMARY KEY)
  ├─ name
  ├─ description
  ├─ owner_id (FOREIGN KEY)
  └─ created_at

group_members
  ├─ id (PRIMARY KEY)
  ├─ group_id (FOREIGN KEY)
  ├─ user_id (FOREIGN KEY)
  └─ role (admin/member)
```

#### Cache Layer (Redis)

**Purpose**: High-speed data caching and session management

**Usage Patterns**:
- Session storage (user authentication tokens)
- Drawing locks (prevent concurrent edits)
- Real-time presence data
- Temporary file uploads
- Rate limiting

**TTL Strategy**:
- Session tokens: 1 hour (configurable)
- Drawing locks: 5 minutes
- Presence data: 5 minutes (refreshed on activity)
- Export files: 24 hours

#### Object Storage (MinIO)

**Purpose**: File and media storage

**Storage Buckets**:
- `icecharts-drawings`: Full drawing exports
- `icecharts-thumbnails`: Drawing preview images
- `icecharts-exports`: Generated exports (PNG/PDF)
- `icecharts-uploads`: User file uploads

**File Organization**:
```
icecharts-drawings/
  ├─ user-{id}/
  │   └─ drawing-{id}/
  │       ├─ drawing.json
  │       ├─ versions/
  │       │   ├─ v1.json
  │       │   └─ v2.json
  │       └─ history/

icecharts-thumbnails/
  └─ {drawing-id}.png

icecharts-exports/
  └─ {export-id}.{format}
```

## Communication Flows

### 1. Real-Time Collaboration

```
User 1 (Browser)      WebSocket       Flask API         Database
     │                  │                  │                 │
     ├─ Draw shape ──→  │  ──────────────→ │  ─────────────→ │
     │                  │ Event broadcast  │                 │
     │  ← Update ────── │ ←──────────────── │                 │
     │                  │                  │                 │
User 2 (Browser)        │
     │                  │
     ├──────────────────┤ ← Receives event
     │ Renders shape    │
     │                  │

Flow: WebSocket maintains persistent connection for real-time updates
```

### 2. API Request Flow

```
Browser                API Endpoint         Service          Database
   │                        │                  │                 │
   ├─ GET /api/v1/        │                  │                 │
   │  drawings/{id}      │                  │                 │
   │                     │  ← Route ──→ permission_check       │
   │                     │  ← Fetch ──────────────────→        │
   │                     │  ← Load ──────────────────→        │
   │                     │  ← Cache in Redis ──────────→       │
   │                     │                  │                 │
   │  ← JSON Response ─← │                  │                 │
   │                     │                  │                 │

Flow: REST API with synchronous request/response pattern
```

### 3. Export Pipeline

```
User Initiates Export      Backend Processing        Output
      │                           │                    │
      ├─ POST /api/v1/          │                    │
      │  export (diagram data) │                    │
      │                        │  ← Validate schema│
      │                        │  ← Generate format│
      │                        │  (PNG/SVG/PDF)   │
      │                        │                    │
      │                        │  ← Upload to MinIO│
      │                        │  ← Generate link │
      │                        │                    │
      │  ← Download link ───← │                    │
      │                        │                    │

Flow: Asynchronous export processing with job queue pattern
```

## Data Models

### Drawing Model

```typescript
interface Drawing {
  id: number;
  owner_id: number;
  name: string;
  description?: string;
  data: {
    nodes: Node[];
    edges: Edge[];
    viewport?: Viewport;
  };
  thumbnail_url?: string;
  is_public: boolean;
  created_at: datetime;
  updated_at: datetime;
}

interface Node {
  id: string;
  type: string; // 'rectangle', 'circle', 'diamond', etc.
  x: number;
  y: number;
  width: number;
  height: number;
  text?: string;
  style?: StyleProperties;
  metadata?: Record<string, any>;
}

interface Edge {
  id: string;
  source: string;  // node id
  target: string;  // node id
  label?: string;
  style?: StyleProperties;
  path?: PathData;
}
```

### Comment Model

```typescript
interface Comment {
  id: number;
  drawing_id: number;
  author_id: number;
  author: {
    id: number;
    email: string;
    full_name: string;
  };
  content: string;
  shape_id?: string;
  parent_comment_id?: number;
  replies: Comment[];
  is_resolved: boolean;
  resolved_by_id?: number;
  resolved_at?: datetime;
  created_at: datetime;
  updated_at: datetime;
}
```

## Scalability Considerations

### Database
- **Connection Pooling**: Configured at 10-20 connections per service
- **Indexing Strategy**: Indexed on frequently queried fields (drawing_id, user_id, created_at)
- **Query Optimization**: N+1 query prevention with joins and eager loading

### Caching
- **Session Cache**: Redis stores active sessions (reduces DB queries)
- **Query Cache**: Frequently accessed data cached with TTL
- **Invalidation**: Cache cleared on writes using event-driven patterns

### Frontend
- **Code Splitting**: Lazy loading of routes and heavy components
- **State Optimization**: Zustand for efficient state management
- **Request Batching**: Multiple API calls combined where possible

### WebSocket
- **Connection Pooling**: Maintains persistent connections
- **Message Queuing**: Handles burst events with queue buffers
- **Broadcasting**: Efficient pub/sub for room-based notifications

## Security Architecture

### Authentication Flow

```
1. User submits credentials
2. API validates against password hash (bcrypt)
3. Generate JWT token (RS256 signature)
4. Store token in HTTP-only cookie + localStorage
5. Include token in all subsequent requests
6. API validates token signature and expiration
7. If valid, proceed; if invalid, return 401
```

### Authorization

```
For each protected resource:
1. Extract user ID from token
2. Verify user exists and is active
3. Check role-based permissions
4. Verify resource ownership or sharing permissions
5. If all pass, grant access; otherwise return 403
```

## Deployment Architecture

### Container Organization

```
icecharts-postgres      PostgreSQL database container
icecharts-redis         Redis cache container
icecharts-minio         MinIO object storage container
icecharts-api           Flask API backend container
icecharts-web           React frontend container
icecharts-prometheus    Prometheus monitoring (optional)
icecharts-grafana       Grafana dashboards (optional)
```

### Network Architecture

```
All containers on single bridge network: icecharts-network
- No containers exposed to host directly
- API accessible via port 5001
- Web UI accessible via port 3000
- Internal communication via container names (DNS)
```

## Performance Optimization

### Frontend
- Memoization of expensive components
- Virtual scrolling for large lists
- Debounced real-time updates
- Service Worker for offline support (future)

### Backend
- Batch operations where possible
- Asynchronous task processing
- Database query optimization
- Response caching

### Infrastructure
- Connection pooling
- Redis for session storage
- MinIO for efficient file serving
- CDN integration for static assets (future)

## Monitoring & Observability

### Metrics Collected
- Request count and latency
- Database query performance
- WebSocket connection count
- Export processing time
- Cache hit rates

### Logging
- Structured JSON logging
- Configurable log levels
- Central log aggregation ready (ELK stack integration)

### Health Checks
- API health endpoint: `/api/v1/health`
- Database connectivity check
- Redis connectivity check
- MinIO connectivity check

## Future Architecture Enhancements

1. **Microservices Split**
   - Export service as separate container
   - Notification service for emails
   - Analytics service

2. **Event-Driven Architecture**
   - Message queue (RabbitMQ/Kafka)
   - Event sourcing for drawing changes
   - Async processing of heavy operations

3. **Scaling Features**
   - Horizontal scaling of API instances
   - Load balancing with NGINX
   - Database read replicas
   - Sharding strategy for large deployments

4. **Advanced Features**
   - GraphQL API alongside REST
   - WebRTC for peer-to-peer collaboration
   - Real-time video conferencing integration
   - Advanced search with Elasticsearch

## Related Documentation

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Features Guide](FEATURES.md) - Detailed feature documentation
- [Contributing](CONTRIBUTING.md) - Development guidelines
