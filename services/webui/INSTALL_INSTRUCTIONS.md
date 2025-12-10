# Canvas Components Installation Instructions

## Required Dependencies

To use the React Flow canvas components, you need to install the following dependency:

```bash
npm install @xyflow/react@^12.0.0
```

## Component Structure

The canvas components have been created at:
```
/home/penguin/code/IceCharts/services/webui/src/components/canvas/
├── Canvas.tsx                    # Main React Flow wrapper component
├── Toolbar.tsx                   # Drawing tools toolbar
├── ShapePanel.tsx                # Left sidebar shape library
├── PropertiesPanel.tsx           # Right sidebar properties panel
├── nodes/
│   ├── ShapeNode.tsx            # Generic shape node (rectangle, circle, diamond, etc.)
│   ├── CloudProviderNode.tsx    # Cloud provider icons (AWS, Azure, GCP, K8s)
│   ├── ContainerNode.tsx        # Grouping container (VPC, subnet, org units)
│   └── TextNode.tsx             # Standalone text element
└── edges/
    └── ConnectorEdge.tsx        # Custom edge with arrows and styling
```

## Features Implemented

### Canvas.tsx
- ✅ useNodesState, useEdgesState hooks
- ✅ Background, Controls, MiniMap
- ✅ Custom node and edge types registration
- ✅ Connection handling
- ✅ Keyboard shortcuts (Delete, Copy, Paste, Undo, Redo)
- ✅ History management (50-step undo/redo)
- ✅ Gold accent colors for selected states

### ShapeNode.tsx
- ✅ Multiple shape types (rectangle, circle, diamond, triangle, hexagon, parallelogram)
- ✅ Resizable handles with NodeResizer
- ✅ Text label editing (double-click to edit)
- ✅ Style props (fill, stroke, strokeWidth, textColor, fontSize)
- ✅ Connection handles on all sides

### CloudProviderNode.tsx
- ✅ Provider icons (AWS, Azure, GCP, Kubernetes, Docker, Terraform, Ansible, Jenkins)
- ✅ SVG icon display with label below
- ✅ Configurable size
- ✅ Connection handles

### ContainerNode.tsx
- ✅ Resizable container for grouping
- ✅ Label at top (editable)
- ✅ Border style options (solid, dashed, dotted)
- ✅ Opacity control
- ✅ Connection handles

### TextNode.tsx
- ✅ Standalone text element
- ✅ Multiline text support (textarea)
- ✅ Resizable
- ✅ Font styling (size, weight, color, alignment)
- ✅ Optional border

### ConnectorEdge.tsx
- ✅ Custom edge styling
- ✅ Arrow markers (none, arrow, circle, diamond)
- ✅ Bidirectional arrows option
- ✅ Label support with floating label renderer
- ✅ Style props (color, width, dash pattern)
- ✅ Gold accent when selected

### Toolbar.tsx
- ✅ Selection and pan modes
- ✅ Shape tools (rectangle, circle, diamond, triangle, hexagon)
- ✅ Text tool
- ✅ Undo/redo buttons
- ✅ Visual feedback for active tools

### ShapePanel.tsx
- ✅ Collapsible categories (Basic, Containers, AWS, Azure, GCP, Kubernetes)
- ✅ Drag to canvas functionality
- ✅ Click to add functionality
- ✅ Visual previews for each shape
- ✅ Expandable/collapsible sections

### PropertiesPanel.tsx
- ✅ Position and size inputs
- ✅ Style controls (fill, stroke, text colors)
- ✅ Font size and weight controls
- ✅ Edge styling (line style, markers, bidirectional)
- ✅ Metadata key/value editor
- ✅ Empty state when nothing selected

## Usage Example

```tsx
import Canvas from './components/canvas/Canvas';

function App() {
  return (
    <div className="h-screen">
      <Canvas />
    </div>
  );
}
```

## Keyboard Shortcuts

- **Delete/Backspace**: Delete selected elements
- **Ctrl/Cmd + C**: Copy selected elements
- **Ctrl/Cmd + V**: Paste copied elements
- **Ctrl/Cmd + Z**: Undo
- **Ctrl/Cmd + Shift + Z** or **Ctrl/Cmd + Y**: Redo
- **Mouse Wheel**: Zoom in/out
- **Double Click**: Edit text on nodes

## Styling Notes

- Gold accent color (#d4af37) is used for selected states
- Tailwind CSS classes are used throughout
- Components use inline styles where dynamic values are needed
- All components are fully typed with TypeScript

## Next Steps

1. Install the @xyflow/react dependency
2. Import and use the Canvas component in your application
3. Customize colors, shapes, and providers as needed
4. Add additional node types or edge types by following the existing patterns
