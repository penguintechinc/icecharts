import React, { useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, Handle, Position, NodeResizer } from '@xyflow/react';

export interface ContainerNodeData {
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

const ContainerNode: React.FC<NodeProps<ContainerNodeData>> = ({ id, data, selected }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label || 'Container');
  const inputRef = useRef<HTMLInputElement>(null);

  const width = data.width || 300;
  const height = data.height || 200;
  const backgroundColor = data.backgroundColor || '#f9fafb';
  const borderColor = data.borderColor || '#6b7280';
  const borderWidth = data.borderWidth || 2;
  const borderStyle = data.borderStyle || 'dashed';
  const labelPosition = data.labelPosition || 'top';
  const textColor = data.textColor || '#374151';
  const fontSize = data.fontSize || 14;
  const opacity = data.opacity || 0.9;

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
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === 'Enter') {
        setIsEditing(false);
        inputRef.current?.blur();
      }
      if (event.key === 'Escape') {
        setLabel(data.label || 'Container');
        setIsEditing(false);
        inputRef.current?.blur();
      }
    },
    [data.label]
  );

  const getBorderStyle = () => {
    switch (borderStyle) {
      case 'dashed':
        return `${borderWidth}px dashed ${selected ? '#d4af37' : borderColor}`;
      case 'dotted':
        return `${borderWidth}px dotted ${selected ? '#d4af37' : borderColor}`;
      case 'solid':
      default:
        return `${borderWidth}px solid ${selected ? '#d4af37' : borderColor}`;
    }
  };

  return (
    <>
      <NodeResizer
        color={selected ? '#d4af37' : '#b1b1b7'}
        isVisible={selected}
        minWidth={150}
        minHeight={100}
        handleStyle={{
          width: 8,
          height: 8,
          borderRadius: '50%',
        }}
      />

      <div
        style={{
          width: `${width}px`,
          height: `${height}px`,
          backgroundColor,
          border: getBorderStyle(),
          borderRadius: '8px',
          opacity,
          position: 'relative',
          boxShadow: selected ? '0 4px 12px rgba(212, 175, 55, 0.3)' : '0 2px 8px rgba(0,0,0,0.05)',
        }}
        onDoubleClick={handleDoubleClick}
      >
        {/* Label */}
        <div
          style={{
            position: 'absolute',
            top: labelPosition === 'top' ? '8px' : '50%',
            left: '50%',
            transform:
              labelPosition === 'top' ? 'translateX(-50%)' : 'translate(-50%, -50%)',
            padding: '4px 12px',
            backgroundColor: 'white',
            borderRadius: '4px',
            border: `1px solid ${borderColor}`,
            zIndex: 1,
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
                width: '150px',
                border: 'none',
                outline: 'none',
                background: 'transparent',
                textAlign: 'center',
                fontSize: `${fontSize}px`,
                color: textColor,
                fontFamily: 'inherit',
                fontWeight: 600,
              }}
            />
          ) : (
            <div
              style={{
                fontSize: `${fontSize}px`,
                color: textColor,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              {label}
            </div>
          )}
        </div>

        {/* Container content area - children nodes can be placed here */}
        <div
          style={{
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* Connection handles at all sides */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#555', opacity: 0.5 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#555', opacity: 0.5 }}
      />
      <Handle
        type="target"
        position={Position.Right}
        style={{ background: '#555', opacity: 0.5 }}
      />
      <Handle
        type="target"
        position={Position.Bottom}
        style={{ background: '#555', opacity: 0.5 }}
      />

      <Handle
        type="source"
        position={Position.Top}
        style={{ background: '#555', opacity: 0.5 }}
      />
      <Handle
        type="source"
        position={Position.Left}
        style={{ background: '#555', opacity: 0.5 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#555', opacity: 0.5 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#555', opacity: 0.5 }}
      />
    </>
  );
};

export default ContainerNode;
