import React from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
  MarkerType,
} from '@xyflow/react';

export type MarkerStyle = 'none' | 'arrow' | 'circle' | 'diamond';
export type DashPattern = 'solid' | 'dashed' | 'dotted';

export interface ConnectorEdgeData {
  label?: string;
  startMarker?: MarkerStyle;
  endMarker?: MarkerStyle;
  strokeColor?: string;
  strokeWidth?: number;
  dashPattern?: DashPattern;
  bidirectional?: boolean;
}

const ConnectorEdge: React.FC<EdgeProps<ConnectorEdgeData>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  markerStart,
  data,
  selected,
}) => {
  const label = data?.label || '';
  const strokeColor = data?.strokeColor || '#b1b1b7';
  const strokeWidth = data?.strokeWidth || 2;
  const dashPattern = data?.dashPattern || 'solid';
  const endMarkerStyle = data?.endMarker || 'arrow';
  const startMarkerStyle = data?.startMarker || 'none';
  const bidirectional = data?.bidirectional || false;

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const getStrokeDasharray = () => {
    switch (dashPattern) {
      case 'dashed':
        return '8,4';
      case 'dotted':
        return '2,2';
      case 'solid':
      default:
        return 'none';
    }
  };

  const createMarkerPath = (markerType: MarkerStyle) => {
    switch (markerType) {
      case 'arrow':
        return 'M 0,-5 L 10,0 L 0,5 Z';
      case 'circle':
        return 'M 5,0 a 5,5 0 1,0 0,0.1 Z';
      case 'diamond':
        return 'M 0,0 L 5,-5 L 10,0 L 5,5 Z';
      case 'none':
      default:
        return '';
    }
  };

  const getMarkerEnd = () => {
    if (endMarkerStyle === 'none') return undefined;
    return {
      type: MarkerType.ArrowClosed,
      color: selected ? '#d4af37' : strokeColor,
    };
  };

  const getMarkerStart = () => {
    if (bidirectional || startMarkerStyle !== 'none') {
      return {
        type: MarkerType.ArrowClosed,
        color: selected ? '#d4af37' : strokeColor,
      };
    }
    return undefined;
  };

  return (
    <>
      <defs>
        {/* Custom marker definitions */}
        {endMarkerStyle !== 'none' && endMarkerStyle !== 'arrow' && (
          <marker
            id={`marker-end-${id}`}
            markerWidth="10"
            markerHeight="10"
            refX="5"
            refY="5"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path
              d={createMarkerPath(endMarkerStyle)}
              fill={selected ? '#d4af37' : strokeColor}
            />
          </marker>
        )}
        {(bidirectional || startMarkerStyle !== 'none') && startMarkerStyle !== 'arrow' && (
          <marker
            id={`marker-start-${id}`}
            markerWidth="10"
            markerHeight="10"
            refX="5"
            refY="5"
            orient="auto-start-reverse"
            markerUnits="strokeWidth"
          >
            <path
              d={createMarkerPath(startMarkerStyle || 'arrow')}
              fill={selected ? '#d4af37' : strokeColor}
            />
          </marker>
        )}
      </defs>

      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={getMarkerEnd()}
        markerStart={getMarkerStart()}
        style={{
          ...style,
          stroke: selected ? '#d4af37' : strokeColor,
          strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
          strokeDasharray: getStrokeDasharray(),
        }}
      />

      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              background: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: 12,
              fontWeight: 500,
              color: '#374151',
              border: `1px solid ${selected ? '#d4af37' : '#e5e7eb'}`,
              pointerEvents: 'all',
              boxShadow: selected
                ? '0 2px 8px rgba(212, 175, 55, 0.3)'
                : '0 1px 3px rgba(0,0,0,0.1)',
            }}
            className="nodrag nopan"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

export default ConnectorEdge;
