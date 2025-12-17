# IceCharts Export Functionality

Comprehensive documentation for exporting IceCharts drawings to various formats.

## Quick Start

Fast reference guide for using IceCharts export features.

### Installation

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

### Using Export Features

#### Option 1: React Component (Recommended for UI)

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

#### Option 2: Custom Hook (Programmatic Control)

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

#### Option 3: Export Utilities (Low-level Control)

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

### Export Options

#### PNG
- **width**: 100-4000 (default 800)
- **height**: 100-4000 (default 600)
- **quality**: 1-100 (default 95)
- **includeBackground**: true/false (default true)

#### SVG
- Format: vector image
- No additional options needed
- Editable in design tools

#### PDF
- **pageSize**: A0, A1, A2, A3, A4, A5, A6, Letter, Legal, Tabloid, Ledger
- **includeBackground**: true/false (default true)

#### JSON
- Preserves all drawing data
- No additional options needed

### API Quick Reference

```bash
# PNG Export
GET /api/v1/drawings/{id}/export/png?width=1024&height=768&quality=95&include_background=true

# SVG Export
GET /api/v1/drawings/{id}/export/svg

# PDF Export
GET /api/v1/drawings/{id}/export/pdf?page_size=A4&include_background=true

# JSON Export
GET /api/v1/drawings/{id}/export/json
```

### Common Patterns

#### Save and Export

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

#### Export Multiple Formats

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

## Overview

The IceCharts export system provides multiple export formats for drawings:
- **PNG**: Raster image format with configurable resolution and quality
- **SVG**: Vector image format for scalable graphics
- **PDF**: Portable document format for printing and sharing
- **JSON**: Data format for backup and interchange

## Backend Implementation

### Export Service

Location: `/services/flask-backend/app/services/export_service.py`

The `ExportService` class provides static methods for exporting drawings:

```python
from app.services.export_service import ExportService, ExportOptions

# Export to PNG
png_bytes = ExportService.export_to_png(
    drawing_data,
    width=800,
    height=600,
    quality=95,
    include_background=True
)

# Export to SVG
svg_string = ExportService.export_to_svg(drawing_data)

# Export to PDF
pdf_bytes = ExportService.export_to_pdf(
    drawing_data,
    page_size="A4",
    include_background=True
)

# Export to JSON
json_string = ExportService.export_to_json(drawing_data)

# Using ExportOptions
options = ExportOptions(
    format="png",
    width=1024,
    height=768,
    quality=90,
    dpi=300,
    page_size="A4",
    include_background=True
)
result = ExportService.export(options, drawing_data)
```

### API Endpoints

#### Drawing Export Endpoints

**GET** `/api/v1/drawings/{drawing_id}/export/png`

Export drawing as PNG image.

Query parameters:
- `width` (int, default: 800): Image width in pixels
- `height` (int, default: 600): Image height in pixels
- `quality` (int, default: 95): PNG compression quality (1-100)
- `include_background` (boolean, default: true): Include background

Response: PNG image file

**GET** `/api/v1/drawings/{drawing_id}/export/svg`

Export drawing as SVG vector image.

Response: SVG file

**GET** `/api/v1/drawings/{drawing_id}/export/pdf`

Export drawing as PDF document.

Query parameters:
- `page_size` (string, default: "A4"): PDF page size
  - Valid values: A0, A1, A2, A3, A4, A5, A6, Letter, Legal, Tabloid, Ledger
- `include_background` (boolean, default: true): Include background

Response: PDF file

**GET** `/api/v1/drawings/{drawing_id}/export/json`

Export drawing as JSON data.

Response: JSON file

### Drawing Data Structure

Drawings can be represented as either a dictionary or SVG string:

```python
# Dictionary format
drawing_data = {
    "id": "drawing_1",
    "name": "My Drawing",
    "width": 800,
    "height": 600,
    "background_color": (255, 255, 255),
    "include_background": True,
    "elements": [
        {
            "type": "rect",
            "x": 10,
            "y": 10,
            "width": 100,
            "height": 100,
            "color": "black",
            "fill": "lightblue",
            "stroke_width": 2
        },
        {
            "type": "circle",
            "cx": 250,
            "cy": 250,
            "r": 50,
            "color": "red",
            "fill": "pink",
            "stroke_width": 1
        },
        {
            "type": "line",
            "x1": 0,
            "y1": 0,
            "x2": 800,
            "y2": 600,
            "color": "green",
            "stroke_width": 2
        },
        {
            "type": "text",
            "x": 400,
            "y": 300,
            "text": "Hello World",
            "color": "blue",
            "font_size": 24
        }
    ]
}

# SVG format
svg_string = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
    <rect width="800" height="600" fill="rgb(255,255,255)"/>
    <!-- SVG elements -->
</svg>"""
```

### Supported Element Types

- **rect**: Rectangle shape
  - Properties: x, y, width, height, color, fill, stroke_width
- **circle**: Circle shape
  - Properties: cx, cy, r, color, fill, stroke_width
