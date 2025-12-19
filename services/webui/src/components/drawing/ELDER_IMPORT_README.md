# Elder Import Integration

This document describes the Elder import functionality in IceCharts, which enables users to import infrastructure entities and relationships from an Elder instance directly into IceCharts drawings.

## Overview

The Elder import feature provides a seamless workflow to:
1. Connect to an Elder instance with credentials
2. Browse and filter available entities
3. Select specific entities and relationships to import
4. Import them as nodes and connectors into the current drawing
5. Automatically layout imported entities on the canvas

## Components

### ElderImportDialog.tsx
Main modal dialog component that manages the complete import workflow.

**Features:**
- Multi-step dialog (Connect → Browse → Select → Importing → Success)
- Connection validation with error handling
- Entity listing with filtering by type
- Select all/deselect functionality
- Dependency inclusion option
- Visual import status and success confirmation

**Props:**
```typescript
interface ElderImportDialogProps {
  drawingId: string;              // Target drawing ID
  isOpen: boolean;                // Dialog visibility state
  onClose: () => void;            // Callback when dialog closes
  onImport: (nodes: unknown[], connectors: unknown[]) => void; // Import callback
}
```

**Usage:**
```typescript
<ElderImportDialog
  drawingId="drawing-123"
  isOpen={isElderDialogOpen}
  onClose={() => setIsElderDialogOpen(false)}
  onImport={(nodes, connectors) => handleImport(nodes, connectors)}
/>
```

## Hooks

### useElderImport()

Custom hook providing Elder API integration logic.

**State:**
- `isLoading: boolean` - Loading state during API calls
- `error: string | null` - Error message if any
- `entities: ElderEntity[]` - Fetched entities from Elder
- `selectedEntities: Set<number>` - IDs of selected entities
- `isConnected: boolean` - Connection status

**Methods:**
- `validateConnection(baseUrl: string, apiKey: string): Promise<boolean>` - Validate Elder credentials
- `fetchEntities(baseUrl, apiKey, orgId, entityType?): Promise<ElderEntity[]>` - Fetch entities
- `fetchRelationships(baseUrl, apiKey, orgId, sourceId?, targetId?): Promise<ElderRelationship[]>` - Fetch relationships
- `toggleEntitySelection(entityId: number): void` - Toggle entity selection
- `toggleSelectAll(): void` - Select/deselect all visible entities
- `importEntities(drawingId, includeDependencies?, canvasWidth?, canvasHeight?): Promise<ImportResult | null>` - Execute import
- `reset(): void` - Clear all state

**Example:**
```typescript
const {
  isLoading,
  error,
  entities,
  selectedEntities,
  validateConnection,
  fetchEntities,
  importEntities,
  toggleEntitySelection,
  reset,
} = useElderImport();
```

## API Utilities

### lib/elderApi.ts

Utility functions for Elder API interactions.

**Functions:**

#### validateElderConnection(baseUrl: string, apiKey: string): Promise<boolean>
Validates connection to an Elder instance.

```typescript
const isValid = await validateElderConnection('https://elder.example.com', 'api-key');
```

#### fetchElderEntities(baseUrl, apiKey, orgId, entityType?, limit?, offset?): Promise<ElderEntity[]>
Fetches entities from Elder with optional filtering.

```typescript
const entities = await fetchElderEntities(
  'https://elder.example.com',
  'api-key',
  1,
  'compute',  // optional: filter by type
  100,        // limit
  0           // offset
);
```

#### fetchElderRelationships(baseUrl, apiKey, orgId, sourceId?, targetId?): Promise<ElderRelationship[]>
Fetches relationships/dependencies from Elder.

```typescript
const relationships = await fetchElderRelationships(
  'https://elder.example.com',
  'api-key',
  1
);
```

#### fetchElderGraph(baseUrl, apiKey, orgId, entityId?, depth?): Promise<any>
Fetches dependency graph from Elder.

```typescript
const graph = await fetchElderGraph(
  'https://elder.example.com',
  'api-key',
  1,
  123,  // optional: start from entity
  2     // depth
);
```

#### importElderEntities(drawingId, baseUrl, apiKey, orgId, entityIds, includeDependencies?, canvasWidth?, canvasHeight?): Promise<ImportResult>
Imports entities into a drawing.

```typescript
const result = await importElderEntities(
  'drawing-123',
  'https://elder.example.com',
  'api-key',
  1,
  [1, 2, 3],        // entity IDs
  true,             // include dependencies
  1600,             // canvas width
  900               // canvas height
);
```

#### checkElderHealth(): Promise<boolean>
Checks if Elder service is healthy.

```typescript
const isHealthy = await checkElderHealth();
```

## Types

### ElderEntity
Represents an infrastructure entity from Elder.

```typescript
interface ElderEntity {
  id: number;
  unique_id: number;
  name: string;
  entity_type: string;
  description?: string;
  metadata?: Record<string, unknown>;
  owner_id?: number;
  organization_id?: number;
}
```

### ElderRelationship
Represents a dependency/relationship between entities.

```typescript
interface ElderRelationship {
  id: number;
  source_entity_id: number;
  target_entity_id: number;
  dependency_type: string;
  description?: string;
  strength?: number;
}
```

