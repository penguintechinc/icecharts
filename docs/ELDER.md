# Elder API Integration for IceCharts

This document describes the Elder API integration that allows users to import infrastructure entities and dependencies from Elder as shapes and connectors into IceCharts drawings.

## Quick Reference

### Files Overview

| File | Location | Lines | Purpose |
|------|----------|-------|---------|
| **elder_service.py** | `services/flask-backend/app/services/` | 481 | Core API client and mapping logic |
| **elder.py** | `services/flask-backend/app/api/v1/` | 356 | REST API endpoints |
| **useElderImport.ts** | `services/webui/src/hooks/` | 377 | React hook for import workflow |
| **ElderImportDialog.tsx** | `services/webui/src/components/drawing/` | 652 | Modal dialog component |

### API Endpoints

```
POST   /api/v1/elder/validate-connection     # Test connection
GET    /api/v1/elder/entities               # Get entities
GET    /api/v1/elder/relationships          # Get dependencies
GET    /api/v1/elder/graph                  # Get full graph
POST   /api/v1/elder/import                 # Import into drawing
GET    /api/v1/elder/health                 # Health check
```

### Core Classes

```python
# Main client
ElderClient(base_url, api_key, timeout=30)

# Data classes
ElderEntity(id, unique_id, name, entity_type, ...)
ElderDependency(id, source_entity_id, target_entity_id, ...)
IceChartsNode(id, type, position, data, ...)
IceChartsConnector(id, source, target, type, ...)

# Enum
EntityTypeMapping.COMPUTE     # Maps to blue rectangle
EntityTypeMapping.VPC         # Maps to green rectangle
EntityTypeMapping.NETWORK     # Maps to purple diamond
# ... etc
```

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

```python
# Client methods
await client.get_entities(org_id, entity_type?, limit?, offset?)
await client.get_relationships(org_id, source_id?, target_id?)
await client.get_graph(org_id, entity_id?, depth?)

# Mapping methods (static)
ElderClient.map_entity_to_shape(entity, x, y)
ElderClient.map_relationship_to_connector(dep, source_id, target_id)
ElderClient.calculate_layout_positions(entities, deps, width, height)
```

**Complete Example - Direct Service Usage:**

```python
import asyncio
from app.services.elder_service import ElderClient

async def example_import():
    # Create client
    client = ElderClient(
        base_url="https://elder.example.com",
        api_key="your-api-key"
    )

    # Fetch all compute entities
    entities = await client.get_entities(
        org_id=1,
        entity_type="compute"
    )

    print(f"Found {len(entities)} compute entities")
    for entity in entities:
        print(f"  - {entity.name} ({entity.entity_type})")

    # Get dependencies
    deps = await client.get_relationships(org_id=1)
    print(f"\nFound {len(deps)} dependencies")

    # Map to shapes
    positions = client.calculate_layout_positions(entities, deps)

    nodes = []
    for entity in entities:
        pos = positions[entity.id]
        node = client.map_entity_to_shape(entity, x=pos["x"], y=pos["y"])
        nodes.append(node)

    # Map to connectors
    entity_to_node = {e.id: n.id for e, n in zip(entities, nodes)}
    connectors = []
    for dep in deps:
        if dep.source_entity_id in entity_to_node:
            source_node = entity_to_node[dep.source_entity_id]
            target_node = entity_to_node[dep.target_entity_id]
            connector = client.map_relationship_to_connector(
                dep,
                source_node,
                target_node
            )
            connectors.append(connector)

    return nodes, connectors


# Run example
asyncio.run(example_import())
```

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

**Flask Route Example - Complete Import:**

