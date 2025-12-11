import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Button from '../common/Button';
import Card from '../common/Card';
import Spinner from '../common/Spinner';
import apiClient from '../../lib/api';

interface Drawing {
  id: string;
  title: string;
  thumbnail?: string;
  lastModified: Date;
  ownerName: string;
  ownerInitials: string;
  ownerAvatar?: string;
}

interface AddDrawingDialogProps {
  collectionId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
  selectionMode?: 'single' | 'multi';
}

export default function AddDrawingDialog({
  collectionId,
  isOpen,
  onClose,
  onSuccess,
  selectionMode = 'multi',
}: AddDrawingDialogProps) {
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [filteredDrawings, setFilteredDrawings] = useState<Drawing[]>([]);
  const [selectedDrawingIds, setSelectedDrawingIds] = useState<Set<string>>(
    new Set()
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);

  // Fetch drawings on dialog open
  useEffect(() => {
    if (isOpen) {
      fetchDrawings();
    }
  }, [isOpen]);

  // Filter drawings based on search query
  useEffect(() => {
    const query = searchQuery.toLowerCase();
    const filtered = drawings.filter((drawing) =>
      drawing.title.toLowerCase().includes(query)
    );
    setFilteredDrawings(filtered);
  }, [searchQuery, drawings]);

  const fetchDrawings = async (page: number = 1) => {
    const isFirstPage = page === 1;
    setLoading(isFirstPage);
    if (!isFirstPage) setLoadingMore(true);
    setApiError(null);

    try {
      const response = await apiClient.get('/drawings', {
        params: {
          page,
          per_page: 20,
        },
      });

      const newDrawings = response.data.items || [];
      if (isFirstPage) {
        setDrawings(newDrawings);
      } else {
        setDrawings((prev) => [...prev, ...newDrawings]);
      }

      setCurrentPage(page);
      setHasMore(
        response.data.total > page * (response.data.per_page || 20)
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch drawings';
      setApiError(errorMessage);
      console.error('Fetch drawings error:', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleDrawingToggle = (drawingId: string) => {
    setSelectedDrawingIds((prev) => {
      const newSet = new Set(prev);
      if (selectionMode === 'single') {
        newSet.clear();
      }
      if (newSet.has(drawingId)) {
        newSet.delete(drawingId);
      } else {
        newSet.add(drawingId);
      }
      return newSet;
    });
  };

  const handleAddDrawings = async () => {
    if (selectedDrawingIds.size === 0) {
      return;
    }

    setLoading(true);
    setApiError(null);

    try {
      const drawingIds = Array.from(selectedDrawingIds);

      // Add each drawing to the collection
      await Promise.all(
        drawingIds.map((drawingId) =>
          apiClient.post(`/collections/${collectionId}/drawings`, {
            drawing_id: drawingId,
          })
        )
      );

      if (onSuccess) {
        onSuccess();
      }

      setSelectedDrawingIds(new Set());
      onClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to add drawings';
      setApiError(errorMessage);
      console.error('Add drawings error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedDrawingIds(new Set());
    setSearchQuery('');
    setApiError(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Add Drawings to Collection"
      size="lg"
      footer={
        <>
          <Button
            variant="ghost"
            size="md"
            onClick={handleClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleAddDrawings}
            disabled={loading || selectedDrawingIds.size === 0}
            isLoading={loading}
          >
            Add {selectedDrawingIds.size > 0 ? `(${selectedDrawingIds.size})` : ''}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* API Error Alert */}
        {apiError && (
          <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {apiError}
          </div>
        )}

        {/* Search Input */}
        <Input
          placeholder="Search drawings by name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          disabled={loading}
          type="text"
        />

        {/* Selection Mode Indicator */}
        <p className="text-xs text-slate-400">
          {selectionMode === 'single'
            ? 'Select one drawing'
            : `Select ${selectedDrawingIds.size > 0 ? selectedDrawingIds.size : 'multiple'} drawing${selectedDrawingIds.size !== 1 ? 's' : ''}`}
        </p>

        {/* Drawings Grid */}
        <div className="max-h-96 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Spinner />
            </div>
          ) : filteredDrawings.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-slate-400">
              {drawings.length === 0
                ? 'No drawings found'
                : 'No drawings match your search'}
            </div>
          ) : (
            <div className="space-y-2">
              {filteredDrawings.map((drawing) => (
                <Card
                  key={drawing.id}
                  className={`cursor-pointer transition-colors ${
                    selectedDrawingIds.has(drawing.id)
                      ? 'border-ice-gold-400 bg-slate-700/50'
                      : 'hover:border-ice-gold-400/50'
                  }`}
                  padding="sm"
                  onClick={() => handleDrawingToggle(drawing.id)}
                >
                  <div className="flex items-start gap-3">
                    {/* Checkbox */}
                    <input
                      type="checkbox"
                      checked={selectedDrawingIds.has(drawing.id)}
                      onChange={() => handleDrawingToggle(drawing.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="mt-1 h-4 w-4 text-ice-gold-400 border-slate-600 rounded focus:ring-ice-gold-400"
                    />

                    {/* Thumbnail */}
                    <div className="flex-shrink-0">
                      <div className="w-16 h-12 bg-slate-900 rounded overflow-hidden">
                        {drawing.thumbnail ? (
                          <img
                            src={drawing.thumbnail}
                            alt={drawing.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-slate-500">
                            <svg
                              className="w-5 h-5"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Drawing Info */}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-slate-100 truncate">
                        {drawing.title}
                      </h4>
                      <p className="text-xs text-slate-400 mt-1">
                        By {drawing.ownerName}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {new Date(drawing.lastModified).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* Load More Button */}
        {hasMore && !loading && filteredDrawings.length > 0 && (
          <div className="flex justify-center pt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => fetchDrawings(currentPage + 1)}
              disabled={loadingMore}
              isLoading={loadingMore}
            >
              Load More
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
