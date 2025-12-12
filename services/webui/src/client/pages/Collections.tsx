import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Button from '../components/Button';
import type { Collection } from '../types';

type ViewMode = 'grid' | 'list';

export default function Collections() {
  const { user } = useAuth();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterShareMode, setFilterShareMode] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    total: 0,
    pages: 1,
  });

  useEffect(() => {
    fetchCollections();
  }, [searchQuery, filterShareMode, pagination.page]);

  const fetchCollections = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        per_page: '12',
        ...(searchQuery && { search: searchQuery }),
        ...(filterShareMode !== 'all' && { share_mode: filterShareMode }),
      });

      const response = await api.get<{ success: boolean; count: number; collections: Collection[] }>(
        `/collections?${params}`
      );

      setCollections(response.data.collections || []);
      setPagination({
        page: pagination.page,
        total: response.data.count || 0,
        pages: Math.ceil((response.data.count || 0) / 12) || 1,
      });
    } catch (err) {
      console.error('Failed to fetch collections:', err);
      setCollections([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleFilterChange = (value: string) => {
    setFilterShareMode(value);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleDelete = async (collectionId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm('Delete this collection? This will not delete the drawings.')) {
      return;
    }

    try {
      await api.delete(`/collections/${collectionId}`);
      fetchCollections();
    } catch (err) {
      console.error('Failed to delete collection:', err);
    }
  };

  const getShareStatusBadge = (collection: Collection) => {
    if (collection.share_mode === 'link_only') {
      return (
        <span className="text-xs px-2 py-0.5 rounded bg-blue-900/30 text-blue-400">
          Link sharing
        </span>
      );
    } else if (collection.share_mode === 'registered_users') {
      return (
        <span className="text-xs px-2 py-0.5 rounded bg-green-900/30 text-green-400">
          Registered users
        </span>
      );
    } else if (collection.is_public) {
      return (
        <span className="text-xs px-2 py-0.5 rounded bg-purple-900/30 text-purple-400">
          Public
        </span>
      );
    }
    return (
      <span className="text-xs px-2 py-0.5 rounded bg-gray-900/30 text-gray-400">
        Private
      </span>
    );
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ice-gold-400">Collections</h1>
          <p className="text-ice-navy-400 mt-1">
            {pagination.total} collection{pagination.total !== 1 ? 's' : ''} total
          </p>
        </div>
        <Link to="/collections/new">
          <Button>Create New Collection</Button>
        </Link>
      </div>

      {/* Filters and Search */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search collections..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Share Mode Filter */}
          <select
            value={filterShareMode}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="input md:w-48"
          >
            <option value="all">All Collections</option>
            <option value="private">Private</option>
            <option value="link_only">Link Sharing</option>
            <option value="registered_users">Registered Users</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                viewMode === 'grid'
                  ? 'bg-ice-gold-600 text-white'
                  : 'bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700'
              }`}
              title="Grid View"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                viewMode === 'list'
                  ? 'bg-ice-gold-600 text-white'
                  : 'bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700'
              }`}
              title="List View"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Collections Grid/List */}
      {isLoading ? (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
              : 'space-y-4'
          }
        >
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              {viewMode === 'grid' && (
                <div className="h-32 bg-ice-navy-700 rounded mb-3"></div>
              )}
              <div className="h-4 bg-ice-navy-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-ice-navy-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : collections.length > 0 ? (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {collections.map((collection) => (
                <div key={collection.id} className="relative">
                  <Link
                    to={`/collections/${collection.id}`}
                    className="card hover:bg-ice-navy-850 transition-colors group block"
                  >
                    {/* Thumbnail */}
                    <div className="h-32 bg-ice-navy-800 rounded mb-3 flex items-center justify-center overflow-hidden">
                      {collection.thumbnail_url ? (
                        <img
                          src={collection.thumbnail_url}
                          alt={collection.name}
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
                            d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                          />
                        </svg>
                      )}
                    </div>

                    <h3 className="font-medium text-ice-gold-400 group-hover:text-ice-gold-300 truncate mb-1">
                      {collection.name}
                    </h3>
                    {collection.description && (
                      <p className="text-xs text-ice-navy-400 mb-2 line-clamp-2">
                        {collection.description}
                      </p>
                    )}
                    <p className="text-xs text-ice-navy-500 mb-2">
                      Updated {new Date(collection.updated_at).toLocaleDateString()}
                    </p>

                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      {getShareStatusBadge(collection)}
                      <span className="text-xs px-2 py-0.5 rounded bg-ice-navy-800 text-ice-navy-400">
                        {collection.drawing_count} drawing{collection.drawing_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </Link>

                  {/* Actions Menu (Only for Owner) */}
                  {collection.owner_id === user?.id && (
                    <div className="absolute top-3 right-3 z-10">
                      <button
                        onClick={(e) => handleDelete(collection.id, e)}
                        className="p-2 rounded-lg bg-red-600/80 hover:bg-red-600 text-white transition-colors"
                        title="Delete collection"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {collections.map((collection) => (
                <Link
                  key={collection.id}
                  to={`/collections/${collection.id}`}
                  className="card hover:bg-ice-navy-850 transition-colors flex items-center gap-4 relative"
                >
                  <div className="w-16 h-16 bg-ice-navy-800 rounded flex-shrink-0 flex items-center justify-center overflow-hidden">
                    {collection.thumbnail_url ? (
                      <img
                        src={collection.thumbnail_url}
                        alt={collection.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        className="w-8 h-8 text-ice-navy-600"
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
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-ice-gold-400 truncate">
                      {collection.name}
                    </h3>
                    {collection.description && (
                      <p className="text-sm text-ice-navy-400 truncate">
                        {collection.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <span className="text-xs text-ice-navy-500">
                        {new Date(collection.updated_at).toLocaleDateString()}
                      </span>
                      {getShareStatusBadge(collection)}
                      <span className="text-xs px-2 py-0.5 rounded bg-ice-navy-800 text-ice-navy-400">
                        {collection.drawing_count} drawing{collection.drawing_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>

                  {/* Actions Menu (Only for Owner) */}
                  {collection.owner_id === user?.id && (
                    <button
                      onClick={(e) => handleDelete(collection.id, e)}
                      className="p-2 rounded-lg bg-red-600/80 hover:bg-red-600 text-white transition-colors"
                      title="Delete collection"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </button>
                  )}
                </Link>
              ))}
            </div>
          )}

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page - 1 }))
                }
                disabled={pagination.page === 1}
                className="px-3 py-2 rounded-lg bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-ice-navy-400">
                Page {pagination.page} of {pagination.pages}
              </span>
              <button
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page + 1 }))
                }
                disabled={pagination.page === pagination.pages}
                className="px-3 py-2 rounded-lg bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
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
              d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
            />
          </svg>
          <p className="text-ice-navy-400 mb-4">
            {searchQuery || filterShareMode !== 'all'
              ? 'No collections found matching your filters'
              : 'No collections yet'}
          </p>
          <Link to="/collections/new">
            <Button>Create Your First Collection</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
