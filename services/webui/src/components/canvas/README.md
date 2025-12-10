# IceCharts Canvas Components

A comprehensive set of React Flow-based canvas components for creating infrastructure and architecture diagrams.

## Installation

```bash
cd /home/penguin/code/IceCharts/services/webui
npm install @xyflow/react@^12.0.0
```

## Quick Start

```tsx
import { Canvas } from './components/canvas';

function DiagramEditor() {
  return (
    <div className="h-screen w-screen">
      <Canvas />
    </div>
  );
}
```

## Component Architecture

### Main Components

#### Canvas.tsx
The main React Flow wrapper that orchestrates all other components.

**Features:**
- Node and edge state management
- Undo/redo history (50 steps)
- Keyboard shortcuts (delete, copy, paste, undo, redo)
- Connection handling
- Selection management
- Integrated toolbar, shape panel, and properties panel

**Props:**
```typescript
interface CanvasProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
}
```

#### Toolbar.tsx
Top toolbar with drawing tools and actions.

**Features:**
- Select/pan mode switching
- Quick shape creation buttons
- Text tool
- Undo/redo controls
- Visual feedback for active tools

#### ShapePanel.tsx
Left sidebar with draggable/clickable shape library.

**Features:**
- Collapsible categories
- Drag-to-canvas support
- Click-to-add support
- Categories: Basic Shapes, Containers, AWS, Azure, GCP, Kubernetes

#### PropertiesPanel.tsx
Right sidebar for editing selected element properties.

**Features:**
- Position and size controls
- Style controls (colors, borders, fonts)
- Edge styling (markers, line styles)
- Metadata key-value editor
- Empty state when nothing selected

### Node Types

#### ShapeNode.tsx
Generic geometric shapes with customizable styling.

**Supported Shapes:**
- Rectangle
- Circle
- Diamond
- Triangle
- Hexagon
- Parallelogram

**Features:**
- Resizable with handles
- Double-click to edit label
- Customizable fill, stroke, and text colors
- Connection handles on all four sides

**Data Interface:**
```typescript
interface ShapeNodeData {
  label: string;
  shapeType: 'rectangle' | 'circle' | 'diamond' | 'triangle' | 'hexagon' | 'parallelogram';
  width?: number;
  height?: number;
  fillColor?: string;
  strokeColor?: string;
  strokeWidth?: number;
  textColor?: string;
  fontSize?: number;
}
```

#### CloudProviderNode.tsx
Pre-configured nodes with cloud provider and DevOps tool icons.

**Supported Providers:**
- AWS (Amazon Web Services)
- Azure (Microsoft Azure)
- GCP (Google Cloud Platform)
- Kubernetes
- Docker
- Terraform
- Ansible
- Jenkins

**Features:**
- SVG-based icons with accurate branding colors
- Configurable size
- Optional label below icon
- Connection handles

**Data Interface:**
```typescript
interface CloudProviderNodeData {
  provider: CloudProvider;
  label: string;
  size?: number;
  showLabel?: boolean;
}
```

#### ContainerNode.tsx
Grouping containers for organizing related nodes (VPC, subnets, org units).

**Features:**
- Resizable dimensions
- Label at top (editable)
- Border style options (solid, dashed, dotted)
- Configurable opacity
- Semi-transparent background
- Connection handles

**Data Interface:**
```typescript
interface ContainerNodeData {
  label: string;
  width?: number;
  height?: number;
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  borderStyle?: 'solid' | 'dashed' | 'dotted';
  labelPosition?: 'top' | 'center';
  textColor?: string;
  fontSize?: number;
  opacity?: number;
}
```

#### TextNode.tsx
Standalone text elements for annotations and labels.

**Features:**
- Multiline text support (textarea)
- Resizable
- Double-click to edit
- Ctrl/Cmd+Enter to finish editing
- Font styling (size, weight, color, alignment)
- Optional border
- Background color support

**Data Interface:**
```typescript
interface TextNodeData {
  text: string;
  fontSize?: number;
  fontWeight?: 'normal' | 'bold' | 'semibold';
  textColor?: string;
  backgroundColor?: string;
  padding?: number;
  textAlign?: 'left' | 'center' | 'right';
  width?: number;
  height?: number;
  borderColor?: string;
  borderWidth?: number;
  showBorder?: boolean;
}
```

### Edge Types

#### ConnectorEdge.tsx
Custom edges with extensive styling options.

**Features:**
- Multiple marker types (arrow, circle, diamond, none)
- Bidirectional arrows
- Floating labels
- Line styles (solid, dashed, dotted)
- Customizable colors and widths
- Gold accent when selected

