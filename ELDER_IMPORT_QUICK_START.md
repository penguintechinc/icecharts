# Elder Import Feature - Quick Start Guide

## What Was Added

A complete Elder import UI system that allows users to import infrastructure entities and relationships from an Elder instance directly into IceCharts drawings.

## Key Files Modified/Created

### Modified Files
1. **Toolbar.tsx** - Added Elder import button
2. **Canvas.tsx** - Integrated Elder import dialog
3. **types/index.ts** - Added Elder-specific types

### New Files Created
1. **elderApi.ts** - API utility functions
2. **ELDER_IMPORT_README.md** - Feature documentation
3. **ELDER_IMPORT_IMPLEMENTATION.md** - Implementation summary

### Existing Files (No Changes Needed)
1. **useElderImport.ts** - Hook already had all required functionality
2. **ElderImportDialog.tsx** - Enhanced with success state

## Feature Overview

### User Workflow
```
Click "Import from Elder" button in toolbar
    ↓
Enter Elder connection details
    ↓
Browse and select entities to import
    ↓
Confirm import
    ↓
Entities appear on canvas with automatic layout
```

### What Gets Imported
- Infrastructure entities (compute, vpc, subnet, etc.)
- Dependencies/relationships between entities
- Entity metadata and descriptions
- Automatic layout positioning

## Code Integration Points

### 1. Toolbar Button
Location: `src/components/canvas/Toolbar.tsx`
```typescript
<Toolbar
  onUndo={handleUndo}
  onRedo={handleRedo}
  canUndo={historyIndex > 0}
  canRedo={historyIndex < history.length - 1}
  onAddNode={addNode}
  onElderImport={() => setIsElderDialogOpen(true)}  // NEW
/>
```

### 2. Canvas Integration
Location: `src/components/canvas/Canvas.tsx`
```typescript
// State
const [isElderDialogOpen, setIsElderDialogOpen] = useState(false);

// Handler
const handleElderImport = useCallback(
  (importedNodes: any[], importedConnectors: any[]) => {
    const updatedNodes = [...nodes, ...importedNodes];
    const updatedEdges = [...edges, ...importedConnectors];
    setNodes(updatedNodes);
    setEdges(updatedEdges);
    saveToHistory(updatedNodes, updatedEdges);
    onNodesChange?.(updatedNodes);
    onEdgesChange?.(updatedEdges);
  },
  [nodes, edges, setNodes, setEdges, saveToHistory, onNodesChange, onEdgesChange]
);

// Dialog
<ElderImportDialog
  drawingId="current"
  isOpen={isElderDialogOpen}
  onClose={() => setIsElderDialogOpen(false)}
  onImport={handleElderImport}
/>
```

### 3. API Utilities
Location: `src/lib/elderApi.ts`

Available functions:
```typescript
// Validate connection
validateElderConnection(baseUrl: string, apiKey: string): Promise<boolean>

// Fetch entities
fetchElderEntities(
  baseUrl: string,
  apiKey: string,
  orgId: number,
  entityType?: string,
  limit?: number,
  offset?: number
): Promise<ElderEntity[]>

// Fetch relationships
fetchElderRelationships(
  baseUrl: string,
  apiKey: string,
  orgId: number,
  sourceEntityId?: number,
  targetEntityId?: number
): Promise<ElderRelationship[]>

// Import entities
importElderEntities(
  drawingId: string,
  baseUrl: string,
  apiKey: string,
  orgId: number,
  entityIds: number[],
  includeDependencies?: boolean,
  canvasWidth?: number,
  canvasHeight?: number
): Promise<ImportResult>
```

## TypeScript Types

All types are available in `src/types/index.ts`:

```typescript
// Entity from Elder
interface ElderEntity {
  id: number;
  unique_id: number;
  name: string;
  entity_type: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

// Relationship between entities
interface ElderRelationship {
  id: number;
  source_entity_id: number;
  target_entity_id: number;
  dependency_type: string;
  description?: string;
  strength?: number;
}

// Import result
interface ElderImportResult {
  success: boolean;
  message: string;
  nodes: Node[];
  connectors: Edge[];
  entity_count: number;
  relationship_count: number;
}
```

## Hook Usage

The `useElderImport` hook is available in `src/hooks/useElderImport.ts`:

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

## API Endpoints

All requests go through the backend at `/api/v1/elder/`:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /validate-connection | Validate Elder credentials |
| GET | /entities | Fetch entities |
| GET | /relationships | Fetch relationships |
| GET | /graph | Fetch dependency graph |
| POST | /import | Import entities into drawing |
| GET | /health | Check service health |

## Dialog Steps

1. **Connect** - User provides Elder connection details
2. **Browse/Select** - User selects entities to import
3. **Importing** - Loading state during API call
4. **Success** - Confirmation and auto-close

## Configuration

No additional configuration required. The feature works out of the box once:
1. Flask backend is running with Elder API routes
2. User has valid Elder instance credentials
3. User has appropriate permissions in Elder

## Error Handling

All error scenarios are handled with user-friendly messages:
- Invalid credentials → "Failed to connect to Elder"
- No entities selected → "Please select at least one entity"
- Import failure → Shows error from server
- Network error → Generic connection error message

## Styling

Elder import UI uses scoped CSS classes prefixed with `elder-`:
- Modal overlay and dialog
- Form inputs and labels
- Entity list and items
- Buttons and states
- Success confirmation display

All styles are embedded in the ElderImportDialog component.

## Testing Checklist

- [ ] Import button appears in toolbar
- [ ] Dialog opens when button clicked
- [ ] Connection validation works
- [ ] Entity list loads correctly
- [ ] Entity filtering works
- [ ] Select/deselect works
- [ ] Imported entities appear on canvas
- [ ] Relationships are imported
- [ ] Undo/redo works with imports
- [ ] Error messages display correctly

## Troubleshooting

### Import button doesn't appear
- Check if onElderImport prop is passed to Toolbar
- Verify Canvas component is properly updated

### Dialog doesn't open
- Check if isElderDialogOpen state exists
- Verify onClose callback is implemented

### Entities don't load
- Verify Elder base URL is correct
- Check API key is valid
- Ensure Organization ID is correct
- Check network connectivity

### Imported entities don't appear
- Verify import response includes nodes/connectors
- Check Canvas is properly handling imported data
- Verify history saving is working

## Next Steps

1. **Testing**: Test with actual Elder instance
2. **Deployment**: Deploy updated webui
3. **User Training**: Document feature for end users
4. **Monitoring**: Watch for import errors in logs
5. **Enhancements**: Consider feature requests (preview, batching, etc.)

## Support

For detailed information, see:
- Implementation guide: `ELDER_IMPORT_IMPLEMENTATION.md`
- Feature documentation: `src/components/drawing/ELDER_IMPORT_README.md`
- API reference: `src/lib/elderApi.ts`
- Hook documentation: `src/hooks/useElderImport.ts`

## Performance Notes

- Entities limited to 1000 per fetch
- Import operation is single API call (all at once)
- Auto-layout computed on server side
- No caching of connection details (security)
- Success dialog auto-closes after 2 seconds

## Security Notes

- API keys never logged or stored
- HTTPS required for Elder connection
- All inputs validated on server
- User authentication required (auth_required middleware)
- Clear error messages without revealing system details
