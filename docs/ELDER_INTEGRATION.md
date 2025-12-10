# Elder API Integration for IceCharts

This document describes the Elder API integration that allows users to import infrastructure entities and dependencies from Elder as shapes and connectors into IceCharts drawings.

## Overview

The Elder integration enables IceCharts users to:

- Connect to an Elder instance (self-hosted or cloud)
- Browse infrastructure entities (compute, VPC, subnet, datacenter, network, user, security issues)
- Select entities for import
- Import entities as shapes with appropriate styling and icons
- Include relationships/dependencies as connectors between shapes
- Automatically layout imported entities on the canvas

## Architecture

### Backend Components

#### 1. Elder Service (`app/services/elder_service.py`)

The `ElderClient` class provides the core Elder API integration:

```python
from app.services.elder_service import ElderClient, ElderEntity, ElderDependency

# Initialize client
client = ElderClient(
    base_url="https://elder.example.com",
    api_key="your-api-key"
)

# Fetch entities
entities = await client.get_entities(
    org_id=1,
    entity_type="compute",  # Optional filter
    limit=100
)

# Fetch dependencies
relationships = await client.get_relationships(org_id=1)

# Get full dependency graph
graph = await client.get_graph(org_id=1, depth=2)
```

**Key Classes:**

- **`ElderEntity`**: Represents an Elder entity with id, name, type, metadata
- **`ElderDependency`**: Represents a relationship between entities
- **`IceChartsNode`**: Result of mapping Elder entity to IceCharts shape
- **`IceChartsConnector`**: Result of mapping Elder dependency to connector

**Key Methods:**

- `get_entities()`: Fetch entities from Elder API
- `get_relationships()`: Fetch dependencies from Elder API
- `get_graph()`: Fetch full dependency graph
- `map_entity_to_shape()`: Convert Elder entity to IceCharts node
- `map_relationship_to_connector()`: Convert dependency to connector
- `calculate_layout_positions()`: Calculate hierarchical layout for entities

#### 2. Elder API Endpoints (`app/api/v1/elder.py`)

REST API endpoints for Elder integration:

**Connection Management:**

```bash
# Validate connection to Elder instance
POST /api/v1/elder/validate-connection
Content-Type: application/json

{
  "base_url": "https://elder.example.com",
  "api_key": "api-key"
}

Response:
{
  "success": true,
  "message": "Connection to Elder validated successfully"
}
```

**Entity Operations:**

```bash
# Get entities from Elder
GET /api/v1/elder/entities?base_url=https://elder.example.com&api_key=xxx&org_id=1&entity_type=compute&limit=100

Response:
{
  "success": true,
  "entities": [
    {
      "id": 1,
      "unique_id": 12345678,
      "name": "web-server-01",
      "entity_type": "compute",
      "description": "Production web server",
      "metadata": {
        "ip": "10.0.1.5",
        "os": "Ubuntu 22.04"
      }
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

```bash
# Get relationships
GET /api/v1/elder/relationships?base_url=xxx&api_key=xxx&org_id=1

Response:
{
  "success": true,
  "relationships": [
    {
      "id": 1,
      "source_entity_id": 1,
      "target_entity_id": 2,
      "dependency_type": "hosted_on",
      "description": "web server hosted on infrastructure"
    }
  ],
  "total": 10
}
```

```bash
# Get full graph
GET /api/v1/elder/graph?base_url=xxx&api_key=xxx&org_id=1&depth=2

Response:
{
  "success": true,
  "graph": {
    "entities": [...],
    "dependencies": [...]
  }
}
```

**Import Operation:**

```bash
# Import entities into drawing
POST /api/v1/elder/import
Content-Type: application/json

{
  "drawing_id": "drawing-123",
  "base_url": "https://elder.example.com",
  "api_key": "api-key",
  "org_id": 1,
  "entity_ids": [1, 2, 3],
  "include_dependencies": true,
  "canvas_width": 1600,
  "canvas_height": 900
}