- **line**: Line shape
  - Properties: x1, y1, x2, y2, color, stroke_width
- **text**: Text element
  - Properties: x, y, text, color, font_size

## Frontend Implementation

### Export Hook

Location: `/services/webui/src/client/hooks/useExport.ts`

```typescript
import { useExport } from '../../hooks/useExport';

function MyComponent() {
  const { loading, error, success, exportDrawing } = useExport();

  const handleExport = async () => {
    try {
      await exportDrawing('drawing_id', {
        format: 'png',
        width: 1024,
        height: 768,
        quality: 95,
        includeBackground: true
      });
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div>
      {loading && <p>Exporting...</p>}
      {error && <p>Error: {error}</p>}
      {success && <p>Export successful!</p>}
      <button onClick={handleExport}>Export Drawing</button>
    </div>
  );
}
```

### Export Dialog Component

Location: `/services/webui/src/client/components/drawing/ExportDialog.tsx`

Modal dialog for exporting drawings with format selection and options.

```typescript
import { ExportDialog } from './ExportDialog';
import { useState } from 'react';

function DrawingEditor() {
  const [showExportDialog, setShowExportDialog] = useState(false);

  return (
    <>
      <button onClick={() => setShowExportDialog(true)}>
        Export Drawing
      </button>
      <ExportDialog
        drawingId="drawing_1"
        drawingName="My Drawing"
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
      />
    </>
  );
}
```

#### Component Props

```typescript
interface ExportDialogProps {
  drawingId: string;
  drawingName: string;
  isOpen: boolean;
  onClose: () => void;
}
```

### Export Utilities

Location: `/services/webui/src/lib/export.ts`

Utility functions for client-side export operations:

```typescript
import {
  createCanvasPreview,
  canvasToDataUrl,
  downloadBlob,
  downloadJson,
  downloadSvg,
  drawingToSvg,
  validateExportOptions,
  getExtensionForFormat,
  getMimeTypeForFormat
} from '../../lib/export';

// Create preview from canvas element
const canvas = document.getElementById('drawing-canvas');
const preview = await createCanvasPreview(canvas, 800, 600);

// Convert drawing to SVG
const svgString = drawingToSvg(drawingData, 800, 600);

// Download SVG
downloadSvg(svgString, 'drawing.svg');

// Validate options before export
const validation = validateExportOptions({
  format: 'png',
  width: 800,
  height: 600
});
```

## Templates System

### Template Endpoints

**GET** `/api/v1/templates`

List available templates with optional filtering.

Query parameters:
- `category` (string): Filter by category
- `search` (string): Search templates by name

**GET** `/api/v1/templates/{template_id}`

Get specific template details and content.

**POST** `/api/v1/templates`

Create a new template from a drawing.

Request body:
```json
{
  "name": "My Template",
  "description": "Template description",
  "category": "custom",
  "drawing_id": "drawing_id",
  "is_public": false
}
```

**POST** `/api/v1/templates/{template_id}/use`

Create a new drawing from a template.

Request body:
```json
{
  "name": "New Drawing from Template",
  "description": "Optional description"
}
```

### Template Gallery Component

Location: `/services/webui/src/client/components/drawing/TemplateGallery.tsx`

Browse and select templates from a gallery.

```typescript
import { TemplateGallery } from './TemplateGallery';
import { useState } from 'react';

function DrawingSelector() {
  const [showGallery, setShowGallery] = useState(false);

  const handleSelectTemplate = (template) => {
    // Create drawing from template
    console.log('Selected template:', template);
  };

  return (
    <>
      <button onClick={() => setShowGallery(true)}>
        Browse Templates
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

#### Component Props

```typescript
interface TemplateGalleryProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTemplate: (template: Template) => void;
}
```

### Save as Template Dialog

Location: `/services/webui/src/client/components/drawing/SaveAsTemplateDialog.tsx`

Save current drawing as a reusable template.

```typescript
import { SaveAsTemplateDialog } from './SaveAsTemplateDialog';
import { useState } from 'react';

