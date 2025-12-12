import React, { useState, useCallback, useRef, useEffect } from 'react';
import { NodeProps, NodeResizer } from '@xyflow/react';

export interface TextNodeData {
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

const TextNode: React.FC<NodeProps> = ({ data, selected }) => {
  const [isEditing, setIsEditing] = useState(false);
  const nodeData = data as unknown as TextNodeData;
  const [text, setText] = useState(nodeData.text || 'Text');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const fontSize = nodeData.fontSize || 14;
  const fontWeight = nodeData.fontWeight || 'normal';
  const textColor = nodeData.textColor || '#000000';
  const backgroundColor = nodeData.backgroundColor || 'transparent';
  const padding = nodeData.padding || 8;
  const textAlign = nodeData.textAlign || 'left';
  const width = nodeData.width || 150;
  const height = nodeData.height || 60;
  const borderColor = nodeData.borderColor || '#e5e7eb';
  const borderWidth = nodeData.borderWidth || 1;
  const showBorder = nodeData.showBorder !== false;

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      textareaRef.current.select();
    }
  }, [isEditing]);

  const handleDoubleClick = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
  }, []);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      // Allow Enter for new lines in textarea
      if (event.key === 'Escape') {
        setText(nodeData.text || 'Text');
        setIsEditing(false);
        textareaRef.current?.blur();
      }
      // Ctrl/Cmd + Enter to finish editing
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        setIsEditing(false);
        textareaRef.current?.blur();
      }
    },
    [nodeData.text]
  );

  const getFontWeight = () => {
    switch (fontWeight) {
      case 'bold':
        return 700;
      case 'semibold':
        return 600;
      case 'normal':
      default:
        return 400;
    }
  };

  return (
    <>
      <NodeResizer
        color={selected ? '#d4af37' : '#b1b1b7'}
        isVisible={selected || false}
        minWidth={80}
        minHeight={40}
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
          border: showBorder
            ? `${borderWidth}px solid ${selected ? '#d4af37' : borderColor}`
            : 'none',
          borderRadius: '4px',
          padding: `${padding}px`,
          overflow: 'hidden',
          boxShadow:
            selected && showBorder
              ? '0 4px 12px rgba(212, 175, 55, 0.3)'
              : showBorder
              ? '0 1px 3px rgba(0,0,0,0.1)'
              : 'none',
        }}
        onDoubleClick={handleDoubleClick}
      >
        {isEditing ? (
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              outline: 'none',
              background: 'transparent',
              resize: 'none',
              fontSize: `${fontSize}px`,
              fontWeight: getFontWeight(),
              color: textColor,
              textAlign,
              fontFamily: 'inherit',
              lineHeight: 1.4,
            }}
          />
        ) : (
          <div
            style={{
              width: '100%',
              height: '100%',
              fontSize: `${fontSize}px`,
              fontWeight: getFontWeight(),
              color: textColor,
              textAlign,
              lineHeight: 1.4,
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              overflow: 'auto',
            }}
          >
            {text}
          </div>
        )}
      </div>
    </>
  );
};

export default TextNode;
