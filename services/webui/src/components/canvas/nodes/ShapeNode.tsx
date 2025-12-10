import React, { useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position, NodeResizer } from '@xyflow/react';

export type ShapeType = 'rectangle' | 'circle' | 'diamond' | 'triangle' | 'hexagon' | 'parallelogram';

export interface ShapeNodeData {
  label: string;
  shapeType: ShapeType;
  width?: number;
  height?: number;
  fillColor?: string;
  strokeColor?: string;
  strokeWidth?: number;
  textColor?: string;
  fontSize?: number;
}

const ShapeNode: React.FC<NodeProps> = ({ data, selected }) => {
  const [isEditing, setIsEditing] = useState(false);
  const nodeData = data as unknown as ShapeNodeData;
  const [label, setLabel] = useState(nodeData.label || '');
  const inputRef = useRef<HTMLInputElement>(null);

  const width = nodeData.width || 120;
  const height = nodeData.height || 80;
  const fillColor = nodeData.fillColor || '#ffffff';
  const strokeColor = nodeData.strokeColor || '#000000';
  const strokeWidth = nodeData.strokeWidth || 2;
  const textColor = nodeData.textColor || '#000000';
  const fontSize = nodeData.fontSize || 14;
  const shapeType = nodeData.shapeType || 'rectangle';

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleDoubleClick = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
    // Update node data through parent component
    if (nodeData.label !== label) {
      // This would need to be handled by the parent Canvas component
      // For now, just update local state
    }
  }, [nodeData.label, label]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter') {
        setIsEditing(false);
        inputRef.current?.blur();
      }
      if (event.key === 'Escape') {
        setLabel(nodeData.label || '');
        setIsEditing(false);
        inputRef.current?.blur();
      }
    },
    [nodeData.label]
  );

  const renderShape = () => {
    const shapeStyle = {
      width: '100%',
      height: '100%',
      fill: fillColor,
      stroke: selected ? '#d4af37' : strokeColor,
      strokeWidth: selected ? strokeWidth + 1 : strokeWidth,
    };

    switch (shapeType) {
      case 'circle':
        return (
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            <ellipse cx="50" cy="50" rx="48" ry="48" style={shapeStyle} />
          </svg>
        );

      case 'diamond':
        return (
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polygon points="50,5 95,50 50,95 5,50" style={shapeStyle} />
          </svg>
        );

      case 'triangle':
        return (
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polygon points="50,5 95,95 5,95" style={shapeStyle} />
          </svg>
        );

      case 'hexagon':
        return (
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polygon points="25,5 75,5 95,50 75,95 25,95 5,50" style={shapeStyle} />
          </svg>
        );

      case 'parallelogram':
        return (
          <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
            <polygon points="15,5 100,5 85,95 0,95" style={shapeStyle} />
          </svg>
        );

      case 'rectangle':
      default:
        return (
          <div
            style={{
              width: '100%',
              height: '100%',
              backgroundColor: fillColor,
              border: `${selected ? strokeWidth + 1 : strokeWidth}px solid ${selected ? '#d4af37' : strokeColor}`,
              borderRadius: '4px',
            }}
          />
        );
    }
  };

  return (
    <>
      <NodeResizer
        color={selected ? '#d4af37' : '#b1b1b7'}
        isVisible={selected || false}
        minWidth={60}
        minHeight={40}
        handleStyle={{
          width: 8,
          height: 8,
          borderRadius: '50%',
        }}
      />
      <Handle type="target" position={Position.Top} style={{ background: '#555' }} />
      <Handle type="target" position={Position.Left} style={{ background: '#555' }} />
      <Handle type="target" position={Position.Right} style={{ background: '#555' }} />
      <Handle type="target" position={Position.Bottom} style={{ background: '#555' }} />

      <div
        style={{
          width: `${width}px`,
          height: `${height}px`,
          position: 'relative',
        }}
        onDoubleClick={handleDoubleClick}
      >
        {renderShape()}

        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '90%',
            textAlign: 'center',
            pointerEvents: isEditing ? 'auto' : 'none',
            zIndex: 10,
          }}
        >
          {isEditing ? (
            <input
              ref={inputRef}
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              style={{
                width: '100%',
                border: 'none',
                outline: 'none',
                background: 'transparent',
                textAlign: 'center',
                fontSize: `${fontSize}px`,
                color: textColor,
                fontFamily: 'inherit',
              }}
            />
          ) : (
            <div
              style={{
                fontSize: `${fontSize}px`,
                color: textColor,
                fontWeight: 500,
                lineHeight: 1.2,
                wordWrap: 'break-word',
                overflow: 'hidden',
                maxHeight: '100%',
              }}
            >
              {label}
            </div>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Top} style={{ background: '#555' }} />
      <Handle type="source" position={Position.Left} style={{ background: '#555' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#555' }} />
      <Handle type="source" position={Position.Bottom} style={{ background: '#555' }} />
    </>
  );
};

export default ShapeNode;
