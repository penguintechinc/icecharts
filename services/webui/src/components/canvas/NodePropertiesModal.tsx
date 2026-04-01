import React, { useState, useEffect } from 'react';
import type { Node, Edge } from '@xyflow/react';

interface NodePropertiesModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedNode: Node | null;
  selectedEdge: Edge | null;
  onUpdateNode: (nodeId: string, newData: any) => void;
  onUpdateEdge: (edgeId: string, newData: any) => void;
}

const NodePropertiesModal: React.FC<NodePropertiesModalProps> = ({
  isOpen,
  onClose,
  selectedNode,
  selectedEdge,
  onUpdateNode,
  onUpdateEdge,
}) => {
  const [activeTab, setActiveTab] = useState<'general' | 'style' | 'metadata' | 'comments'>('general');
  const [metadata, setMetadata] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [comment, setComment] = useState('');

  useEffect(() => {
    if (selectedNode?.data && typeof selectedNode.data === 'object') {
      const data = selectedNode.data as any;
      setMetadata(data.metadata || {});
      setComment(data.comments || '');
    } else if (selectedEdge?.data && typeof selectedEdge.data === 'object') {
      const data = selectedEdge.data as any;
      setMetadata(data.metadata || {});
      setComment(data.comments || '');
    } else {
      setMetadata({});
      setComment('');
    }
  }, [selectedNode, selectedEdge, isOpen]);

  if (!isOpen || (!selectedNode && !selectedEdge)) return null;

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

  const handleCommentChange = (value: string) => {
    setComment(value);
    if (selectedNode) {
      onUpdateNode(selectedNode.id, { comments: value });
    } else if (selectedEdge) {
      onUpdateEdge(selectedEdge.id, { comments: value });
    }
  };

  const isNode = !!selectedNode;
  const title = isNode ? `Node Properties: ${selectedNode.id}` : `Edge Properties: ${selectedEdge?.id}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 font-sans">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
          <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-200 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 bg-white">
          <button
            className={`px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'general' ? 'border-b-2 border-gold-500 text-gold-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('general')}
          >
            General
          </button>
          <button
            className={`px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'style' ? 'border-b-2 border-gold-500 text-gold-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('style')}
          >
            Style
          </button>
          <button
            className={`px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'metadata' ? 'border-b-2 border-gold-500 text-gold-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('metadata')}
          >
            Metadata
          </button>
          <button
            className={`px-6 py-3 text-sm font-medium transition-colors ${activeTab === 'comments' ? 'border-b-2 border-gold-500 text-gold-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('comments')}
          >
            Comments
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {activeTab === 'general' && (
            <div className="space-y-4">
              {isNode ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                    <input
                      type="text"
                      value={selectedNode.type || 'default'}
                      disabled
                      className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded text-gray-600"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Label / Text</label>
                    <input
                      type="text"
                      value={(selectedNode.data as any)?.label || (selectedNode.data as any)?.text || ''}
                      onChange={(e) =>
                        handleNodeChange(
                          (selectedNode.data as any)?.text !== undefined ? 'text' : 'label',
                          e.target.value
                        )
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 focus:border-transparent outline-none transition-all"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Position X</label>
                      <input
                        type="number"
                        value={Math.round(selectedNode.position.x)}
                        disabled
                        className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded text-gray-600"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Position Y</label>
                      <input
                        type="number"
                        value={Math.round(selectedNode.position.y)}
                        disabled
                        className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded text-gray-600"
                      />
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Label</label>
                    <input
                      type="text"
                      value={(selectedEdge?.data as any)?.label || ''}
                      onChange={(e) => handleEdgeChange('label', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 focus:border-transparent outline-none transition-all"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                      <input
                        type="text"
                        value={selectedEdge?.source || ''}
                        disabled
                        className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded text-gray-600"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Target</label>
                      <input
                        type="text"
                        value={selectedEdge?.target || ''}
                        disabled
                        className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded text-gray-600"
                      />
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'style' && (
            <div className="space-y-4">
              {isNode ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Fill Color</label>
                      <div className="flex gap-2">
                        <input
                          type="color"
                          value={(selectedNode.data as any).fillColor || '#ffffff'}
                          onChange={(e) => handleNodeChange('fillColor', e.target.value)}
                          className="h-10 w-12 rounded cursor-pointer border border-gray-300"
                        />
                        <input
                          type="text"
                          value={(selectedNode.data as any).fillColor || '#ffffff'}
                          onChange={(e) => handleNodeChange('fillColor', e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Text Color</label>
                      <div className="flex gap-2">
                        <input
                          type="color"
                          value={(selectedNode.data as any).textColor || '#000000'}
                          onChange={(e) => handleNodeChange('textColor', e.target.value)}
                          className="h-10 w-12 rounded cursor-pointer border border-gray-300"
                        />
                        <input
                          type="text"
                          value={(selectedNode.data as any).textColor || '#000000'}
                          onChange={(e) => handleNodeChange('textColor', e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Stroke Color</label>
                      <div className="flex gap-2">
                        <input
                          type="color"
                          value={(selectedNode.data as any).strokeColor || '#000000'}
                          onChange={(e) => handleNodeChange('strokeColor', e.target.value)}
                          className="h-10 w-12 rounded cursor-pointer border border-gray-300"
                        />
                        <input
                          type="text"
                          value={(selectedNode.data as any).strokeColor || '#000000'}
                          onChange={(e) => handleNodeChange('strokeColor', e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Stroke Width</label>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        value={(selectedNode.data as any).strokeWidth || 1}
                        onChange={(e) => handleNodeChange('strokeWidth', parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Font Size</label>
                    <input
                      type="number"
                      min="8"
                      max="72"
                      value={(selectedNode.data as any).fontSize || 14}
                      onChange={(e) => handleNodeChange('fontSize', parseInt(e.target.value) || 14)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Line Color</label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={(selectedEdge?.data?.strokeColor as string) || '#b1b1b7'}
                        onChange={(e) => handleEdgeChange('strokeColor', e.target.value)}
                        className="h-10 w-12 rounded cursor-pointer border border-gray-300"
                      />
                      <input
                        type="text"
                        value={(selectedEdge?.data?.strokeColor as string) || '#b1b1b7'}
                        onChange={(e) => handleEdgeChange('strokeColor', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Line Width</label>
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={(selectedEdge?.data?.strokeWidth as number) || 2}
                        onChange={(e) => handleEdgeChange('strokeWidth', parseInt(e.target.value) || 1)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Line Style</label>
                      <select
                        value={(selectedEdge?.data?.dashPattern as string) || 'solid'}
                        onChange={(e) => handleEdgeChange('dashPattern', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                      >
                        <option value="solid">Solid</option>
                        <option value="dashed">Dashed</option>
                        <option value="dotted">Dotted</option>
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Start Marker</label>
                      <select
                        value={(selectedEdge?.data?.startMarker as string) || 'none'}
                        onChange={(e) => handleEdgeChange('startMarker', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                      >
                        <option value="none">None</option>
                        <option value="arrow">Arrow</option>
                        <option value="circle">Circle</option>
                        <option value="diamond">Diamond</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">End Marker</label>
                      <select
                        value={(selectedEdge?.data?.endMarker as string) || 'arrow'}
                        onChange={(e) => handleEdgeChange('endMarker', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                      >
                        <option value="none">None</option>
                        <option value="arrow">Arrow</option>
                        <option value="circle">Circle</option>
                        <option value="diamond">Diamond</option>
                      </select>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'metadata' && (
            <div className="space-y-6">
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-800 mb-3">Add New Metadata</h3>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <input
                    type="text"
                    placeholder="Key"
                    value={newKey}
                    onChange={(e) => setNewKey(e.target.value)}
                    className="px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                  />
                  <input
                    type="text"
                    placeholder="Value"
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value)}
                    className="px-3 py-2 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 outline-none transition-all"
                  />
                </div>
                <button
                  onClick={handleAddMetadata}
                  className="w-full px-4 py-2 bg-gold-500 text-white text-sm font-medium rounded hover:bg-gold-600 transition-colors shadow-sm"
                >
                  Add Metadata Pair
                </button>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-800 mb-3">Existing Metadata</h3>
                {Object.entries(metadata).length > 0 ? (
                  <div className="border border-gray-200 rounded-lg divide-y divide-gray-200 shadow-sm overflow-hidden">
                    {Object.entries(metadata).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between p-3 bg-white hover:bg-gray-50 transition-colors">
                        <div className="flex-1 min-w-0 pr-4">
                          <p className="text-sm font-medium text-gray-700 truncate">{key}</p>
                          <p className="text-sm text-gray-500 truncate">{value}</p>
                        </div>
                        <button
                          onClick={() => handleRemoveMetadata(key)}
                          className="text-red-500 hover:text-red-700 p-1.5 rounded-full hover:bg-red-50 transition-colors"
                          title="Remove metadata"
                        >
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic text-center py-4 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                    No metadata defined for this element.
                  </p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'comments' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes / Comments</label>
                <textarea
                  value={comment}
                  onChange={(e) => handleCommentChange(e.target.value)}
                  placeholder="Add technical notes or comments here..."
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-gold-500 h-64 resize-none outline-none transition-all shadow-inner"
                />
                <p className="mt-2 text-xs text-gray-500 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  These comments are stored with the element and can be used for documentation.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gold-500 text-white font-semibold rounded hover:bg-gold-600 transition-colors shadow-sm"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodePropertiesModal;
