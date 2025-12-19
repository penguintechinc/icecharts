import React, { useState } from 'react';

export type ToolMode = 'select' | 'pan' | 'shape' | 'line' | 'text';
export type ShapeType = 'rectangle' | 'circle' | 'diamond' | 'triangle' | 'hexagon';

interface ToolbarProps {
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  onAddNode: (nodeType: string, nodeData: any) => void;
  onElderImport?: () => void;
}

const Toolbar: React.FC<ToolbarProps> = ({
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  onAddNode,
  onElderImport,
}) => {
  const [activeMode, setActiveMode] = useState<ToolMode>('select');
  const [_selectedShape, setSelectedShape] = useState<ShapeType>('rectangle');

  const handleModeChange = (mode: ToolMode) => {
    setActiveMode(mode);
  };

  const handleAddShape = (shapeType: ShapeType) => {
    setSelectedShape(shapeType);
    onAddNode('shape', {
      label: shapeType.charAt(0).toUpperCase() + shapeType.slice(1),
      shapeType,
      width: 120,
      height: 80,
      fillColor: '#ffffff',
      strokeColor: '#000000',
      strokeWidth: 2,
    });
  };

  const handleAddText = () => {
    onAddNode('text', {
      text: 'Text',
      fontSize: 14,
      fontWeight: 'normal',
      textColor: '#000000',
      backgroundColor: 'transparent',
      showBorder: false,
    });
  };

  const iconButtonClass = (isActive: boolean) =>
    `p-2 rounded-md transition-colors ${
      isActive
        ? 'bg-yellow-600 text-white shadow-md'
        : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
    }`;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-2 flex items-center gap-2">
      {/* Selection Mode */}
      <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
        <button
          className={iconButtonClass(activeMode === 'select')}
          onClick={() => handleModeChange('select')}
          title="Select (V)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"
            />
          </svg>
        </button>
        <button
          className={iconButtonClass(activeMode === 'pan')}
          onClick={() => handleModeChange('pan')}
          title="Pan (H)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11"
            />
          </svg>
        </button>
      </div>

      {/* Shapes */}
      <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
        <button
          className={iconButtonClass(false)}
          onClick={() => handleAddShape('rectangle')}
          title="Rectangle"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <rect
              x="3"
              y="6"
              width="18"
              height="12"
              rx="2"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
        <button
          className={iconButtonClass(false)}
          onClick={() => handleAddShape('circle')}
          title="Circle"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <circle
              cx="12"
              cy="12"
              r="8"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
        <button
          className={iconButtonClass(false)}
          onClick={() => handleAddShape('diamond')}
          title="Diamond"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              d="M12 3L21 12L12 21L3 12L12 3Z"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
        <button
          className={iconButtonClass(false)}
          onClick={() => handleAddShape('triangle')}
          title="Triangle"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              d="M12 4L20 20H4L12 4Z"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
        <button
          className={iconButtonClass(false)}
          onClick={() => handleAddShape('hexagon')}
          title="Hexagon"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              d="M6 8L12 4L18 8V16L12 20L6 16V8Z"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>

      {/* Text */}
      <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
        <button
          className={iconButtonClass(false)}
          onClick={handleAddText}
          title="Text (T)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </button>
      </div>

      {/* Undo/Redo */}
      <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
        <button
          className={iconButtonClass(false)}
          onClick={onUndo}
          disabled={!canUndo}
          title="Undo (Ctrl+Z)"
          style={{ opacity: canUndo ? 1 : 0.4, cursor: canUndo ? 'pointer' : 'not-allowed' }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
            />
          </svg>
        </button>
        <button
          className={iconButtonClass(false)}
          onClick={onRedo}
          disabled={!canRedo}
          title="Redo (Ctrl+Y)"
          style={{ opacity: canRedo ? 1 : 0.4, cursor: canRedo ? 'pointer' : 'not-allowed' }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 10h-10a8 8 0 00-8 8v2m18-10l-6 6m6-6l-6-6"
            />
          </svg>
        </button>
      </div>

      {/* Elder Integration */}
      {onElderImport && (
        <div className="flex items-center gap-1 border-r border-gray-200 pr-2">
          <button
            className={iconButtonClass(false)}
            onClick={onElderImport}
            title="Import from Elder"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
          </button>
        </div>
      )}

      {/* Zoom info */}
      <div className="text-sm text-gray-500 font-medium">
        Use mouse wheel to zoom
      </div>
    </div>
  );
};

export default Toolbar;
