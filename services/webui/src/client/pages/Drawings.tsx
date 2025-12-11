import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import Button from '../components/Button';
import type { Drawing } from '../types';

type ViewMode = 'grid' | 'list';

export default function Drawings() {
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterVisibility, setFilterVisibility] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    total: 0,
    pages: 1,
  });

  useEffect(() => {
    fetchDrawings();
  }, [searchQuery, filterVisibility, pagination.page]);

  const fetchDrawings = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        per_page: '12',
        ...(searchQuery && { search: searchQuery }),
        ...(filterVisibility !== 'all' && { visibility: filterVisibility }),
      });

      const response = await api.get<{ success: boolean; count: number; drawings: Drawing[] }>(
        `/drawings?${params}`
      );

      setDrawings(response.data.drawings || []);
      setPagination({
        page: pagination.page,
        total: response.data.count || 0,
        pages: Math.ceil((response.data.count || 0) / 12) || 1,
      });
    } catch (err) {
      console.error('Failed to fetch drawings:', err);
      setDrawings([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handleFilterChange = (value: string) => {
    setFilterVisibility(value);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">Drawings</h1>
          <p className="text-dark-400 mt-1">
            {pagination.total} drawing{pagination.total !== 1 ? 's' : ''} total
          </p>
        </div>
        <Link to="/drawings/new">
          <Button>Create New Drawing</Button>
        </Link>
      </div>

      {/* Filters and Search */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search drawings..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Visibility Filter */}
          <select
            value={filterVisibility}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="input md:w-48"
          >
            <option value="all">All Drawings</option>
            <option value="private">Private</option>
            <option value="group">Group</option>
            <option value="public">Public</option>
          </select>

          {/* View Mode Toggle */}
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-2 rounded-lg transition-colors ${
                viewMode === 'grid'
                  ? 'bg-gold-600 text-white'
                  : 'bg-dark-800 text-gold-400 hover:bg-dark-700'
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
                  ? 'bg-gold-600 text-white'
                  : 'bg-dark-800 text-gold-400 hover:bg-dark-700'
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

      {/* Drawings Grid/List */}
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
                <div className="h-32 bg-dark-700 rounded mb-3"></div>
              )}
              <div className="h-4 bg-dark-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-dark-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : drawings.length > 0 ? (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {drawings.map((drawing) => (
                <Link
                  key={drawing.id}
                  to={`/drawings/${drawing.id}`}
                  className="card hover:bg-dark-850 transition-colors group"
                >
                  {/* Thumbnail */}
                  <div className="h-32 bg-dark-800 rounded mb-3 flex items-center justify-center overflow-hidden">
                    {drawing.thumbnail_url ? (
                      <img
                        src={drawing.thumbnail_url}
                        alt={drawing.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        className="w-12 h-12 text-dark-600"
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

                  <h3 className="font-medium text-gold-400 group-hover:text-gold-300 truncate mb-1">
                    {drawing.name}
                  </h3>
                  <p className="text-xs text-dark-400">
                    Updated {new Date(drawing.updated_at).toLocaleDateString()}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        drawing.visibility === 'private'
                          ? 'bg-red-900/30 text-red-400'
                          : drawing.visibility === 'group'
                          ? 'bg-blue-900/30 text-blue-400'
                          : 'bg-green-900/30 text-green-400'
                      }`}
                    >
                      {drawing.visibility}
                    </span>
                    {drawing.is_template && (
                      <span className="text-xs px-2 py-0.5 rounded bg-purple-900/30 text-purple-400">
                        template
                      </span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {drawings.map((drawing) => (
                <Link
                  key={drawing.id}
                  to={`/drawings/${drawing.id}`}
                  className="card hover:bg-dark-850 transition-colors flex items-center gap-4"
                >
                  <div className="w-16 h-16 bg-dark-800 rounded flex-shrink-0 flex items-center justify-center overflow-hidden">
                    {drawing.thumbnail_url ? (
                      <img
                        src={drawing.thumbnail_url}
                        alt={drawing.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        className="w-8 h-8 text-dark-600"
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
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gold-400 truncate">
                      {drawing.name}
                    </h3>
                    {drawing.description && (
                      <p className="text-sm text-dark-400 truncate">
                        {drawing.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-dark-500">
                        {new Date(drawing.updated_at).toLocaleDateString()}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${
                          drawing.visibility === 'private'
                            ? 'bg-red-900/30 text-red-400'
                            : drawing.visibility === 'group'
                            ? 'bg-blue-900/30 text-blue-400'
                            : 'bg-green-900/30 text-green-400'
                        }`}
                      >
                        {drawing.visibility}
                      </span>
                    </div>
                  </div>
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
                className="px-3 py-2 rounded-lg bg-dark-800 text-gold-400 hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="text-dark-400">
                Page {pagination.page} of {pagination.pages}
              </span>
              <button
                onClick={() =>
                  setPagination((prev) => ({ ...prev, page: prev.page + 1 }))
                }
                disabled={pagination.page === pagination.pages}
                className="px-3 py-2 rounded-lg bg-dark-800 text-gold-400 hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="card text-center py-12">
          <p className="text-dark-400 mb-4">
            {searchQuery || filterVisibility !== 'all'
              ? 'No drawings found matching your filters'
              : 'No drawings yet'}
          </p>
          <Link to="/drawings/new">
            <Button>Create Your First Drawing</Button>
          </Link>
        </div>
      )}
    </div>
  );
}