Response:
{
  "success": true,
  "message": "Imported 3 entities and 2 relationships",
  "nodes": [
    {
      "id": "elder_1_12345678",
      "type": "rectangle",
      "position": { "x": 100, "y": 100 },
      "data": {
        "label": "web-server-01",
        "icon": "server",
        "elder_type": "compute",
        "metadata": {...}
      },
      "style": {
        "backgroundColor": "#3B82F6",
        "color": "#FFFFFF"
      }
    }
  ],
  "connectors": [
    {
      "id": "elder_dep_1",
      "source": "elder_1_12345678",
      "target": "elder_2_87654321",
      "type": "default",
      "animated": true,
      "label": "hosted on"
    }
  ],
  "entity_count": 3,
  "relationship_count": 2
}
```

### Frontend Components

#### 1. Hook: `useElderImport` (`hooks/useElderImport.ts`)

React hook managing Elder import state and operations:

```typescript
const {
  isLoading,
  error,
  entities,
  selectedEntities,
  isConnected,
  validateConnection,
  fetchEntities,
  fetchRelationships,
  toggleEntitySelection,
  toggleSelectAll,
  importEntities,
  reset,
} = useElderImport();
```

**Key Methods:**

- `validateConnection(baseUrl, apiKey)`: Test Elder connection
- `fetchEntities(baseUrl, apiKey, orgId, entityType?)`: Get entities from Elder
- `fetchRelationships(baseUrl, apiKey, orgId)`: Get relationships
- `toggleEntitySelection(entityId)`: Select/deselect entity
- `toggleSelectAll()`: Select all entities
- `importEntities(drawingId, includeDependencies?)`: Import selected entities
- `reset()`: Clear state

#### 2. Component: `ElderImportDialog` (`components/drawing/ElderImportDialog.tsx`)

Modal dialog for the complete import workflow:

```typescript
<ElderImportDialog
  drawingId="drawing-123"
  isOpen={true}
  onClose={() => setDialogOpen(false)}
  onImport={(nodes, connectors) => {
    // Handle imported nodes and connectors
  }}
/>
```

**Workflow Steps:**

1. **Connect**: Enter Elder URL, API key, and organization ID
2. **Browse**: Filter and view available entities
3. **Select**: Choose which entities to import
4. **Configure**: Options for including dependencies
5. **Import**: Execute import and show progress

## Entity Type Mapping

Elder entities are mapped to IceCharts shapes as follows:

| Elder Type | IceCharts Shape | Icon | Color |
|-----------|-----------------|------|-------|
| `compute` | Rectangle | server | #3B82F6 (Blue) |
| `vpc` | Rectangle | network | #10B981 (Green) |
| `subnet` | Rectangle | share-2 | #6366F1 (Indigo) |
| `datacenter` | Rectangle | database | #F59E0B (Amber) |
| `network` | Diamond | router | #8B5CF6 (Purple) |
| `user` | Circle | user | #EC4899 (Pink) |
| `security_issue` | Diamond | alert-triangle | #EF4444 (Red) |

## Dependency Type Mapping

Relationships between entities become animated connectors with appropriate labels:

| Dependency Type | Label | Animated |
|-----------------|-------|----------|
| `depends_on` | "depends on" | Yes |
| `hosted_on` | "hosted on" | No |
| `manages` | "manages" | No |
| `connects_to` | "connects to" | Yes |

## Usage Example

### Backend Implementation

```python
from flask import Flask, jsonify, request
from app.services.elder_service import ElderClient

app = Flask(__name__)

@app.route('/api/v1/elder/import', methods=['POST'])
def import_elder_entities():
    data = request.get_json()

    client = ElderClient(
        base_url=data['base_url'],
        api_key=data['api_key']
    )

    # Fetch entities
    entities = await client.get_entities(
        org_id=data['org_id'],
        limit=1000
    )

    # Map to shapes
    nodes = []
    for entity in entities:
        node = ElderClient.map_entity_to_shape(
            entity,
            x=100,
            y=100
        )
        nodes.append(node.to_dict())

    return jsonify({'nodes': nodes})