**Data Interface:**
```typescript
interface ConnectorEdgeData {
  label?: string;
  startMarker?: 'none' | 'arrow' | 'circle' | 'diamond';
  endMarker?: 'none' | 'arrow' | 'circle' | 'diamond';
  strokeColor?: string;
  strokeWidth?: number;
  dashPattern?: 'solid' | 'dashed' | 'dotted';
  bidirectional?: boolean;
}
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Delete` / `Backspace` | Delete selected elements |
| `Ctrl/Cmd + C` | Copy selected elements |
| `Ctrl/Cmd + V` | Paste copied elements (offset by 50px) |
| `Ctrl/Cmd + Z` | Undo last action |
| `Ctrl/Cmd + Shift + Z` / `Ctrl/Cmd + Y` | Redo action |
| `Mouse Wheel` | Zoom in/out |
| `Double Click` (on node) | Edit text/label |
| `Escape` (while editing) | Cancel edit |
| `Enter` (while editing text) | Finish edit |
| `Ctrl/Cmd + Enter` (in textarea) | Finish multiline edit |

## Styling

### Theme Colors

The canvas uses a gold accent theme for selected states:
- Primary accent: `#d4af37` (gold)
- Default stroke: `#b1b1b7` (gray)
- Background: `#f9fafb` (light gray)

### Customization

All components accept style props through their data interfaces. You can customize:
- Fill colors
- Stroke colors and widths
- Text colors and sizes
- Border styles
- Background colors
- Opacity levels

## Usage Examples

### Creating a Basic Diagram

```tsx
import { Canvas } from './components/canvas';
import type { Node, Edge } from '@xyflow/react';

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'shape',
    position: { x: 250, y: 100 },
    data: {
      label: 'Web Server',
      shapeType: 'rectangle',
      fillColor: '#ffffff',
      strokeColor: '#000000',
    },
  },
  {
    id: '2',
    type: 'cloudProvider',
    position: { x: 250, y: 250 },
    data: {
      provider: 'aws',
      label: 'EC2',
      size: 64,
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    type: 'connector',
    data: {
      label: 'deployed on',
      endMarker: 'arrow',
    },
  },
];

function App() {
  return <Canvas initialNodes={initialNodes} initialEdges={initialEdges} />;
}
```

### Adding Custom Node Types

```tsx
import { ReactFlow, NodeTypes } from '@xyflow/react';
import { ShapeNode, CloudProviderNode } from './components/canvas';
import CustomNode from './CustomNode';

const nodeTypes: NodeTypes = {
  shape: ShapeNode,
  cloudProvider: CloudProviderNode,
  custom: CustomNode, // Your custom node
};

// Use in ReactFlow
<ReactFlow nodeTypes={nodeTypes} ... />
```

### Handling State Changes

```tsx
function DiagramEditor() {
  const handleNodesChange = (nodes: Node[]) => {
    console.log('Nodes updated:', nodes);
    // Save to backend, update state, etc.
  };

  const handleEdgesChange = (edges: Edge[]) => {
    console.log('Edges updated:', edges);
    // Save to backend, update state, etc.
  };

  return (
    <Canvas
      onNodesChange={handleNodesChange}
      onEdgesChange={handleEdgesChange}
    />
  );
}
```

## File Structure

```
/home/penguin/code/IceCharts/services/webui/src/components/canvas/
├── Canvas.tsx                 # Main wrapper component
├── Toolbar.tsx                # Top toolbar
├── ShapePanel.tsx             # Left sidebar shape library
├── PropertiesPanel.tsx        # Right sidebar properties
├── index.ts                   # Export barrel
├── nodes/
│   ├── ShapeNode.tsx         # Generic shapes
│   ├── CloudProviderNode.tsx # Cloud provider icons
│   ├── ContainerNode.tsx     # Grouping containers
│   └── TextNode.tsx          # Text elements
└── edges/
    └── ConnectorEdge.tsx     # Custom connectors
```

## Dependencies

- `@xyflow/react` v12+ - React Flow library for node-based UIs
- `react` v18+ - React framework
- `react-dom` v18+ - React DOM renderer
- Tailwind CSS - For utility classes (already configured in project)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Performance Considerations

- The canvas uses React Flow's built-in optimizations
- History is limited to 50 steps to prevent memory issues
- Large diagrams (>100 nodes) may experience slower interactions
- Consider using lazy loading for extensive shape libraries

## Accessibility

- Keyboard navigation support via React Flow
- Focus management for input fields
- ARIA labels on interactive elements
- Color contrast meets WCAG AA standards

## Future Enhancements

Potential additions for future versions:
- Export to PNG/SVG/PDF
- Import from Terraform/CloudFormation
- Collaborative editing
- Version history
- Templates library
- Snap-to-grid
- Alignment guides
- Multi-select actions
- Nested containers (parent-child relationships)

## Troubleshooting

### Nodes not appearing
- Ensure `@xyflow/react` CSS is imported: `import '@xyflow/react/dist/style.css'`
- Check that node types are registered in the `nodeTypes` prop

### Drag and drop not working
- Verify the shape panel's drag handlers are properly bound
- Check that the canvas wrapper div has proper dimensions

### Undo/redo not working
- Ensure keyboard event listeners are attached
- Check browser console for errors

### Styling issues
- Verify Tailwind CSS is configured and built
- Check that all required style props are provided
- Inspect element to see applied styles

## License

Part of the IceCharts project. See main project LICENSE file.

## Contact

For issues, questions, or contributions, please refer to the main IceCharts repository.