function DrawingEditor() {
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  return (
    <>
      <button onClick={() => setShowSaveDialog(true)}>
        Save as Template
      </button>
      <SaveAsTemplateDialog
        drawingId="drawing_1"
        drawingName="My Drawing"
        isOpen={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        onSuccess={() => {
          console.log('Template saved successfully');
        }}
      />
    </>
  );
}
```

#### Component Props

```typescript
interface SaveAsTemplateDialogProps {
  drawingId: string;
  drawingName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}
```

#### Template Management Quick Reference

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

## Dependencies

### Backend Dependencies

Add to `requirements.txt`:

```
Pillow==10.4.0          # Image manipulation
cairosvg==2.7.2         # SVG to PNG rendering
WeasyPrint==62.0        # HTML/CSS to PDF conversion
```

### Frontend Dependencies

Add to `package.json`:

```json
{
  "html2canvas": "^1.4.1"
}
```

## Usage Examples

### Export Drawing to PNG

```python
# Backend
from app.services.export_service import ExportService

drawing_data = {
    "width": 800,
    "height": 600,
    "elements": [...]
}

png_bytes = ExportService.export_to_png(
    drawing_data,
    width=1024,
    height=768,
    quality=95
)

# Return as response
return send_file(
    io.BytesIO(png_bytes),
    mimetype="image/png",
    as_attachment=True,
    download_name="drawing.png"
)
```

```typescript
// Frontend
const { exportDrawing } = useExport();

await exportDrawing('drawing_1', {
  format: 'png',
  width: 1024,
  height: 768,
  quality: 95
});
```

### Export Drawing to PDF

```python
# Backend
pdf_bytes = ExportService.export_to_pdf(
    drawing_data,
    page_size="A4",
    include_background=True
)

return send_file(
    io.BytesIO(pdf_bytes),
    mimetype="application/pdf",
    as_attachment=True,
    download_name="drawing.pdf"
)
```

### Create Drawing from Template

```python
# Backend
# Load template
template = get_template_by_id(template_id)

# Create drawing from template data
new_drawing = {
    "name": request.json.get("name"),
    "content": template.content,
    "width": template.width,
    "height": template.height
}

# Save drawing
drawing_id = save_drawing(new_drawing)

return jsonify({
    "success": True,
    "drawing": new_drawing,
    "id": drawing_id
})
```

```typescript
// Frontend
const response = await apiClient.post(
  `/v1/templates/${templateId}/use`,
  {
    name: "My Drawing from Template",
    description: "Created from template"
  }
);

const newDrawing = response.data.drawing;
```

## Error Handling

### Backend

All export methods raise exceptions on errors:

```python
try:
    png_bytes = ExportService.export_to_png(drawing_data)
except ValueError as e:
    # Invalid options or data
    return jsonify({"error": str(e)}), 400
except Exception as e:
    # Export process failed
    return jsonify({"error": str(e)}), 500
```

### Frontend

The `useExport` hook handles errors:

```typescript
const { error, exportDrawing } = useExport();

try {
  await exportDrawing('drawing_1', options);
} catch (err) {
  console.error('Export error:', err);
  // Error is also available in hook state
  if (error) {
    showErrorMessage(error);
  }
}
```

## Performance Considerations

- **PNG Export**: Use quality setting 70-85 for web, 95 for print
- **PDF Export**: WeasyPrint rendering can be CPU-intensive for large drawings
- **SVG Export**: Lightweight, recommended for further editing
- **Large drawings**: Consider splitting into multiple exports
- **Client-side Preview**: Use html2canvas for quick previews
- **Lazy Loading**: Load templates only when needed
- **Batch Operations**: Group multiple exports
- **Caching**: Cache template list responses
- **Async Processing**: Use async/await for UI responsiveness

## Security Considerations

- Validate all user input in export options
- Limit maximum dimensions (4000x4000 pixels)
- Restrict export to authorized users only
- Sanitize SVG content to prevent XSS
- Rate-limit export API endpoints
- All inputs validated before export
- User authorization verified
- SVG content sanitized
- File size limits enforced
- Credentials not exposed in responses

### API Authentication

All endpoints require Bearer token:

```typescript
headers: {
  Authorization: `Bearer ${token}`
}
```

Token automatically added by apiClient interceptor.

## Troubleshooting

### Export Button Not Working
- Check authentication (JWT token)
- Verify drawing ID exists
- Check browser console for errors
- Ensure API is accessible

### PNG Export Fails

Check:
- Image dimensions are valid (100-4000px)
- Cairo/cairosvg is properly installed
- System has sufficient memory

### PNG Quality Issues
- Increase quality parameter (up to 95-100)
- Increase resolution (width/height)
- Check background color

### PDF Export Slow

- Reduce drawing complexity
- Use smaller dimensions
- Check server CPU/memory
- Consider async processing

### SVG Export Issues

- Ensure all elements have required properties
- Validate SVG with online validators
- Check browser SVG support

### Templates Not Loading

- Verify template IDs exist in database
- Check user permissions
- Ensure API endpoint is accessible
- Check network in browser DevTools

## File Locations

- **Export Service**: `/services/flask-backend/app/services/export_service.py`
- **Export Hook**: `/services/webui/src/client/hooks/useExport.ts`
- **Export Dialog**: `/services/webui/src/client/components/drawing/ExportDialog.tsx`
- **Template Gallery**: `/services/webui/src/client/components/drawing/TemplateGallery.tsx`
- **Save Template Dialog**: `/services/webui/src/client/components/drawing/SaveAsTemplateDialog.tsx`
- **Export Utils**: `/services/webui/src/lib/export.ts`

## Future Enhancements

- Batch export multiple drawings
- Custom export presets/profiles
- Cloud storage integration (Google Drive, Dropbox)
- Export history and versioning
- Email export functionality
- Advanced PDF options (bookmarks, metadata)
- Watermark support
- Export scheduling/automation
