import React, { useState, useEffect } from 'react';
import type { Node, Edge } from '@xyflow/react';

interface PropertiesPanelProps {
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onUpdateNode: (nodeId: string, newData: any) => void;
  onUpdateEdge: (edgeId: string, newData: any) => void;
}

const PropertiesPanel: React.FC<PropertiesPanelProps> = ({
  selectedNode,
  selectedEdge,
  onUpdateNode,
  onUpdateEdge,
}) => {
  const [metadata, setMetadata] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');

  useEffect(() => {
    if (selectedNode?.data?.metadata) {
      setMetadata(selectedNode.data.metadata);
    } else if (selectedEdge?.data?.metadata) {
      setMetadata(selectedEdge.data.metadata);
    } else {
      setMetadata({});
    }
  }, [selectedNode, selectedEdge]);

  const handleAddMetadata = () => {
    if (newKey.trim() && newValue.trim()) {
      const updatedMetadata = { ...metadata, [newKey]: newValue };
      setMetadata(updatedMetadata);

      if (selectedNode) {
        onUpdateNode(selectedNode.id, { metadata: updatedMetadata });
      } else if (selectedEdge) {
        onUpdateEdge(selectedEdge.id, { metadata: updatedMetadata });
      }

      setNewKey('');
      setNewValue('');
    }
  };

  const handleRemoveMetadata = (key: string) => {
    const updatedMetadata = { ...metadata };
    delete updatedMetadata[key];
    setMetadata(updatedMetadata);

    if (selectedNode) {
      onUpdateNode(selectedNode.id, { metadata: updatedMetadata });
    } else if (selectedEdge) {
      onUpdateEdge(selectedEdge.id, { metadata: updatedMetadata });
    }
  };

  const handleNodeChange = (field: string, value: any) => {
    if (selectedNode) {
      onUpdateNode(selectedNode.id, { [field]: value });
    }
  };

  const handleEdgeChange = (field: string, value: any) => {
    if (selectedEdge) {
      onUpdateEdge(selectedEdge.id, { [field]: value });
    }
  };

  if (!selectedNode && !selectedEdge) {
    return (
      <div className="w-80 bg-gray-50 border-l border-gray-200 p-4 flex-shrink-0">
        <div className="text-center text-gray-500 mt-8">
          <svg
            className="h-12 w-12 mx-auto mb-4 text-gray-400"
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
          <p className="text-sm font-medium">No element selected</p>
          <p className="text-xs text-gray-400 mt-1">
            Select a node or edge to view properties
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-gray-50 border-l border-gray-200 overflow-y-auto flex-shrink-0">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Properties</h2>

        {selectedNode && (
          <>
            {/* Node Type */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
              <div className="px-3 py-2 bg-gray-100 rounded text-sm text-gray-700 capitalize">
                {selectedNode.type || 'default'}
              </div>
            </div>

            {/* Position */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-2">Position</label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">X</label>
                  <input
                    type="number"
                    value={Math.round(selectedNode.position.x)}
                    disabled
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-gray-100"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Y</label>
                  <input
                    type="number"
                    value={Math.round(selectedNode.position.y)}
                    disabled
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded bg-gray-100"
                  />
                </div>
              </div>
            </div>

            {/* Size (if applicable) */}
            {selectedNode.data?.width && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-2">Size</label>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Width</label>
                    <input
                      type="number"
                      value={selectedNode.data.width}
                      onChange={(e) =>
                        handleNodeChange('width', parseInt(e.target.value) || 100)
                      }
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Height</label>
                    <input
                      type="number"
                      value={selectedNode.data.height}
                      onChange={(e) =>
                        handleNodeChange('height', parseInt(e.target.value) || 100)
                      }
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Label/Text */}
            {(selectedNode.data?.label !== undefined || selectedNode.data?.text !== undefined) && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {selectedNode.data?.text !== undefined ? 'Text' : 'Label'}
                </label>
                <input
                  type="text"
                  value={selectedNode.data?.label || selectedNode.data?.text || ''}
                  onChange={(e) =>
                    handleNodeChange(
                      selectedNode.data?.text !== undefined ? 'text' : 'label',
                      e.target.value
                    )
                  }
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                />
              </div>
            )}

            {/* Fill Color */}
            {selectedNode.data?.fillColor !== undefined && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-1">Fill Color</label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={selectedNode.data.fillColor}
                    onChange={(e) => handleNodeChange('fillColor', e.target.value)}
                    className="h-10 w-16 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={selectedNode.data.fillColor}
                    onChange={(e) => handleNodeChange('fillColor', e.target.value)}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {/* Stroke Color */}
            {selectedNode.data?.strokeColor !== undefined && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Stroke Color
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={selectedNode.data.strokeColor}
                    onChange={(e) => handleNodeChange('strokeColor', e.target.value)}
                    className="h-10 w-16 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={selectedNode.data.strokeColor}
                    onChange={(e) => handleNodeChange('strokeColor', e.target.value)}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {/* Stroke Width */}
            {selectedNode.data?.strokeWidth !== undefined && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Stroke Width
                </label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={selectedNode.data.strokeWidth}
                  onChange={(e) =>
                    handleNodeChange('strokeWidth', parseInt(e.target.value) || 1)
                  }
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                />
              </div>
            )}

            {/* Text Color */}
            {selectedNode.data?.textColor !== undefined && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-1">Text Color</label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={selectedNode.data.textColor}
                    onChange={(e) => handleNodeChange('textColor', e.target.value)}
                    className="h-10 w-16 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={selectedNode.data.textColor}
                    onChange={(e) => handleNodeChange('textColor', e.target.value)}
                    className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {/* Font Size */}
            {selectedNode.data?.fontSize !== undefined && (
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-600 mb-1">Font Size</label>
                <input
                  type="number"
                  min="8"
                  max="72"
                  value={selectedNode.data.fontSize}
                  onChange={(e) => handleNodeChange('fontSize', parseInt(e.target.value) || 14)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                />
              </div>
            )}
          </>
        )}

        {selectedEdge && (
          <>
            {/* Edge Label */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
              <input
                type="text"
                value={selectedEdge.data?.label || ''}
                onChange={(e) => handleEdgeChange('label', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
              />
            </div>

            {/* Stroke Color */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">Color</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={selectedEdge.data?.strokeColor || '#b1b1b7'}
                  onChange={(e) => handleEdgeChange('strokeColor', e.target.value)}
                  className="h-10 w-16 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={selectedEdge.data?.strokeColor || '#b1b1b7'}
                  onChange={(e) => handleEdgeChange('strokeColor', e.target.value)}
                  className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
                />
              </div>
            </div>

            {/* Stroke Width */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">Width</label>
              <input
                type="number"
                min="1"
                max="10"
                value={selectedEdge.data?.strokeWidth || 2}
                onChange={(e) => handleEdgeChange('strokeWidth', parseInt(e.target.value) || 2)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
              />
            </div>

            {/* Dash Pattern */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">Line Style</label>
              <select
                value={selectedEdge.data?.dashPattern || 'solid'}
                onChange={(e) => handleEdgeChange('dashPattern', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
              >
                <option value="solid">Solid</option>
                <option value="dashed">Dashed</option>
                <option value="dotted">Dotted</option>
              </select>
            </div>

            {/* End Marker */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">End Marker</label>
              <select
                value={selectedEdge.data?.endMarker || 'arrow'}
                onChange={(e) => handleEdgeChange('endMarker', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
              >
                <option value="none">None</option>
                <option value="arrow">Arrow</option>
                <option value="circle">Circle</option>
                <option value="diamond">Diamond</option>
              </select>
            </div>

            {/* Start Marker */}
            <div className="mb-4">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Start Marker
              </label>
              <select
                value={selectedEdge.data?.startMarker || 'none'}
                onChange={(e) => handleEdgeChange('startMarker', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
              >
                <option value="none">None</option>
                <option value="arrow">Arrow</option>
                <option value="circle">Circle</option>
                <option value="diamond">Diamond</option>
              </select>
            </div>

            {/* Bidirectional */}
            <div className="mb-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedEdge.data?.bidirectional || false}
                  onChange={(e) => handleEdgeChange('bidirectional', e.target.checked)}
                  className="rounded text-yellow-600 focus:ring-yellow-600"
                />
                <span className="text-xs font-medium text-gray-600">Bidirectional</span>
              </label>
            </div>
          </>
        )}

        {/* Metadata Section */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Metadata</h3>

          {Object.entries(metadata).length > 0 && (
            <div className="space-y-2 mb-4">
              {Object.entries(metadata).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center gap-2 p-2 bg-white border border-gray-200 rounded"
                >
                  <div className="flex-1">
                    <div className="text-xs font-medium text-gray-700">{key}</div>
                    <div className="text-xs text-gray-500 truncate">{value}</div>
                  </div>
                  <button
                    onClick={() => handleRemoveMetadata(key)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="space-y-2">
            <input
              type="text"
              placeholder="Key"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
            />
            <input
              type="text"
              placeholder="Value"
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-yellow-600 focus:border-transparent"
            />
            <button
              onClick={handleAddMetadata}
              className="w-full px-4 py-2 bg-yellow-600 text-white text-sm font-medium rounded hover:bg-yellow-700 transition-colors"
            >
              Add Metadata
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PropertiesPanel;