```python
from flask import Blueprint, jsonify, request
from app.services.elder_service import ElderClient
from app.models import Drawing

elder_bp = Blueprint('elder', __name__)

@elder_bp.route('/drawings/<drawing_id>/import-elder', methods=['POST'])
async def import_elder_to_drawing(drawing_id: str):
    """Import Elder entities into a drawing."""
    data = request.get_json()

    # Validate drawing exists and user has access
    drawing = Drawing.query.get(drawing_id)
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404

    # Create Elder client
    client = ElderClient(
        base_url=data['base_url'],
        api_key=data['api_key']
    )

    # Fetch entities
    entities = await client.get_entities(
        org_id=data['org_id'],
        limit=1000
    )

    # Filter if specific IDs provided
    if data.get('entity_ids'):
        entity_ids = set(data['entity_ids'])
        entities = [e for e in entities if e.id in entity_ids]

    # Get dependencies
    dependencies = await client.get_relationships(org_id=data['org_id'])

    # Calculate positions
    positions = ElderClient.calculate_layout_positions(
        entities,
        dependencies,
        canvas_width=data.get('canvas_width', 1600),
        canvas_height=data.get('canvas_height', 900)
    )

    # Map to shapes
    nodes_data = []
    entity_id_map = {}

    for entity in entities:
        pos = positions[entity.id]
        node = ElderClient.map_entity_to_shape(entity, x=pos['x'], y=pos['y'])
        nodes_data.append(node.to_dict())
        entity_id_map[entity.id] = node.id

    # Map dependencies to connectors
    connectors_data = []
    for dep in dependencies:
        if (dep.source_entity_id in entity_id_map and
            dep.target_entity_id in entity_id_map):
            connector = ElderClient.map_relationship_to_connector(
                dep,
                entity_id_map[dep.source_entity_id],
                entity_id_map[dep.target_entity_id]
            )
            connectors_data.append(connector.to_dict())

    # Update drawing with imported data
    drawing.data = {
        'nodes': nodes_data,
        'connectors': connectors_data,
        'viewport': {'x': 0, 'y': 0, 'zoom': 1}
    }
    drawing.save()

    return jsonify({
        'success': True,
        'message': f'Imported {len(nodes_data)} entities and {len(connectors_data)} relationships',
        'nodes': nodes_data,
        'connectors': connectors_data
    })
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

**Example - Using the Hook:**

```typescript
import React, { useState } from 'react';
import { useElderImport } from '@/hooks/useElderImport';

