import { useState, useEffect } from 'react';
import Button from '../common/Button';
import Textarea from '../common/Textarea';
import Input from '../common/Input';

interface KeyValuePair {
  id: string;
  key: string;
  value: string;
}

interface NodeMetadataModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodeId: string;
  initialComments: string;
  initialMetadata: Record<string, string>;
  onSave: (comments: string, metadata: Record<string, string>) => void;
}

export default function NodeMetadataModal({
  isOpen,
  onClose,
  nodeId,
  initialComments,
  initialMetadata,
  onSave,
}: NodeMetadataModalProps) {
  const [comments, setComments] = useState<string>(initialComments);
  const [metadata, setMetadata] = useState<KeyValuePair[]>([]);

  // Initialize metadata from initialMetadata object
  useEffect(() => {
    if (isOpen) {
      setComments(initialComments);
      const metadataArray = Object.entries(initialMetadata).map(([key, value], index) => ({
        id: `${nodeId}-${index}`,
        key,
        value,
      }));
      setMetadata(metadataArray);
    }
  }, [isOpen, nodeId, initialComments, initialMetadata]);

  // Handle escape key and body overflow
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleAddMetadata = () => {
    const newId = `${nodeId}-${Date.now()}`;
    setMetadata([...metadata, { id: newId, key: '', value: '' }]);
  };

  const handleRemoveMetadata = (id: string) => {
    setMetadata(metadata.filter((item) => item.id !== id));
  };

  const handleMetadataChange = (id: string, field: 'key' | 'value', value: string) => {
    setMetadata(
      metadata.map((item) =>
        item.id === id ? { ...item, [field]: value } : item
      )
    );
  };

  const handleSave = () => {
    // Convert metadata array back to object, filtering out empty entries
    const metadataObject = metadata.reduce(
      (acc, item) => {
        if (item.key.trim()) {
          acc[item.key.trim()] = item.value.trim();
        }
        return acc;
      },
      {} as Record<string, string>
    );

    onSave(comments, metadataObject);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Dark backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal content */}
      <div
        className="relative bg-slate-800 border border-slate-700 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800">
          <h2 className="text-lg font-semibold text-ice-gold-400">
            Node Metadata - {nodeId}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors"
            aria-label="Close dialog"
          >
            <svg
              className="h-6 w-6"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-6">
          {/* Comments section */}
          <div>
            <h3 className="text-sm font-semibold text-ice-navy-300 mb-3">Comments</h3>
            <Textarea
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="Add comments about this node..."
              rows={4}
            />
          </div>

          {/* Metadata section */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-ice-navy-300">Metadata</h3>
              <button
                onClick={handleAddMetadata}
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-ice-gold-400 hover:bg-slate-700/50 border border-ice-gold-400/50 rounded-lg transition-colors"
              >
                <svg
                  className="h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M12 5v14M5 12h14" />
                </svg>
                Add Pair
              </button>
            </div>

            {metadata.length === 0 ? (
              <p className="text-sm text-slate-400 py-4">
                No metadata pairs yet. Click "Add Pair" to add key-value pairs.
              </p>
            ) : (
              <div className="space-y-3">
                {metadata.map((item) => (
                  <div key={item.id} className="flex gap-3 items-start">
                    <div className="flex-1">
                      <Input
                        placeholder="Key"
                        value={item.key}
                        onChange={(e) =>
                          handleMetadataChange(item.id, 'key', e.target.value)
                        }
                        className="text-sm"
                      />
                    </div>
                    <div className="flex-1">
                      <Input
                        placeholder="Value"
                        value={item.value}
                        onChange={(e) =>
                          handleMetadataChange(item.id, 'value', e.target.value)
                        }
                        className="text-sm"
                      />
                    </div>
                    <button
                      onClick={() => handleRemoveMetadata(item.id)}
                      className="mt-1 p-2 text-slate-400 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
                      aria-label="Remove metadata pair"
                    >
                      <svg
                        className="h-5 w-5"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M18 6L6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-700 bg-slate-800">
          <Button variant="secondary" size="md" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleSave}
            className="bg-ice-gold-400 text-slate-900 hover:bg-ice-gold-300"
          >
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}
