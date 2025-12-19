# Playbook Node Components

This directory contains React Flow node components and configuration panels for different node types in the Playbook Editor.

## PlaybookNode

Custom React Flow node component that renders workflow nodes with category-aware styling and explicit connection handles for complex control flows.

### Features

- **Category-Based Styling**: Different colors for triggers (green), transforms (blue), and actions (orange)
- **Multiple Connection Handles**: Support for single and multiple input/output handles for branching logic
- **Smart Handle Positioning**: Single handles center-aligned, multiple handles distributed evenly
- **Visual Feedback**: Selection state indicated by golden border
- **Performance Optimized**: Memoized component for efficient re-renders
- **Type-Safe**: Full TypeScript support with exported types

### Node Categories

| Category | Inputs | Outputs | Use Case | Handle Colors |
|----------|--------|---------|----------|---------------|
| **triggers** | None | Yes | Start workflow execution | Green (#22C55E) |
| **transforms** | Yes | Yes | Process and transform data | Blue (#3B82F6) |
| **actions** | Yes | None | Output/consume data | Orange (#F97316) |

### Usage

```tsx
import { PlaybookNode, type PlaybookNodeData } from '../../components/playbooks/nodes';
import { ReactFlow, useNodesState, useEdgesState } from '@xyflow/react';

const nodeTypes = {
  playbook: PlaybookNode,
};

const initialNodes = [
  {
    id: 'trigger-1',
    type: 'playbook',
    position: { x: 0, y: 0 },
    data: {
      label: 'On Schedule',
      nodeType: 'trigger_schedule',
      category: 'triggers',
      handles: {
        inputs: [],
        outputs: ['default']
      }
    }
  },
  {
    id: 'transform-1',
    type: 'playbook',
    position: { x: 0, y: 100 },
    data: {
      label: 'Filter Data',
      nodeType: 'Filter',
      category: 'transforms',
      handles: {
        inputs: ['default'],
        outputs: ['true', 'false']
      }
    }
  }
];

function WorkflowEditor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
    />
  );
}
```

### Component Interface

```typescript
export interface PlaybookNodeData {
  label: string;                    // Display text for node
  nodeType: string;                 // Type identifier (e.g., 'Filter', 'transform_if_then')
  category?: 'triggers' | 'transforms' | 'actions';
  handles?: {
    inputs: string[];               // Array of input handle IDs
    outputs: string[];              // Array of output handle IDs
  };
}
```

### Handle Configuration Examples

```typescript
// Simple node - single input/output
{ inputs: ['default'], outputs: ['default'] }

// Conditional branching - true/false paths
{ inputs: ['default'], outputs: ['true', 'false'] }

// Switch statement - multiple cases
{ inputs: ['default'], outputs: ['case1', 'case2', 'case3', 'default'] }

// Loop node - iteration and completion paths
{ inputs: ['default'], outputs: ['item', 'complete'] }

// Merge operation - multiple inputs
{ inputs: ['input1', 'input2', 'input3'], outputs: ['default'] }

// Logic gates - multiple inputs
{ inputs: ['input1', 'input2'], outputs: ['true', 'false'] }
```

### Styling Customization

The component automatically applies category-specific colors:
- **Triggers** (green): `rgba(34, 197, 94, 0.15)` background, `#22C55E` handles
- **Transforms** (blue): `rgba(59, 130, 246, 0.15)` background, `#3B82F6` handles
- **Actions** (orange): `rgba(249, 115, 22, 0.15)` background, `#F97316` handles
- **Selected**: `#D4AF37` (gold) border

### Integration with PlaybookEditor

The PlaybookNode is fully integrated with the PlaybookEditor. Nodes created via drag-and-drop automatically:
1. Get assigned a category (triggers, transforms, actions)
2. Get handle configuration based on nodeType (via `getNodeHandles()`)
3. Render with appropriate styling and connection points

## Configuration Panels

This directory also contains configuration panel components for different node types in the Playbook Editor.

## AskAIConfigPanel

Configuration panel for the "Ask AI" transform node that allows querying LLMs.

### Features

- **Provider Selection**: Choose between Ollama (local), Claude (Anthropic), or OpenAI
- **Model Configuration**: Select or enter model name with provider-specific suggestions
- **Prompt Template**: Define prompts with variable interpolation using `{input}` or `{path.to.field}`
- **System Prompt**: Optional system prompt for context setting
- **Temperature Control**: Slider from 0.0 (precise) to 2.0 (creative)
- **Max Tokens**: Configure maximum response length
- **Input Mapping**: JSONPath expression to extract specific data from input

### Usage

```tsx
import { AskAIConfigPanel } from '../../components/playbooks/nodes';

const [config, setConfig] = useState({
  provider: 'ollama',
  model: 'llama2',
  prompt: 'Analyze this data: {input}',
  systemPrompt: 'You are a data analyst.',
  temperature: 1.0,
  maxTokens: 1000,
  inputMapping: '$.data.items[*]',
});

<AskAIConfigPanel config={config} onChange={setConfig} />
```

### Provider-Specific Models

#### Ollama (Local)
- llama2
- mistral
- codellama
- mixtral

#### Claude (Anthropic)
- claude-3-opus
- claude-3-sonnet
- claude-3-haiku

#### OpenAI
- gpt-4
- gpt-4-turbo
- gpt-3.5-turbo

### Configuration Interface

```typescript
interface AskAIConfig {
  provider: 'ollama' | 'claude' | 'openai';
  model: string;
  prompt: string;
  systemPrompt?: string;
  temperature?: number;        // 0.0 - 2.0
  maxTokens?: number;          // 1 - 8000
  inputMapping?: string;       // JSONPath expression
}
```

### Styling

The component uses the IceCharts theme with:
- `ice-navy` shades for backgrounds and borders
- `ice-gold` accents for interactive elements
- Tailwind CSS utility classes
- Responsive design with focus states
