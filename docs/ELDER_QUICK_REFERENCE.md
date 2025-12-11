# Elder Integration - Quick Reference

Quick reference guide for the Elder API integration in IceCharts.

## Files Overview

| File | Location | Lines | Purpose |
|------|----------|-------|---------|
| **elder_service.py** | `services/flask-backend/app/services/` | 481 | Core API client and mapping logic |
| **elder.py** | `services/flask-backend/app/api/v1/` | 356 | REST API endpoints |
| **useElderImport.ts** | `services/webui/src/hooks/` | 377 | React hook for import workflow |
| **ElderImportDialog.tsx** | `services/webui/src/components/drawing/` | 652 | Modal dialog component |
| **ELDER_INTEGRATION.md** | `docs/` | - | Complete documentation |
| **ELDER_INTEGRATION_EXAMPLES.md** | `docs/` | - | Code examples and usage patterns |

## Backend API

### Endpoints

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

### Key Methods

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

## Frontend API

### Hook Usage

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

### Dialog Usage

```typescript
<ElderImportDialog
  drawingId={id}
  isOpen={true}
  onClose={() => {}}
  onImport={(nodes, connectors) => {}}
/>
```

## Request/Response Examples

### Validate Connection

```bash
POST /api/v1/elder/validate-connection
Authorization: Bearer token
Content-Type: application/json

{
  "base_url": "https://elder.example.com",
  "api_key": "your-key"
}

# Response 200
{
  "success": true,
  "message": "Connection to Elder validated successfully"
}
```

### Get Entities

```bash
GET /api/v1/elder/entities?base_url=https://elder.example.com&api_key=xxx&org_id=1

# Response 200
{
  "success": true,
  "entities": [
    {
      "id": 1,
      "unique_id": 12345,
      "name": "web-server-01",
      "entity_type": "compute",
      "description": "...",
      "metadata": {}
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

### Import Entities

```bash
POST /api/v1/elder/import
Authorization: Bearer token
Content-Type: application/json

{
  "drawing_id": "drawing-123",
  "base_url": "https://elder.example.com",
  "api_key": "key",
  "org_id": 1,
  "entity_ids": [1, 2, 3],
  "include_dependencies": true,
  "canvas_width": 1600,
  "canvas_height": 900
}

# Response 200
{
  "success": true,
  "message": "Imported 3 entities and 2 relationships",
  "nodes": [
    {
      "id": "elder_1_12345",
      "type": "rectangle",
      "position": {"x": 100, "y": 100},
      "data": {
        "label": "web-server-01",
        "icon": "server",
        "elder_type": "compute",
        "metadata": {}
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
      "source": "elder_1_12345",
      "target": "elder_2_67890",
      "type": "default",
      "animated": true,
      "label": "depends on"
    }
  ],
  "entity_count": 3,
  "relationship_count": 2
}
```

## Entity Type to Shape Mapping

| Entity Type | Shape | Icon | Color | Animated |
|------------|-------|------|-------|----------|
| compute | rectangle | server | #3B82F6 | - |
| vpc | rectangle | network | #10B981 | - |
| subnet | rectangle | share-2 | #6366F1 | - |
| datacenter | rectangle | database | #F59E0B | - |
| network | diamond | router | #8B5CF6 | - |
| user | circle | user | #EC4899 | - |
| security_issue | diamond | alert-triangle | #EF4444 | - |

## Dependency Type to Connector Mapping

| Dependency Type | Label | Animated |
|-----------------|-------|----------|
| depends_on | depends on | Yes |
| hosted_on | hosted on | No |
| manages | manages | No |
| connects_to | connects to | Yes |

## Common Usage Patterns

### Python - Simple Import

```python
from app.services.elder_service import ElderClient

async def import_entities():
    client = ElderClient(
        base_url="https://elder.example.com",
        api_key="api-key"
    )

    entities = await client.get_entities(org_id=1)
    deps = await client.get_relationships(org_id=1)

    nodes = [
        ElderClient.map_entity_to_shape(e, x=0, y=0)
        for e in entities
    ]

    return nodes
```

### TypeScript - Import with Hook

```typescript
import { useElderImport } from '@/hooks/useElderImport';

function MyComponent() {
  const {
    validateConnection,
    fetchEntities,
    importEntities,
  } = useElderImport();

  const handleImport = async () => {
    await validateConnection(url, key);
    await fetchEntities(url, key, orgId);
    const result = await importEntities(drawingId);
    // Use result.nodes and result.connectors
  };

  return <button onClick={handleImport}>Import</button>;
}
```

### React - Using Dialog

```typescript
<ElderImportDialog
  drawingId="drawing-123"
  isOpen={showDialog}
  onClose={() => setShowDialog(false)}
  onImport={(nodes, connectors) => {
    // Add to canvas
    canvas.addNodes(nodes);
    canvas.addConnectors(connectors);
  }}
/>
```

## Configuration

### Backend

No special configuration needed. The service is lazy-loaded on-demand.

Optional environment variables (all can be passed per-request):
```bash
ELDER_BASE_URL=https://elder.example.com
ELDER_API_KEY=your-api-key
ELDER_ORG_ID=1
```

### Frontend

API endpoints are discovered from the Flask backend. No additional configuration needed.

## Error Handling

### Backend

All endpoints return JSON with `success` boolean:

```json
{
  "success": false,
  "error": "Failed to connect to Elder: Connection refused"
}
```

### Frontend Hook

The hook stores errors in state:

```typescript
const { error } = useElderImport();

if (error) {
  // Display error to user
}
```

### Dialog Component

Errors are displayed inline in the dialog:

```typescript
{error && <div className="error">{error}</div>}
```

## Performance Tips

1. **Pagination**: Fetch entities in pages for large datasets
2. **Filtering**: Use entity_type filter to reduce payload
3. **Caching**: Store entity lists locally to avoid repeated fetches
4. **Debouncing**: Debounce filter changes to reduce API calls
5. **Lazy Loading**: Load relationships only when needed

## Testing

### Unit Test Template

```python
@pytest.mark.asyncio
async def test_map_entity_to_shape():
    entity = ElderEntity(
        id=1, unique_id=123, name="test",
        entity_type="compute"
    )
    node = ElderClient.map_entity_to_shape(entity, x=0, y=0)
    assert node.type == "rectangle"
```

### API Test Template

```bash
curl -X POST http://localhost:5000/api/v1/elder/import \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Elder not running/accessible | Check URL and network |
| Invalid API key | Wrong credentials | Verify API key in Elder |
| No entities found | Wrong org ID | Check organization ID |
| Import timeout | Large entity count | Increase timeout or paginate |
| Memory issues | Very large graphs | Process in batches |

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

## Documentation

- **Full Integration Guide**: `/home/penguin/code/IceCharts/docs/ELDER_INTEGRATION.md`
- **Code Examples**: `/home/penguin/code/IceCharts/docs/ELDER_INTEGRATION_EXAMPLES.md`
- **Implementation Summary**: `/home/penguin/code/IceCharts/ELDER_INTEGRATION_SUMMARY.md`
- **This Quick Reference**: `/home/penguin/code/IceCharts/ELDER_QUICK_REFERENCE.md`
