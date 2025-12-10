# Export Functionality - Quick Start Guide

Fast reference guide for using IceCharts export features.

## Installation

1. **Backend Dependencies**
```bash
# Already added to requirements.txt:
# - Pillow==10.4.0
# - cairosvg==2.7.2
# - WeasyPrint==62.0

pip install -r requirements.txt
```

2. **Frontend Dependencies**
```bash
# Already added to package.json:
# - html2canvas==^1.4.1

cd services/webui
npm install
```

## Using Export Features

### Option 1: React Component (Recommended for UI)

```typescript
import { ExportDialog } from './components/drawing/ExportDialog';
import { useState } from 'react';

function MyDrawing() {
  const [showExport, setShowExport] = useState(false);

  return (
    <>
      <button onClick={() => setShowExport(true)}>
        Export Drawing
      </button>

      <ExportDialog
        drawingId="my_drawing_123"
        drawingName="My Diagram"
        isOpen={showExport}
        onClose={() => setShowExport(false)}
      />
    </>
  );
}
```

### Option 2: Custom Hook (Programmatic Control)

```typescript
import { useExport } from './hooks/useExport';

function MyDrawing() {
  const { loading, error, exportDrawing } = useExport();

  const handleExportPNG = async () => {
    try {
      await exportDrawing('drawing_id', {
        format: 'png',
        width: 1024,
        height: 768,
        quality: 95
      });
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <button onClick={handleExportPNG} disabled={loading}>
      {loading ? 'Exporting...' : 'Export as PNG'}
    </button>
  );
}
```

### Option 3: Export Utilities (Low-level Control)

```typescript
import { downloadSvg, drawingToSvg, validateExportOptions } from './lib/export';

// Validate options
const validation = validateExportOptions({
  format: 'png',
  width: 800
});

if (!validation.valid) {
  console.error(validation.error);
}

// Convert and download
const svgString = drawingToSvg(drawingData, 800, 600);
downloadSvg(svgString, 'my_drawing.svg');
```

## API Endpoints Reference

### Export Drawing

```bash
# PNG
GET /api/v1/drawings/{id}/export/png?width=1024&height=768&quality=95&include_background=true

# SVG
GET /api/v1/drawings/{id}/export/svg

# PDF
GET /api/v1/drawings/{id}/export/pdf?page_size=A4&include_background=true

# JSON
GET /api/v1/drawings/{id}/export/json
```

### Template Management

```bash
# List templates
GET /api/v1/templates?category=custom&search=diagram

# Create template
POST /api/v1/templates
{
  "name": "My Template",
  "description": "Description",
  "category": "custom",
  "drawing_id": "drawing_123",
  "is_public": false
}

# Use template
POST /api/v1/templates/{id}/use
{
  "name": "My Drawing from Template"
}
```

## Drawing Data Format

```python
# Python/Backend format
drawing_data = {
    "id": "drawing_1",
    "name": "My Drawing",
    "width": 800,
    "height": 600,
    "background_color": (255, 255, 255),
    "elements": [
        {
            "type": "rect",
            "x": 10,
            "y": 10,
            "width": 100,
            "height": 100,
            "color": "black",
            "fill": "lightblue"
        },
        {
            "type": "circle",
            "cx": 250,
            "cy": 250,
            "r": 50,
            "color": "red",
            "fill": "pink"
        }
    ]
}
```

## Export Options

### PNG
- **width**: 100-4000 (default 800)
- **height**: 100-4000 (default 600)
- **quality**: 1-100 (default 95)
- **includeBackground**: true/false (default true)

### SVG
- Format: vector image
- No additional options needed
- Editable in design tools

### PDF
- **pageSize**: A0, A1, A2, A3, A4, A5, A6, Letter, Legal, Tabloid, Ledger
- **includeBackground**: true/false (default true)

### JSON
- Preserves all drawing data
- No additional options needed

## Component Props

### ExportDialog
```typescript
interface ExportDialogProps {
  drawingId: string;
  drawingName: string;
  isOpen: boolean;
  onClose: () => void;
}
```

### TemplateGallery
```typescript
interface TemplateGalleryProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTemplate: (template: Template) => void;
}
```

### SaveAsTemplateDialog
```typescript
interface SaveAsTemplateDialogProps {
  drawingId: string;
  drawingName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}
```

## Common Patterns

### Save and Export

