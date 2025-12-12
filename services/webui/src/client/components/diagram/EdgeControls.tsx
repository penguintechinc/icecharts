import React, { useState } from 'react';
import { Edge } from '@xyflow/react';

interface EdgeData {
  label?: string;
  startMarker?: 'none' | 'arrow' | 'circle' | 'diamond';
  endMarker?: 'none' | 'arrow' | 'circle' | 'diamond';
  animated?: boolean;
}

interface EdgeControlsProps {
  selectedEdge: Edge | null;
  onUpdateEdge: (edgeId: string, data: Partial<EdgeData>) => void;
  position: { x: number; y: number };
}

/**
 * EdgeControls Component
 *
 * A floating toolbar for editing edge properties in the diagram editor.
 * Appears when an edge is selected and provides controls for:
 * - Start marker selection (none, arrow, circle, diamond)
 * - Direction toggles (→, ←, ↔)
 * - End marker selection (none, arrow, circle, diamond)
 * - Animation toggle
 *
 * Features:
 * - Dark theme styling matching the IceCharts design system
 * - Floating position above the click point
 * - Smooth transitions and hover states
 * - Icon-based marker selector with visual feedback
 */
export default function EdgeControls({
  selectedEdge,
  onUpdateEdge,
  position,
}: EdgeControlsProps) {
  const [isVisible, setIsVisible] = useState(true);

  // Return early if no edge is selected
  if (!selectedEdge || !isVisible) {
    return null;
  }

  // Extract current edge data
  const edgeData = (selectedEdge.data || {}) as EdgeData;
  const currentStartMarker = edgeData.startMarker || 'none';
  const currentEndMarker = edgeData.endMarker || 'arrow';
  // animated is stored directly on the edge, not in edge.data
  const isAnimated = selectedEdge.animated || false;

  // Calculate toolbar position (offset above the click point)
  const toolbarStyle: React.CSSProperties = {
    position: 'fixed',
    left: `${position.x}px`,
    top: `${position.y - 120}px`,
    zIndex: 1000,
  };

  // Marker button component
  const MarkerButton = ({
    marker,
    isSelected,
    onClick,
  }: {
    marker: 'none' | 'arrow' | 'circle' | 'diamond';
    isSelected: boolean;
    onClick: () => void;
  }) => {
    const getMarkerIcon = () => {
      switch (marker) {
        case 'arrow':
          return '▶';
        case 'circle':
          return '●';
        case 'diamond':
          return '◆';
        default:
          return '—';
      }
    };

    return (
      <button
        onClick={onClick}
        className={`px-2.5 py-1.5 rounded transition-all duration-200 text-sm font-medium ${
          isSelected
            ? 'bg-ice-gold-400 text-gray-900 shadow-md'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
        title={`Set marker to ${marker}`}
      >
        {getMarkerIcon()}
      </button>
    );
  };

  // Direction button component
  const DirectionButton = ({
    label,
    onClick,
    isActive,
  }: {
    label: string;
    onClick: () => void;
    isActive: boolean;
  }) => {
    return (
      <button
        onClick={onClick}
        className={`px-3 py-1.5 rounded transition-all duration-200 text-sm font-medium ${
          isActive
            ? 'bg-ice-blue-500 text-white shadow-md'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
        title={label}
      >
        {label}
      </button>
    );
  };

  // Toggle button component
  const ToggleButton = ({
    label,
    isActive,
    onClick,
  }: {
    label: string;
    isActive: boolean;
    onClick: () => void;
  }) => {
    return (
      <button
        onClick={onClick}
        className={`px-3 py-1.5 rounded transition-all duration-200 text-sm font-medium ${
          isActive
            ? 'bg-emerald-600 text-white shadow-md'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
        }`}
        title={label}
      >
        {label}
      </button>
    );
  };

  // Handle start marker selection
  const handleStartMarkerChange = (marker: 'none' | 'arrow' | 'circle' | 'diamond') => {
    onUpdateEdge(selectedEdge.id, { startMarker: marker });
  };

  // Handle end marker selection
  const handleEndMarkerChange = (marker: 'none' | 'arrow' | 'circle' | 'diamond') => {
    onUpdateEdge(selectedEdge.id, { endMarker: marker });
  };

  // Handle direction changes
  const handleDirectionRight = () => {
    onUpdateEdge(selectedEdge.id, {
      startMarker: 'none',
      endMarker: 'arrow',
    });
  };

  const handleDirectionLeft = () => {
    onUpdateEdge(selectedEdge.id, {
      startMarker: 'arrow',
      endMarker: 'none',
    });
  };

  const handleDirectionBidirectional = () => {
    onUpdateEdge(selectedEdge.id, {
      startMarker: 'arrow',
      endMarker: 'arrow',
    });
  };

  // Handle animation toggle
  const handleToggleAnimation = () => {
    onUpdateEdge(selectedEdge.id, { animated: !isAnimated });
  };

  // Check which direction buttons should be active
  const isRightActive = currentStartMarker === 'none' && currentEndMarker === 'arrow';
  const isLeftActive = currentStartMarker === 'arrow' && currentEndMarker === 'none';
  const isBidirectionalActive = currentStartMarker === 'arrow' && currentEndMarker === 'arrow';

  return (
    <div
      style={toolbarStyle}
      className="fade-in animate-in zoom-in-95"
    >
      <div className="flex flex-col gap-3 bg-gray-800 border border-gray-700 rounded-lg shadow-2xl p-4 w-max">
        {/* Header / Close button */}
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-xs font-semibold text-ice-gold-400 uppercase tracking-wider">
            Edge Controls
          </h3>
          <button
            onClick={() => setIsVisible(false)}
            className="text-gray-400 hover:text-gray-200 transition-colors text-lg leading-none"
            title="Close controls"
          >
            ×
          </button>
        </div>

        {/* Start Marker Selection */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-gray-300 uppercase tracking-wider">
            Start Marker
          </label>
          <div className="flex gap-1">
            <MarkerButton
              marker="none"
              isSelected={currentStartMarker === 'none'}
              onClick={() => handleStartMarkerChange('none')}
            />
            <MarkerButton
              marker="arrow"
              isSelected={currentStartMarker === 'arrow'}
              onClick={() => handleStartMarkerChange('arrow')}
            />
            <MarkerButton
              marker="circle"
              isSelected={currentStartMarker === 'circle'}
              onClick={() => handleStartMarkerChange('circle')}
            />
            <MarkerButton
              marker="diamond"
              isSelected={currentStartMarker === 'diamond'}
              onClick={() => handleStartMarkerChange('diamond')}
            />
          </div>
        </div>

        {/* Direction Quick Toggles */}
        <div className="flex flex-col gap-2 border-t border-gray-700 pt-3">
          <label className="text-xs font-medium text-gray-300 uppercase tracking-wider">
            Direction
          </label>
          <div className="flex gap-1">
            <DirectionButton
              label="→"
              onClick={handleDirectionRight}
              isActive={isRightActive}
            />
            <DirectionButton
              label="←"
              onClick={handleDirectionLeft}
              isActive={isLeftActive}
            />
            <DirectionButton
              label="↔"
              onClick={handleDirectionBidirectional}
              isActive={isBidirectionalActive}
            />
          </div>
        </div>

        {/* End Marker Selection */}
        <div className="flex flex-col gap-2 border-t border-gray-700 pt-3">
          <label className="text-xs font-medium text-gray-300 uppercase tracking-wider">
            End Marker
          </label>
          <div className="flex gap-1">
            <MarkerButton
              marker="none"
              isSelected={currentEndMarker === 'none'}
              onClick={() => handleEndMarkerChange('none')}
            />
            <MarkerButton
              marker="arrow"
              isSelected={currentEndMarker === 'arrow'}
              onClick={() => handleEndMarkerChange('arrow')}
            />
            <MarkerButton
              marker="circle"
              isSelected={currentEndMarker === 'circle'}
              onClick={() => handleEndMarkerChange('circle')}
            />
            <MarkerButton
              marker="diamond"
              isSelected={currentEndMarker === 'diamond'}
              onClick={() => handleEndMarkerChange('diamond')}
            />
          </div>
        </div>

        {/* Animation Toggle */}
        <div className="flex flex-col gap-2 border-t border-gray-700 pt-3">
          <label className="text-xs font-medium text-gray-300 uppercase tracking-wider">
            Animation
          </label>
          <ToggleButton
            label={isAnimated ? 'ON' : 'OFF'}
            isActive={isAnimated}
            onClick={handleToggleAnimation}
          />
        </div>

        {/* Edge Info */}
        <div className="flex flex-col gap-1 border-t border-gray-700 pt-3 text-xs text-gray-400">
          <div>
            <span className="text-gray-500">Edge ID: </span>
            <code className="text-gray-300 font-mono text-[10px]">{selectedEdge.id}</code>
          </div>
          {edgeData.label && (
            <div>
              <span className="text-gray-500">Label: </span>
              <span className="text-gray-300">{edgeData.label}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