function ElderIntegrationExample() {
  const [baseUrl, setBaseUrl] = useState('https://elder.example.com');
  const [apiKey, setApiKey] = useState('');
  const [orgId, setOrgId] = useState('1');

  const {
    isLoading,
    error,
    entities,
    selectedEntities,
    isConnected,
    validateConnection,
    fetchEntities,
    toggleEntitySelection,
    importEntities,
  } = useElderImport();

  const handleConnect = async () => {
    const valid = await validateConnection(baseUrl, apiKey);
    if (valid) {
      await fetchEntities(baseUrl, apiKey, parseInt(orgId));
    }
  };

  const handleImport = async () => {
    const result = await importEntities('drawing-123', true);
    if (result) {
      console.log(`Imported ${result.nodes.length} nodes and ${result.connectors.length} connectors`);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h2>Elder Integration</h2>

      {!isConnected ? (
        <div>
          <input
            type="url"
            placeholder="Elder URL"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
          />
          <input
            type="password"
            placeholder="API Key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
          />
          <input
            type="number"
            placeholder="Organization ID"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
          />
          <button onClick={handleConnect} disabled={isLoading}>
            {isLoading ? 'Connecting...' : 'Connect'}
          </button>
        </div>
      ) : (
        <div>
          <h3>Entities ({selectedEntities.size} selected)</h3>
          <ul>
            {entities.map((entity) => (
              <li key={entity.id}>
                <input
                  type="checkbox"
                  checked={selectedEntities.has(entity.id)}
                  onChange={() => toggleEntitySelection(entity.id)}
                />
                {entity.name} ({entity.entity_type})
              </li>
            ))}
          </ul>
          <button onClick={handleImport} disabled={isLoading || selectedEntities.size === 0}>
            {isLoading ? 'Importing...' : 'Import Selected'}
          </button>
        </div>
      )}

      {error && <div style={{ color: 'red' }}>{error}</div>}
    </div>
  );
}

export default ElderIntegrationExample;
```

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

**Example - Using the Dialog Component:**

```typescript
import React, { useState } from 'react';
import ElderImportDialog from '@/components/drawing/ElderImportDialog';

function DrawingCanvas() {
  const [showImportDialog, setShowImportDialog] = useState(false);
  const drawingId = 'current-drawing-id';

  const handleImport = (nodes: unknown[], connectors: unknown[]) => {
    // Add nodes and connectors to the canvas
    console.log('Imported nodes:', nodes);
    console.log('Imported connectors:', connectors);

    // Update your canvas state with the imported data
    addNodesToCanvas(nodes);
    addConnectorsToCanvas(connectors);

    setShowImportDialog(false);
  };

  return (
    <div>
      <canvas id="drawing-canvas" />

      <button onClick={() => setShowImportDialog(true)}>
        Import from Elder
      </button>

      <ElderImportDialog
        drawingId={drawingId}
        isOpen={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        onImport={handleImport}
      />
    </div>
  );
}

function addNodesToCanvas(nodes: unknown[]) {
  // Implementation to add nodes to canvas
}

function addConnectorsToCanvas(connectors: unknown[]) {
  // Implementation to add connectors to canvas
}

export default DrawingCanvas;
```

**Advanced Form with Validation:**

```typescript
import React, { useState, useCallback } from 'react';
import { useElderImport } from '@/hooks/useElderImport';

function AdvancedElderImport({ drawingId }: { drawingId: string }) {
  const [step, setStep] = useState<'config' | 'select' | 'importing'>('config');
  const [config, setConfig] = useState({
    baseUrl: '',
    apiKey: '',
    orgId: '',
    entityType: '',
    includeDependencies: true,
  });

  const {
    isLoading,
    error,
    entities,
    selectedEntities,
    isConnected,
    validateConnection,
    fetchEntities,
    toggleEntitySelection,
    toggleSelectAll,
    importEntities,
  } = useElderImport();

  const handleConnect = useCallback(async () => {
    // Validate inputs
    if (!config.baseUrl.trim() || !config.apiKey.trim() || !config.orgId.trim()) {
      alert('Please fill all connection details');
      return;
    }

    // Validate connection
    const isValid = await validateConnection(config.baseUrl, config.apiKey);
    if (!isValid) {
      return;
    }

    // Fetch entities
    await fetchEntities(
      config.baseUrl,
      config.apiKey,
      parseInt(config.orgId),
      config.entityType || undefined
    );

    setStep('select');
  }, [config, validateConnection, fetchEntities]);

  const handleImport = useCallback(async () => {
    if (selectedEntities.size === 0) {
      alert('Select at least one entity');
      return;
    }

    setStep('importing');
    const result = await importEntities(drawingId, config.includeDependencies);

    if (result) {
      console.log('Import successful:', result);
      // Handle success
    } else {
      setStep('select');
    }
  }, [selectedEntities, drawingId, config.includeDependencies, importEntities]);

  return (
    <form onSubmit={(e) => { e.preventDefault(); }}>
      {step === 'config' && (
        <fieldset disabled={isLoading}>
          <legend>Elder Configuration</legend>

          <label>
            Base URL:
            <input
              type="url"
              value={config.baseUrl}
              onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
              placeholder="https://elder.example.com"
              required
            />
          </label>

          <label>
            API Key:
            <input
              type="password"
              value={config.apiKey}
              onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
              placeholder="Your API key"
              required
            />
          </label>

          <label>
            Organization ID:
            <input
              type="number"
              value={config.orgId}
              onChange={(e) => setConfig({ ...config, orgId: e.target.value })}
              placeholder="1"
              required
            />
          </label>

          <label>
            Entity Type Filter (optional):
            <select
              value={config.entityType}
              onChange={(e) => setConfig({ ...config, entityType: e.target.value })}
            >
              <option value="">All Types</option>
              <option value="compute">Compute</option>
              <option value="vpc">VPC</option>
              <option value="network">Network</option>
              <option value="user">User</option>
            </select>
          </label>

          {error && <p style={{ color: 'red' }}>{error}</p>}

          <button type="button" onClick={handleConnect}>
            {isLoading ? 'Connecting...' : 'Connect'}
          </button>
        </fieldset>
      )}

      {step === 'select' && (
        <fieldset disabled={isLoading}>
          <legend>Select Entities ({selectedEntities.size} selected)</legend>

          <label>
            <input
              type="checkbox"
              onChange={toggleSelectAll}
              checked={selectedEntities.size === entities.length && entities.length > 0}
            />
            Select All
          </label>

          <ul>
            {entities.map((entity) => (
              <li key={entity.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedEntities.has(entity.id)}
                    onChange={() => toggleEntitySelection(entity.id)}
                  />
                  {entity.name} ({entity.entity_type})
                  {entity.description && <small> - {entity.description}</small>}
                </label>
              </li>
            ))}
          </ul>

          <label>
            <input
              type="checkbox"
              checked={config.includeDependencies}
              onChange={(e) => setConfig({ ...config, includeDependencies: e.target.checked })}
            />
            Include Dependencies
          </label>

          <div>
            <button type="button" onClick={() => setStep('config')}>
              Back
            </button>
            <button type="button" onClick={handleImport} disabled={selectedEntities.size === 0}>
              {isLoading ? 'Importing...' : 'Import'}
            </button>
          </div>
        </fieldset>
      )}

      {step === 'importing' && (
        <fieldset disabled>
          <legend>Importing...</legend>
          <p>Please wait while entities are being imported.</p>
          <progress />
        </fieldset>
      )}
    </form>
  );
}

export default AdvancedElderImport;
```

## Entity Type Mapping

Elder entities are mapped to IceCharts shapes as follows:

| Elder Type | IceCharts Shape | Icon | Color | Hex Code |
|-----------|-----------------|------|-------|----------|
| `compute` | Rectangle | server | Blue | #3B82F6 |
| `vpc` | Rectangle | network | Green | #10B981 |
| `subnet` | Rectangle | share-2 | Indigo | #6366F1 |
| `datacenter` | Rectangle | database | Amber | #F59E0B |
| `network` | Diamond | router | Purple | #8B5CF6 |
| `user` | Circle | user | Pink | #EC4899 |
| `security_issue` | Diamond | alert-triangle | Red | #EF4444 |

## Dependency Type Mapping

Relationships between entities become animated connectors with appropriate labels:

| Dependency Type | Label | Animated |
|-----------------|-------|----------|
| `depends_on` | "depends on" | Yes |
| `hosted_on` | "hosted on" | No |
| `manages` | "manages" | No |
| `connects_to` | "connects to" | Yes |

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

### Backend Configuration

No special configuration needed. The service is lazy-loaded on-demand. All configuration can be passed per-request.

### API Client Configuration

The client uses httpx for async HTTP requests with configurable timeout:

```python
client = ElderClient(
    base_url="https://elder.example.com",
    api_key="api-key",
    timeout=30  # Request timeout in seconds
)
```

### Frontend Configuration

API endpoints are discovered from the Flask backend. No additional configuration needed.

## Direct API Usage Examples

### cURL Examples

```bash
# Validate connection
curl -X POST https://icecharts.example.com/api/v1/elder/validate-connection \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "base_url": "https://elder.example.com",
    "api_key": "api-key"
  }'

# Get entities
curl https://icecharts.example.com/api/v1/elder/entities \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  -d "base_url=https://elder.example.com" \
  -d "api_key=api-key" \
  -d "org_id=1" \
  -d "entity_type=compute"

# Get relationships
curl https://icecharts.example.com/api/v1/elder/relationships \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -G \
  -d "base_url=https://elder.example.com" \
  -d "api_key=api-key" \
  -d "org_id=1"

# Import entities
curl -X POST https://icecharts.example.com/api/v1/elder/import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "drawing_id": "drawing-123",
    "base_url": "https://elder.example.com",
    "api_key": "api-key",
    "org_id": 1,
    "entity_ids": [1, 2, 3],
    "include_dependencies": true,
    "canvas_width": 1600,
    "canvas_height": 900
  }'
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