```typescript
import { SaveAsTemplateDialog } from './components/drawing/SaveAsTemplateDialog';
import { ExportDialog } from './components/drawing/ExportDialog';
import { useState } from 'react';

function DrawingToolbar({ drawingId, drawingName }) {
  const [showSave, setShowSave] = useState(false);
  const [showExport, setShowExport] = useState(false);

  return (
    <>
      <button onClick={() => setShowSave(true)}>Save as Template</button>
      <button onClick={() => setShowExport(true)}>Export</button>

      <SaveAsTemplateDialog
        drawingId={drawingId}
        drawingName={drawingName}
        isOpen={showSave}
        onClose={() => setShowSave(false)}
      />

      <ExportDialog
        drawingId={drawingId}
        drawingName={drawingName}
        isOpen={showExport}
        onClose={() => setShowExport(false)}
      />
    </>
  );
}
```

### Browse Templates

```typescript
import { TemplateGallery } from './components/drawing/TemplateGallery';
import { useState } from 'react';

function NewDrawingButton() {
  const [showGallery, setShowGallery] = useState(false);

  const handleSelectTemplate = (template) => {
    // Create drawing from template
    createDrawingFromTemplate(template.id);
    setShowGallery(false);
  };

  return (
    <>
      <button onClick={() => setShowGallery(true)}>
        New Drawing from Template
      </button>

      <TemplateGallery
        isOpen={showGallery}
        onClose={() => setShowGallery(false)}
        onSelectTemplate={handleSelectTemplate}
      />
    </>
  );
}
```

### Export Multiple Formats

```typescript
import { useExport } from './hooks/useExport';

function ExportMultiple({ drawingId }) {
  const { exportDrawing } = useExport();

  const handleExportAll = async () => {
    const formats = ['png', 'svg', 'pdf', 'json'];

    for (const format of formats) {
      try {
        await exportDrawing(drawingId, { format });
      } catch (err) {
        console.error(`Export to ${format} failed:`, err);
      }
    }
  };

  return <button onClick={handleExportAll}>Export All Formats</button>;
}
```

## Troubleshooting

### Export Button Not Working
- Check authentication (JWT token)
- Verify drawing ID exists
- Check browser console for errors
- Ensure API is accessible

### PDF Export is Slow
- Reduce drawing complexity
- Use smaller dimensions
- Check server resources
- Consider async processing

### PNG Quality Issues
- Increase quality parameter (up to 95-100)
- Increase resolution (width/height)
- Check background color

### Templates Not Loading
- Verify template IDs exist
- Check user permissions
- Ensure API endpoint is running
- Check network in browser DevTools

## Performance Tips

1. **Client-side Preview**: Use html2canvas for quick previews
2. **Lazy Loading**: Load templates only when needed
3. **Batch Operations**: Group multiple exports
4. **Caching**: Cache template list responses
5. **Async Processing**: Use async/await for UI responsiveness

## Security Checklist

- [ ] All inputs validated before export
- [ ] User authorization verified
- [ ] SVG content sanitized
- [ ] File size limits enforced
- [ ] Rate limiting applied to API
- [ ] Credentials not exposed in responses

## File Locations

- **Export Service**: `/services/flask-backend/app/services/export_service.py`
- **Export Hook**: `/services/webui/src/client/hooks/useExport.ts`
- **Export Dialog**: `/services/webui/src/client/components/drawing/ExportDialog.tsx`
- **Template Gallery**: `/services/webui/src/client/components/drawing/TemplateGallery.tsx`
- **Save Template Dialog**: `/services/webui/src/client/components/drawing/SaveAsTemplateDialog.tsx`
- **Export Utils**: `/services/webui/src/lib/export.ts`
- **Full Documentation**: `/docs/EXPORT_FUNCTIONALITY.md`

## API Authentication

All endpoints require Bearer token:

```typescript
headers: {
  Authorization: `Bearer ${token}`
}
```

Token automatically added by apiClient interceptor.

## Getting Help

1. Check `/docs/EXPORT_FUNCTIONALITY.md` for detailed docs
2. Review implementation in `/EXPORT_IMPLEMENTATION_SUMMARY.md`
3. Check component prop interfaces
4. Review example code in this guide
5. Check browser console for errors

## Next Steps

1. Integrate components into main UI
2. Connect to actual drawing database
3. Test with real drawings
4. Optimize performance
5. Add additional export formats as needed

---

Need more details? See `/docs/EXPORT_FUNCTIONALITY.md`
