/**
 * AnimatedFlowEdge - Custom edge component with directional flow animation
 *
 * Features:
 * - Animated dashed line showing data flow direction
 * - Arrow marker at target end
 * - Color-coded based on edge state (active, success, error)
 */

import React from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type Position,
} from '@xyflow/react';

// Edge animation keyframes - inject once
const injectAnimationStyles = () => {
  const styleId = 'playbook-edge-animations';
  if (document.getElementById(styleId)) return;

  const style = document.createElement('style');
  style.id = styleId;
  style.textContent = `
    @keyframes flowAnimation {
      0% {
        stroke-dashoffset: 20;
      }
      100% {
        stroke-dashoffset: 0;
      }
    }

    @keyframes pulseAnimation {
      0%, 100% {
        stroke-opacity: 1;
      }
      50% {
        stroke-opacity: 0.5;
      }
    }

    .animated-flow-edge {
      stroke-dasharray: 5, 5;
      animation: flowAnimation 0.5s linear infinite;
    }

    .animated-flow-edge.active {
      stroke: #60A5FA;
      stroke-width: 2.5;
      animation: flowAnimation 0.3s linear infinite, pulseAnimation 1s ease-in-out infinite;
    }

    .animated-flow-edge.success {
      stroke: #34D399;
      stroke-width: 2;
    }

    .animated-flow-edge.error {
      stroke: #F87171;
      stroke-width: 2;
    }

    .animated-flow-edge.pending {
      stroke: #9CA3AF;
      stroke-width: 1.5;
    }

    .flow-edge-path {
      transition: stroke 0.3s ease, stroke-width 0.3s ease;
    }
  `;
  document.head.appendChild(style);
};

// Inject styles on module load
if (typeof window !== 'undefined') {
  injectAnimationStyles();
}

export interface AnimatedFlowEdgeData {
  /** Edge state for color-coding */
  state?: 'pending' | 'active' | 'success' | 'error';
  /** Whether to animate the edge */
  animated?: boolean;
  /** Custom label to display */
  label?: string;
}

// Define the props interface explicitly for React Flow custom edges
interface AnimatedFlowEdgeProps {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  sourcePosition: Position;
  targetPosition: Position;
  style?: React.CSSProperties;
  data?: AnimatedFlowEdgeData;
  markerEnd?: string;
  selected?: boolean;
}

export const AnimatedFlowEdge: React.FC<AnimatedFlowEdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
  selected,
}) => {
  const state = data?.state || 'pending';
  const animated = data?.animated !== false;

  // Get smooth step path
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 8,
  });

  // Build class names
  const classNames = [
    'flow-edge-path',
    animated ? 'animated-flow-edge' : '',
    state,
    selected ? 'selected' : '',
  ].filter(Boolean).join(' ');

  // Base stroke color by state
  const strokeColors: Record<string, string> = {
    pending: '#6B7280',  // Gray
    active: '#3B82F6',   // Blue
    success: '#10B981',  // Green
    error: '#EF4444',    // Red
  };

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        className={classNames}
        style={{
          stroke: strokeColors[state] || strokeColors.pending,
          strokeWidth: selected ? 3 : 2,
          ...style,
        }}
        markerEnd={markerEnd}
      />

      {/* Optional edge label */}
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              fontSize: 10,
              fontWeight: 500,
              background: '#1F2937',
              color: '#E5E7EB',
              padding: '2px 6px',
              borderRadius: 4,
              border: '1px solid #374151',
              pointerEvents: 'all',
            }}
            className="nodrag nopan"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

export default AnimatedFlowEdge;
