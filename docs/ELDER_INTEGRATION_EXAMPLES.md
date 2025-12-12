# Elder Integration - Usage Examples

Complete examples for using the Elder API integration in IceCharts.

## Backend Examples

### Python - Direct Service Usage

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

### Flask Route - Complete Import

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

## Frontend Examples

### React - Using the Hook

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

### React - Using the Dialog Component

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

### React - Advanced Form with Validation

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

## API Usage Examples

### Direct API Calls

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

## Performance Tips

1. **Pagination**: For large entity lists, fetch in pages
2. **Filtering**: Use entity type filters to reduce payload
3. **Caching**: Cache entity lists locally when possible
4. **Debouncing**: Debounce filter changes to avoid repeated requests
5. **Lazy Loading**: Load related data on demand

## Common Issues and Solutions

### Issue: "Connection refused"
- Verify Elder URL is accessible
- Check firewall rules
- Ensure Elder service is running

### Issue: "Invalid API key"
- Verify API key is correct
- Check API key has necessary permissions
- Check API key hasn't expired

### Issue: "No entities found"
- Verify organization ID is correct
- Check entity exists in Elder
- Try without entity type filter
