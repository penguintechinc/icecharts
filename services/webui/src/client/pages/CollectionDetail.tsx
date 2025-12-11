import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Button from '../components/Button';
import Card from '../components/Card';
import type { Collection, CollectionItem, CollectionAnalytics } from '../types';

export default function CollectionDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [collection, setCollection] = useState<Collection | null>(null);
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [analytics, setAnalytics] = useState<CollectionAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [draggedItem, setDraggedItem] = useState<number | null>(null);
  const [showShareControls, setShowShareControls] = useState(false);
  const [shareToken, setShareToken] = useState<string | null>(null);
  const [shareMode, setShareMode] = useState<'private' | 'link_only' | 'registered_users'>('private');

  useEffect(() => {
    fetchCollectionData();
  }, [id]);

  const fetchCollectionData = async () => {
    setIsLoading(true);
    try {
      const [collectionRes, itemsRes] = await Promise.all([
        api.get<Collection>(`/collections/${id}`),
        api.get<{ items?: CollectionItem[]; drawings?: CollectionItem[] }>(
          `/collections/${id}/drawings`
        ),
      ]);

      const collectionData = collectionRes.data;
      setCollection(collectionData);
      setEditName(collectionData.name);
      setEditDescription(collectionData.description || '');
      setShareToken(collectionData.share_token);
      setShareMode(collectionData.share_mode);
      setItems(itemsRes.data.items || itemsRes.data.drawings || []);

      // Fetch analytics if owner
      if (collectionData.owner_id === user?.id) {
        try {
          const analyticsRes = await api.get<CollectionAnalytics>(
            `/collections/${id}/analytics`
          );
          setAnalytics(analyticsRes.data);
        } catch (err) {
          console.error('Failed to fetch analytics:', err);
        }
      }
    } catch (err) {
      console.error('Failed to fetch collection data:', err);
      setItems([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!editName.trim()) {
      alert('Collection name is required');
      return;
    }

    setIsSaving(true);
    try {
      await api.put(`/collections/${id}`, {
        name: editName,
        description: editDescription || null,
      });
      setIsEditMode(false);
      fetchCollectionData();
    } catch (err) {
      console.error('Failed to update collection:', err);
      alert('Failed to update collection');
    } finally {
      setIsSaving(false);
    }
  };

  const handleGenerateShareToken = async () => {
    try {
      const response = await api.post<{ token: string }>(`/collections/${id}/share/token`);
      setShareToken(response.data.token);
      fetchCollectionData();
    } catch (err) {
      console.error('Failed to generate share token:', err);
      alert('Failed to generate share link');
    }
  };

  const handleUpdateShareMode = async (mode: 'private' | 'link_only' | 'registered_users') => {
    try {
      await api.put(`/collections/${id}`, {
        share_mode: mode,
      });
      setShareMode(mode);
      fetchCollectionData();
    } catch (err) {
      console.error('Failed to update share mode:', err);
      alert('Failed to update share mode');
    }
  };

  const handleCopyShareLink = () => {
    if (!shareToken) return;
    const shareUrl = `${window.location.origin}/shared/collections/${shareToken}`;
    navigator.clipboard.writeText(shareUrl);
    alert('Share link copied to clipboard!');
  };

  const handleRemoveDrawing = async (itemId: number) => {
    if (!confirm('Remove this drawing from the collection?')) return;

    try {
      const item = items.find((i) => i.id === itemId);
      if (!item) return;

      await api.delete(`/collections/${id}/drawings/${item.drawing_id}`);
      fetchCollectionData();
    } catch (err) {
      console.error('Failed to remove drawing:', err);
      alert('Failed to remove drawing');
    }
  };

  const handleDragStart = (itemId: number) => {
    setDraggedItem(itemId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = async (targetItemId: number) => {
    if (draggedItem === null || draggedItem === targetItemId) {
      setDraggedItem(null);
      return;
    }

    const draggedIndex = items.findIndex((item) => item.id === draggedItem);
    const targetIndex = items.findIndex((item) => item.id === targetItemId);

    if (draggedIndex === -1 || targetIndex === -1) {
      setDraggedItem(null);
      return;
    }

    // Reorder items locally for immediate feedback
    const newItems = [...items];
    const [movedItem] = newItems.splice(draggedIndex, 1);
    newItems.splice(targetIndex, 0, movedItem);
    setItems(newItems);

    // Update order on server
    try {
      const reorderedItems = newItems.map((item, index) => ({
        drawing_id: item.drawing_id,
        order_index: index,
      }));

      await api.put(`/collections/${id}/drawings/reorder`, {
        items: reorderedItems,
      });
    } catch (err) {
      console.error('Failed to reorder drawings:', err);
      // Revert on error
      fetchCollectionData();
    }

    setDraggedItem(null);
  };

  const handleDeleteCollection = async () => {
    if (!confirm('Delete this collection? This will not delete the drawings.')) return;

    try {
      await api.delete(`/collections/${id}`);
      navigate('/collections');
    } catch (err) {
      console.error('Failed to delete collection:', err);
      alert('Failed to delete collection');
    }
  };

  const isOwner = collection?.owner_id === user?.id;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-ice-gold-400 text-xl">Loading collection...</div>
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="card text-center">
        <p className="text-red-400 mb-4">Collection not found</p>
        <Link to="/collections">
          <Button>Back to Collections</Button>
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        {isEditMode ? (
          <div className="card">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Collection Name
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="input w-full"
                  placeholder="Collection name"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Description
                </label>
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="input w-full h-24 resize-none"
                  placeholder="Describe this collection..."
                />
              </div>
              <div className="flex gap-3">
                <Button onClick={handleSaveEdit} isLoading={isSaving}>
                  Save Changes
                </Button>
                <Button
                  onClick={() => {
                    setIsEditMode(false);
                    setEditName(collection.name);
                    setEditDescription(collection.description || '');
                  }}
                  variant="secondary"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-ice-gold-400">{collection.name}</h1>
              {collection.description && (
                <p className="text-ice-navy-400 mt-2">{collection.description}</p>
              )}
              <p className="text-ice-navy-500 text-sm mt-2">
                Created {new Date(collection.created_at).toLocaleDateString()} by{' '}
                {collection.owner_name}
              </p>
              <div className="flex items-center gap-2 mt-2">
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    collection.share_mode === 'link_only'
                      ? 'bg-blue-900/30 text-blue-400'
                      : collection.share_mode === 'registered_users'
                      ? 'bg-green-900/30 text-green-400'
                      : 'bg-gray-900/30 text-gray-400'
                  }`}
                >
                  {collection.share_mode === 'link_only'
                    ? 'Link sharing enabled'
                    : collection.share_mode === 'registered_users'
                    ? 'Registered users only'
                    : 'Private'}
                </span>
              </div>
            </div>
            {isOwner && (
              <div className="flex gap-2">
                <Button onClick={() => setIsEditMode(true)} variant="secondary">
                  Edit
                </Button>
                <Button
                  onClick={() => setShowShareControls(!showShareControls)}
                  variant="secondary"
                >
                  {showShareControls ? 'Hide' : 'Share'}
                </Button>
                <Button onClick={handleDeleteCollection} variant="danger">
                  Delete
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Share Controls Section */}
      {isOwner && showShareControls && (
        <Card title="Share Settings" className="mb-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                Share Mode
              </label>
              <div className="space-y-2">
                <label className="flex items-center gap-3 p-3 rounded-lg border-2 border-ice-navy-600 cursor-pointer hover:border-ice-navy-500">
                  <input
                    type="radio"
                    name="shareMode"
                    value="private"
                    checked={shareMode === 'private'}
                    onChange={(e) => handleUpdateShareMode(e.target.value as any)}
                    className="text-ice-gold-500"
                  />
                  <div>
                    <div className="font-medium text-ice-gold-400">Private</div>
                    <div className="text-xs text-ice-navy-400">Only you can access</div>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 rounded-lg border-2 border-ice-navy-600 cursor-pointer hover:border-ice-navy-500">
                  <input
                    type="radio"
                    name="shareMode"
                    value="link_only"
                    checked={shareMode === 'link_only'}
                    onChange={(e) => handleUpdateShareMode(e.target.value as any)}
                    className="text-ice-gold-500"
                  />
                  <div>
                    <div className="font-medium text-ice-gold-400">Link Sharing</div>
                    <div className="text-xs text-ice-navy-400">
                      Anyone with the link can view
                    </div>
                  </div>
                </label>
                <label className="flex items-center gap-3 p-3 rounded-lg border-2 border-ice-navy-600 cursor-pointer hover:border-ice-navy-500">
                  <input
                    type="radio"
                    name="shareMode"
                    value="registered_users"
                    checked={shareMode === 'registered_users'}
                    onChange={(e) => handleUpdateShareMode(e.target.value as any)}
                    className="text-ice-gold-500"
                  />
                  <div>
                    <div className="font-medium text-ice-gold-400">Registered Users</div>
                    <div className="text-xs text-ice-navy-400">
                      Only registered users can view
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {shareMode !== 'private' && (
              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Share Link
                </label>
                {shareToken ? (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={`${window.location.origin}/shared/collections/${shareToken}`}
                      readOnly
                      className="input flex-1 bg-ice-navy-800"
                    />
                    <Button onClick={handleCopyShareLink} variant="secondary">
                      Copy
                    </Button>
                    <Button onClick={handleGenerateShareToken} variant="secondary">
                      Regenerate
                    </Button>
                  </div>
                ) : (
                  <Button onClick={handleGenerateShareToken}>Generate Share Link</Button>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Analytics Section (Owner Only) */}
      {isOwner && analytics && (
        <Card title="Analytics" className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-ice-navy-850">
              <div className="text-2xl font-bold text-ice-gold-400">{analytics.view_count}</div>
              <div className="text-sm text-ice-navy-400">Total Views</div>
            </div>
            <div className="p-4 rounded-lg bg-ice-navy-850">
              <div className="text-2xl font-bold text-ice-gold-400">
                {analytics.unique_viewers}
              </div>
              <div className="text-sm text-ice-navy-400">Unique Viewers</div>
            </div>
            <div className="p-4 rounded-lg bg-ice-navy-850">
              <div className="text-2xl font-bold text-ice-gold-400">
                {analytics.last_accessed
                  ? new Date(analytics.last_accessed).toLocaleDateString()
                  : 'Never'}
              </div>
              <div className="text-sm text-ice-navy-400">Last Accessed</div>
            </div>
          </div>

          {analytics.recent_accesses.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-ice-gold-400 mb-2">Recent Access</h4>
              <div className="space-y-2">
                {analytics.recent_accesses.slice(0, 5).map((access, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between text-sm p-2 rounded bg-ice-navy-850"
                  >
                    <span className="text-ice-navy-400">
                      {access.user_name || 'Anonymous'}
                    </span>
                    <span className="text-ice-navy-500">
                      {new Date(access.accessed_at).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Drawings Grid */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-ice-gold-400">
          Drawings ({items.length})
        </h2>
        {isOwner && (
          <Link to={`/collections/${id}/add-drawing`}>
            <Button>Add Drawing</Button>
          </Link>
        )}
      </div>

      {items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => (
            <div
              key={item.id}
              draggable={isOwner}
              onDragStart={() => handleDragStart(item.id)}
              onDragOver={handleDragOver}
              onDrop={() => handleDrop(item.id)}
              className={`relative ${isOwner ? 'cursor-move' : ''}`}
            >
              <Link
                to={`/drawings/${item.drawing_id}`}
                className="card hover:bg-ice-navy-850 transition-colors block"
              >
                <div className="h-32 bg-ice-navy-800 rounded mb-3 flex items-center justify-center overflow-hidden">
                  {item.drawing.thumbnail_url ? (
                    <img
                      src={item.drawing.thumbnail_url}
                      alt={item.drawing.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <svg
                      className="w-12 h-12 text-ice-navy-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
                      />
                    </svg>
                  )}
                </div>
                <h3 className="font-medium text-ice-gold-400 truncate mb-1">
                  {item.drawing.name}
                </h3>
                <p className="text-xs text-ice-navy-400">By {item.drawing.owner_name}</p>
                <p className="text-xs text-ice-navy-500">
                  Added {new Date(item.added_at).toLocaleDateString()}
                </p>
              </Link>

              {/* Remove button (Owner Only) */}
              {isOwner && (
                <button
                  onClick={() => handleRemoveDrawing(item.id)}
                  className="absolute top-3 right-3 z-10 p-2 rounded-lg bg-red-600/80 hover:bg-red-600 text-white transition-colors"
                  title="Remove from collection"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <svg
            className="w-16 h-16 text-ice-navy-600 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
            />
          </svg>
          <p className="text-ice-navy-400 mb-4">No drawings in this collection yet</p>
          {isOwner && (
            <Link to={`/collections/${id}/add-drawing`}>
              <Button>Add Your First Drawing</Button>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
