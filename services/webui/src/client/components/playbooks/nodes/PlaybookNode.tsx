/**
 * PlaybookNode - Custom React Flow node component for playbook workflows
 *
 * Renders workflow nodes with category-aware styling and multiple connection handles
 * for conditional branching, looping, and complex control flows.
 *
 * Features:
 * - Category-based styling (triggers, transforms, conditionals, actions)
 * - Multiple input/output handles for branching logic
 * - Visual distinction for selected nodes
 * - Explicit handle rendering with proper positioning
 * - Performance optimized with React.memo
 */

import React, { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

/**
 * Data structure for PlaybookNode
 */
export interface PlaybookNodeData {
  label: string;
  nodeType: string;
  category?: 'triggers' | 'transforms' | 'actions' | 'conditionals';
  handles?: {
    inputs: string[];
    outputs: string[];
  };
}

/**
 * PlaybookNode component
 *
 * Renders a node in the playbook workflow canvas with:
 * - Dynamic handles based on node type (single or multiple)
 * - Category-specific colors and styling
 * - Proper handle positioning and sizing
 * - Visual feedback for selection state
 *
 * @param data - Node data containing label, type, category, and handle configuration
 * @param selected - Whether node is currently selected
 * @returns Rendered node component with handles
 */
const PlaybookNode: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as unknown as PlaybookNodeData;
  const category = (nodeData?.category as 'triggers' | 'transforms' | 'actions' | 'conditionals') || 'transforms';

  // Determine handle visibility based on category
  // Triggers: only source (bottom) - they emit data into the flow
  // Actions: only target (top) - they receive data from the flow
  // Transforms & Conditionals: both - they receive and emit data
  const showTargetHandle = category !== 'triggers';
  const showSourceHandle = category !== 'actions';

  // Get styling based on category
  // Dark backgrounds with category-specific light text for better readability
  const getNodeStyling = () => {
    const baseStyle = {
      backgroundColor: '#1e3a5f',  // Dark navy blue for transforms
      borderColor: '#3B82F6',
      handleColor: '#3B82F6',
      textColor: '#93c5fd',  // Light blue text
    };

    switch (category) {
      case 'triggers':
        return {
          backgroundColor: '#1a3d2e',  // Dark green-tinted navy
          borderColor: '#22C55E',
          handleColor: '#22C55E',
          textColor: '#86efac',  // Light green text
        };
      case 'conditionals':
        return {
          backgroundColor: '#2d1f47',  // Dark purple-tinted navy
          borderColor: '#A855F7',
          handleColor: '#A855F7',
          textColor: '#d8b4fe',  // Light purple text
        };
      case 'actions':
        return {
          backgroundColor: '#3d2a1a',  // Dark orange-tinted navy
          borderColor: '#F97316',
          handleColor: '#F97316',
          textColor: '#fdba74',  // Light orange text
        };
      default:
        return baseStyle;
    }
  };

  const styling = getNodeStyling();
  const borderColor = selected ? '#D4AF37' : styling.borderColor;

  // Get input and output handles from node configuration
  const inputHandles = nodeData.handles?.inputs || ['default'];
  const outputHandles = nodeData.handles?.outputs || ['default'];

  return (
    <div
      style={{
        background: styling.backgroundColor,
        border: `2px solid ${borderColor}`,
        borderRadius: '8px',
        padding: '12px 16px',
        minWidth: '160px',
        color: styling.textColor,
        fontSize: '14px',
        textAlign: 'center',
        position: 'relative',
        transition: 'border-color 0.2s ease',
      }}
    >
      {/* Input Handles (Top) - For nodes that receive data */}
      {showTargetHandle && (
        <>
          {inputHandles.length === 1 ? (
            // Single target handle - center position
            <Handle
              type="target"
              position={Position.Top}
              id={inputHandles[0]}
              style={{
                background: styling.handleColor,
                width: 12,
                height: 12,
                border: '2px solid #1e293b',
                top: -6,
              }}
            />
          ) : (
            // Multiple target handles - distributed across top
            inputHandles.map((handleId, index) => {
              const totalHandles = inputHandles.length;
              const leftPercentage = ((index + 1) / (totalHandles + 1)) * 100;

              return (
                <Handle
                  key={`target-${handleId}`}
                  type="target"
                  position={Position.Top}
                  id={handleId}
                  style={{
                    background: styling.handleColor,
                    width: 10,
                    height: 10,
                    border: '2px solid #1e293b',
                    top: -5,
                    left: `${leftPercentage}%`,
                    transform: 'translateX(-50%)',
                  }}
                />
              );
            })
          )}
        </>
      )}

      {/* Node Label */}
      <div
        style={{
          fontWeight: 500,
          fontSize: '13px',
          lineHeight: '1.4',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          maxHeight: '40px',
        }}
      >
        {nodeData.label}
      </div>

      {/* Output Handles (Bottom) - For nodes that emit data */}
      {showSourceHandle && (
        <>
          {outputHandles.length === 1 ? (
            // Single source handle - center position
            <Handle
              type="source"
              position={Position.Bottom}
              id={outputHandles[0]}
              style={{
                background: styling.handleColor,
                width: 12,
                height: 12,
                border: '2px solid #1e293b',
                bottom: -6,
              }}
            />
          ) : (
            // Multiple source handles - distributed across bottom
            outputHandles.map((handleId, index) => {
              const totalHandles = outputHandles.length;
              const leftPercentage = ((index + 1) / (totalHandles + 1)) * 100;

              return (
                <Handle
                  key={`source-${handleId}`}
                  type="source"
                  position={Position.Bottom}
                  id={handleId}
                  style={{
                    background: styling.handleColor,
                    width: 10,
                    height: 10,
                    border: '2px solid #1e293b',
                    bottom: -5,
                    left: `${leftPercentage}%`,
                    transform: 'translateX(-50%)',
                  }}
                />
              );
            })
          )}
        </>
      )}
    </div>
  );
};

export default memo(PlaybookNode);