All endpoints return JSON with `success` boolean:

```json
{
  "success": false,
  "error": "Failed to connect to Elder: Connection refused"
}
```

### Frontend Error Handling

The `useElderImport` hook manages error state:

```typescript
const { error } = useElderImport();

if (error) {
  return <div className="error">{error}</div>;
}
```

The dialog component displays errors inline:

```typescript
{error && <div className="error">{error}</div>}
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

### Performance Tips

1. **Pagination**: Fetch entities in pages for large datasets
2. **Filtering**: Use entity_type filter to reduce payload
3. **Caching**: Store entity lists locally to avoid repeated fetches
4. **Debouncing**: Debounce filter changes to reduce API calls
5. **Lazy Loading**: Load relationships only when needed

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

## Testing

### Unit Test Example

```python
import pytest
from app.services.elder_service import ElderClient, ElderEntity

@pytest.mark.asyncio
async def test_map_entity_to_shape():
    """Test entity to shape mapping."""
    entity = ElderEntity(
        id=1,
        unique_id=12345,
        name="web-server",
        entity_type="compute",
        description="Production server"
    )

    node = ElderClient.map_entity_to_shape(entity, x=100, y=200)

    assert node.id == "elder_1_12345"
    assert node.type == "rectangle"
    assert node.position == {"x": 100, "y": 200}
    assert node.data["label"] == "web-server"
    assert node.data["icon"] == "server"
