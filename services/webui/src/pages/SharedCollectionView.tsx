import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../client/lib/api';
import Button from '../client/components/Button';
import type { Collection, CollectionItem } from '../client/types';

export default function SharedCollectionView() {
  const { token } = useParams<{ token: string }>();
  const [collection, setCollection] = useState<Collection | null>(null);
  const [items, setItems] = useState<CollectionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSharedCollection();
  }, [token]);

  const fetchSharedCollection = async () => {
    if (!token) {
      setError('Invalid collection token');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [collectionRes, itemsRes] = await Promise.all([
        api.get<Collection>(`/collections/shared/${token}`),
        api.get<{ items?: CollectionItem[]; drawings?: CollectionItem[] }>(
          `/collections/shared/${token}/drawings`
        ),
      ]);

      setCollection(collectionRes.data);
      setItems(itemsRes.data.items || itemsRes.data.drawings || []);
    } catch (err: any) {
      console.error('Failed to fetch shared collection:', err);
      if (err.response?.status === 404) {
        setError('Collection not found');
      } else if (err.response?.status === 403) {
        setError('This collection is not shared');
      } else {
        setError('Failed to load collection');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-ice-navy-900 flex items-center justify-center">
        <div className="text-ice-gold-400 text-xl">Loading collection...</div>
      </div>
    );
  }

  if (error || !collection) {
    return (
      <div className="min-h-screen bg-ice-navy-900 flex items-center justify-center p-4">
        <div className="card max-w-md w-full text-center">
          <svg
            className="w-16 h-16 text-ice-navy-500 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
            />
          </svg>
          <p className="text-red-400 mb-6 text-lg font-medium">
            {error || 'Collection not found'}
          </p>
          <Link to="/">
            <Button>Go Home</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ice-navy-900">
      {/* Header */}
      <div className="bg-ice-navy-850 border-b border-ice-navy-700 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-ice-gold-400 mb-2">
                {collection.name}
              </h1>
              {collection.description && (
                <p className="text-ice-navy-400 text-base max-w-2xl">
                  {collection.description}
                </p>
              )}
            </div>
            <Link to="/">
              <Button variant="secondary">Close</Button>
            </Link>
          </div>

          {/* Collection Info */}
          <div className="flex items-center gap-4 text-sm text-ice-navy-500">
            <span>By {collection.owner_name}</span>
            <span>
              Created {new Date(collection.created_at).toLocaleDateString()}
            </span>
            <span className="text-ice-gold-400 font-medium">
              {items.length} drawing{items.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </div>

      {/* Collection Content */}
      <div className="max-w-7xl mx-auto p-4">
        {items.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((item) => (
              <div
                key={item.id}
                className="card hover:bg-ice-navy-850 transition-colors"
              >
                <div className="h-40 bg-ice-navy-800 rounded mb-3 flex items-center justify-center overflow-hidden border border-ice-navy-700">
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
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  )}
                </div>
                <h3 className="font-medium text-ice-gold-400 truncate mb-1">
                  {item.drawing.name}
                </h3>
                {item.drawing.description && (
                  <p className="text-xs text-ice-navy-400 truncate mb-2">
                    {item.drawing.description}
                  </p>
                )}
                <p className="text-xs text-ice-navy-500 mb-2">
                  By {item.drawing.owner_name}
                </p>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      item.drawing.visibility === 'private'
                        ? 'bg-red-900/30 text-red-400'
                        : item.drawing.visibility === 'group'
                        ? 'bg-blue-900/30 text-blue-400'
                        : 'bg-green-900/30 text-green-400'
                    }`}
                  >
                    {item.drawing.visibility}
                  </span>
                </div>
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
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-ice-navy-400 mb-4">
              This collection is empty
            </p>
          </div>
        )}

        {/* Sign Up Call-to-Action */}
        <div className="mt-12 card text-center p-8 bg-gradient-to-r from-ice-navy-850 to-ice-navy-800 border-l-4 border-ice-gold-400">
          <h2 className="text-2xl font-bold text-ice-gold-400 mb-3">
            Create Your Own Drawings
          </h2>
          <p className="text-ice-navy-400 mb-6 max-w-md mx-auto">
            Join our community to create, share, and collaborate on network diagrams
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link to="/register">
              <Button>Sign Up</Button>
            </Link>
            <Link to="/login">
              <Button variant="secondary">Sign In</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