```

### Frontend Implementation

```typescript
import ElderImportDialog from '@/components/drawing/ElderImportDialog';
import { useElderImport } from '@/hooks/useElderImport';

function DrawingEditor({ drawingId }: { drawingId: string }) {
  const [showImport, setShowImport] = useState(false);

  const handleImport = (nodes: unknown[], connectors: unknown[]) => {
    // Add nodes and connectors to drawing
    addNodesToCanvas(nodes);
    addConnectorsToCanvas(connectors);
  };

  return (
    <>
      <button onClick={() => setShowImport(true)}>
        Import from Elder
      </button>

      <ElderImportDialog
        drawingId={drawingId}
        isOpen={showImport}
        onClose={() => setShowImport(false)}
        onImport={handleImport}
      />
    </>
  );
}
```

## Configuration

### Environment Variables

The Elder integration requires these environment variables (optional, can be provided per request):

```bash
# Elder instance URL
ELDER_BASE_URL=https://elder.example.com

# Elder API key
ELDER_API_KEY=your-api-key

# Default organization ID
ELDER_ORG_ID=1
```

### API Client Configuration

The client uses httpx for async HTTP requests with configurable timeout:

```python
client = ElderClient(
    base_url="https://elder.example.com",
    api_key="api-key",
    timeout=30  # Request timeout in seconds
)
```

## Error Handling

### Backend Errors

The API returns appropriate error responses:

```json
{
  "success": false,
  "error": "Failed to connect to Elder: Connection refused"
}
```

Common error scenarios:

- **400 Bad Request**: Missing or invalid parameters
- **401 Unauthorized**: Invalid API credentials
- **503 Service Unavailable**: Elder service unreachable

### Frontend Error Handling

The `useElderImport` hook manages error state:

```typescript
const { error, isLoading } = useElderImport();

if (error) {
  return <div className="error">{error}</div>;
}
```

## Performance Considerations

### Pagination

For large entity lists, use pagination:

```python
# Fetch entities in pages
entities = []
for offset in range(0, total_count, limit):
    page = await client.get_entities(
        org_id=1,
        limit=100,
        offset=offset
    )
    entities.extend(page)
```

### Layout Calculation

The layout algorithm uses a grid-based approach for O(n) complexity:

```python
positions = ElderClient.calculate_layout_positions(
    entities,
    dependencies,
    canvas_width=1600,
    canvas_height=900
)
```

### Connection Caching

The hook caches connection details to avoid re-entry:

```typescript
const connectionRef = useRef<{ baseUrl, apiKey, orgId }>(null);
// Connection details persist across state changes
```

## Security Considerations

### API Key Handling

- API keys are transmitted in request headers/query parameters
- In production, use HTTPS only
- Consider storing keys in secure vaults
- Rotate keys regularly

### Authentication

The Elder integration respects IceCharts authentication:

```python
@elder_v1_bp.route("/entities", methods=["GET"])
@auth_required()  # IceCharts user must be authenticated
async def get_entities():
    ...
```

## Troubleshooting

### Connection Failures

1. Verify Elder URL is accessible
2. Check API key is valid
3. Ensure organization ID exists
4. Check network connectivity

### Import Issues

1. Verify entity IDs exist
2. Check dependencies reference valid entities
3. Review canvas dimensions for layout
4. Check Elder service logs

## Future Enhancements

Potential improvements for the integration:

1. **Bulk Operations**: Import/export multiple drawings
2. **Filtering**: Advanced entity filtering by metadata
3. **Real-time Sync**: Keep drawing synchronized with Elder
4. **Custom Mappings**: User-defined entity-to-shape mappings
5. **Caching**: Cache entities locally to reduce API calls
6. **Webhook Integration**: Automatically update on Elder changes
7. **Batch Import**: Import multiple drawings from templates

## See Also

- [Elder Documentation](https://github.com/penguintechinc/Elder)
- [IceCharts API Documentation](./API.md)
- [Canvas Shapes Reference](./SHAPES.md)