```

### API Test Template

```bash
curl -X POST http://localhost:5000/api/v1/elder/import \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{...}'
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

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Elder not running/accessible | Check URL and network |
| Invalid API key | Wrong credentials | Verify API key in Elder |
| No entities found | Wrong org ID | Check organization ID |
| Import timeout | Large entity count | Increase timeout or paginate |
| Memory issues | Very large graphs | Process in batches |

**Issue: "Connection refused"**
- Verify Elder URL is accessible
- Check firewall rules
- Ensure Elder service is running

**Issue: "Invalid API key"**
- Verify API key is correct
- Check API key has necessary permissions
- Check API key hasn't expired

**Issue: "No entities found"**
- Verify organization ID is correct
- Check entity exists in Elder
- Try without entity type filter

## Future Enhancements

Potential improvements for the integration:

1. **Bulk Operations**: Import/export multiple drawings
2. **Filtering**: Advanced entity filtering by metadata
3. **Real-time Sync**: Keep drawing synchronized with Elder
4. **Custom Mappings**: User-defined entity-to-shape mappings
5. **Caching**: Cache entities locally to reduce API calls
6. **Webhook Integration**: Automatically update on Elder changes
7. **Batch Import**: Import multiple drawings from templates

## Key Statistics

- **Total Lines of Code**: 1,866
- **Backend Methods**: 11 (ElderClient)
- **API Endpoints**: 6
- **Frontend Components**: 2 (hook + dialog)
- **Entity Types Supported**: 7
- **Dependency Types Supported**: 4+

## Integration Checklist

- [ ] Copy elder_service.py to backend/services/
- [ ] Copy elder.py to backend/api/v1/
- [ ] Update backend/api/v1/__init__.py (register blueprint)
- [ ] Copy useElderImport.ts to frontend/hooks/
- [ ] Copy ElderImportDialog.tsx to frontend/components/drawing/
- [ ] Update frontend/lib/api.ts (add Elder endpoints)
- [ ] Test connection validation
- [ ] Test entity fetching
- [ ] Test import functionality
- [ ] Test with actual Elder instance
- [ ] Deploy to production

## See Also

- [Elder Documentation](https://github.com/penguintechinc/Elder)
- [IceCharts API Documentation](./API.md)
- [Canvas Shapes Reference](./SHAPES.md)
