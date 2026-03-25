# IceCharts Quick Start Guide

Get up and running with IceCharts features quickly. This guide provides condensed setup instructions for each major feature.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Real-Time Collaboration](#real-time-collaboration)
- [Comments System](#comments-system)
- [Export Functionality](#export-functionality)
- [Elder Integration](#elder-integration)
- [Enterprise SSO](#enterprise-sso)

---

## Initial Setup

### Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.12+

### Start All Services

```bash
# Clone and start
git clone https://github.com/PenguinCloud/IceCharts.git
cd IceCharts
docker-compose up -d

# Services available at:
# - Frontend: http://localhost:3000
# - API: http://localhost:5000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### Development Mode

```bash
# Backend
cd services/flask-backend
pip install -r requirements.txt
python run.py

# Frontend
cd services/webui
npm install
npm run dev
```

---

## Real-Time Collaboration

### 5-Minute Setup

**1. Start Redis**
```bash
docker run -d --name icecharts-redis -p 6379:6379 redis:7-alpine
```

**2. Add to Your Canvas**
```tsx
import { useCollaboration } from './hooks/useCollaboration';
import { CollaboratorCursors, CollaboratorAvatars } from './components/canvas';

function MyCanvas({ drawingId }) {
  const { sendCursorPosition, lockShape, unlockShape } = useCollaboration({
    roomId: drawingId,
    enabled: true,
  });

  return (
    <div onMouseMove={(e) => sendCursorPosition(e.clientX, e.clientY)}>
      <CollaboratorCursors />
      <CollaboratorAvatars position="top-right" />
    </div>
  );
}
```

**Key Features:** Real-time cursors, user presence, shape locking

📚 **Full docs:** [COLLABORATION.md](COLLABORATION.md)

---

## Comments System

### Backend
```python
from app.services.comment_service import CommentService

# Create comment
comment = CommentService.create_comment(
    drawing_id=123,
    author_id=456,
    content="Needs review",
    shape_id="node-1"
)

# Get threaded comments
comments = CommentService.get_comments_tree(drawing_id=123)

# Resolve comment
CommentService.resolve_comment(comment_id=123, resolved_by_id=456)
```

### Frontend
```typescript
import { useCommentsStore } from './store/commentsStore';
import { CommentsPanel } from './components/canvas/CommentsPanel';

const { comments, createComment, resolveComment } = useCommentsStore();

<CommentsPanel
  drawingId={drawingId}
  selectedShapeId={nodeId}
  isOpen={true}
  onClose={() => setOpen(false)}
/>
```

### API Endpoints
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/drawings/<id>/comments` | List comments |
| POST | `/api/v1/drawings/<id>/comments` | Create comment |
| POST | `/api/v1/drawings/<id>/comments/<id>/resolve` | Mark resolved |

📚 **Full docs:** [COMMENTS.md](COMMENTS.md)

---

## Export Functionality

### Using React Component
```tsx
import { ExportDialog } from './components/drawing/ExportDialog';

<ExportDialog
  drawingId="my_drawing_123"
  drawingName="My Diagram"
  isOpen={showExport}
  onClose={() => setShowExport(false)}
/>
```

### Using Hook
```typescript
import { useExport } from './hooks/useExport';

const { loading, exportDrawing } = useExport();

await exportDrawing('drawing_id', {
  format: 'png',  // png, svg, pdf, json
  width: 1024,
  height: 768,
  quality: 95
});
```

### API Endpoints
```bash
GET /api/v1/drawings/{id}/export/png?width=1024&height=768&quality=95
GET /api/v1/drawings/{id}/export/svg
GET /api/v1/drawings/{id}/export/pdf?page_size=A4
GET /api/v1/drawings/{id}/export/json
```

📚 **Full docs:** [EXPORT.md](EXPORT.md)

---

## Elder Integration

Import infrastructure entities from Elder into IceCharts diagrams.

### Using the Dialog
```tsx
import ElderImportDialog from './components/drawing/ElderImportDialog';

<ElderImportDialog
  drawingId="drawing-123"
  isOpen={showDialog}
  onClose={() => setShowDialog(false)}
  onImport={(nodes, connectors) => {
    canvas.addNodes(nodes);
    canvas.addConnectors(connectors);
  }}
/>
```

### Using the Hook
```typescript
import { useElderImport } from './hooks/useElderImport';

const { validateConnection, fetchEntities, importEntities } = useElderImport();

await validateConnection(url, apiKey);
await fetchEntities(url, apiKey, orgId);
const result = await importEntities(drawingId);
```

### API Endpoints
```bash
POST /api/v1/elder/validate-connection
GET  /api/v1/elder/entities?base_url=...&api_key=...&org_id=1
POST /api/v1/elder/import
```

### Entity Mapping
| Elder Type | Shape | Color |
|------------|-------|-------|
| compute | Rectangle | Blue |
| vpc | Rectangle | Green |
| network | Diamond | Purple |
| user | Circle | Pink |
| security_issue | Diamond | Red |

📚 **Full docs:** [ELDER.md](ELDER.md)

---

## Enterprise SSO

### SAML Configuration
```bash
curl -X POST http://localhost:5000/api/v1/sso/saml/config \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata_url": "https://idp.example.com/metadata",
    "jit_enabled": true,
    "auto_assign_role": "viewer"
  }'
```

### OIDC Configuration
```bash
curl -X POST http://localhost:5000/api/v1/sso/oidc/config \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "issuer": "https://accounts.google.com",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "jit_enabled": true
  }'
```

### IdP Quick Setup

**Okta:**
- Metadata URL: `https://{org}.okta.com/app/{app-id}/sso/saml/metadata`

**Azure AD:**
- OIDC Issuer: `https://login.microsoftonline.com/{tenant-id}/v2.0`

**Google:**
- OIDC Issuer: `https://accounts.google.com`

### Frontend Integration
```tsx
import SSOLoginButtons from './components/SSOLoginButtons';

<SSOLoginButtons />  // Displays configured SSO options
```

📚 **Full docs:** [SSO.md](SSO.md)

---

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| WebSocket won't connect | Check CORS config, verify JWT token, ensure Redis running |
| Export fails | Check image dimensions (100-4000px), verify Cairo installed |
| SSO signature failed | Verify X.509 certificate, check metadata URL |
| Elder connection refused | Verify Elder URL accessible, check API key |

### Debug Mode

```bash
# Backend
FLASK_DEBUG=1 python run.py

# Frontend
localStorage.debug = '*';
```

---

## Next Steps

- [Getting Started Guide](GETTING_STARTED.md) - Full installation instructions
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Architecture](ARCHITECTURE.md) - System design overview
- [Deployment](DEPLOYMENT.md) - Production deployment guide