### ElderImportRequest
Request body for import operation.

```typescript
interface ElderImportRequest {
  drawing_id: string;
  base_url: string;
  api_key: string;
  org_id: number;
  entity_ids: number[];
  include_dependencies?: boolean;
  canvas_width?: number;
  canvas_height?: number;
}
```

### ElderImportResult
Result of successful import operation.

```typescript
interface ElderImportResult {
  success: boolean;
  message: string;
  nodes: Node[];
  connectors: Edge[];
  entity_count: number;
  relationship_count: number;
}
```

## Integration with Canvas

The Elder import dialog is integrated into the Canvas component through:

1. **Toolbar Button**: Added to the Toolbar component as an import icon button
2. **State Management**: Canvas component manages dialog open/close state
3. **Import Handler**: `handleElderImport()` callback adds nodes and edges to the canvas
4. **History Tracking**: Imported entities are added to undo/redo history

```typescript
// In Canvas.tsx
const [isElderDialogOpen, setIsElderDialogOpen] = useState(false);

const handleElderImport = useCallback(
  (importedNodes: any[], importedConnectors: any[]) => {
    const updatedNodes = [...nodes, ...importedNodes];
    const updatedEdges = [...edges, ...importedConnectors];
    setNodes(updatedNodes);
    setEdges(updatedEdges);
    saveToHistory(updatedNodes, updatedEdges);
  },
  [nodes, edges, setNodes, setEdges, saveToHistory]
);

// In Toolbar
<Toolbar
  onElderImport={() => setIsElderDialogOpen(true)}
  // ... other props
/>

// Dialog
<ElderImportDialog
  drawingId="current"
  isOpen={isElderDialogOpen}
  onClose={() => setIsElderDialogOpen(false)}
  onImport={handleElderImport}
/>
```

## Workflow

### Connection Step
1. User enters Elder instance URL, API key, and Organization ID
2. Clicking "Connect" validates credentials via `/elder/validate-connection`
3. On success, proceeds to Browse step
4. On failure, displays error message

### Browse/Select Step
1. Available entities are fetched from Elder
2. User can filter entities by type
3. Select individual entities or "Select All"
4. Toggle "Include relationships/dependencies" option
5. Clicking "Import" proceeds to Importing step

### Importing Step
1. Shows loading spinner
2. Calls `/elder/import` API endpoint with selected entities
3. API returns nodes and connectors in IceCharts format
4. Automatically proceeds to Success step

### Success Step
1. Displays success message with entity count
2. Auto-closes after 2 seconds
3. Imported entities and relationships appear on canvas

## Error Handling

The component handles various error scenarios:

- **Connection Errors**: Displays validation error message
- **Missing Fields**: Alerts user to fill required fields
- **API Errors**: Displays error message from server
- **Empty Selection**: Alerts user to select at least one entity
- **No Entities Found**: Shows empty state message

## Styling

The dialog uses scoped CSS with class names prefixed with `elder-` to avoid conflicts:
- `.elder-import-dialog-overlay` - Modal overlay
- `.elder-import-dialog` - Dialog container
- `.elder-dialog-header` - Header section
- `.elder-dialog-content` - Content area
- `.elder-step` - Individual step container
- `.elder-entity-list` - Entity list container
- `.elder-entity-item` - Individual entity item
- `.elder-button-primary` - Primary action button
- `.elder-button-secondary` - Secondary action button
- `.elder-success-container` - Success state display
- Various utility classes for inputs, labels, errors, etc.

## API Endpoints Used

### POST /api/v1/elder/validate-connection
Validates Elder instance credentials.

**Request:**
```json
{
  "base_url": "https://elder.example.com",
  "api_key": "your-api-key"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection to Elder validated successfully"
}
```

### GET /api/v1/elder/entities
Fetches entities from Elder.

**Query Parameters:**
- `base_url` - Elder instance URL
- `api_key` - Elder API key
- `org_id` - Organization ID
- `entity_type` - Optional: Filter by type
- `limit` - Optional: Max results (default: 100)
- `offset` - Optional: Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "entities": [...],
  "total": 50
}
```

### GET /api/v1/elder/relationships
Fetches relationships from Elder.

**Query Parameters:**
- `base_url` - Elder instance URL
- `api_key` - Elder API key
- `org_id` - Organization ID

**Response:**
```json
{
  "success": true,
  "relationships": [...],
  "total": 30
}
```

### POST /api/v1/elder/import
Imports Elder entities into a drawing.

**Request:**
```json
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
```

**Response:**
```json
{
  "success": true,
  "message": "Imported 3 entities and 5 relationships",
  "nodes": [...],
  "connectors": [...],
  "entity_count": 3,
  "relationship_count": 5
}
```

## Security Considerations

1. **API Keys**: Never exposed in logs or UI after submission
2. **HTTPS**: Always use HTTPS for Elder instance URLs
3. **Authentication**: Requires user authentication via auth_required middleware
4. **Input Validation**: All inputs validated on client and server side

## Future Enhancements

- Async import with job status tracking
- Import preview/visualization before confirmation
- Batch entity filtering and multi-select improvements
- Import templates and saved configurations
- Incremental import updates
- Conflict resolution for duplicate entities
- Custom entity type mappings
- Import progress tracking for large datasets
