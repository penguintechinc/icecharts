import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Button from '../components/Button';
import { AnalyticsCard } from '../components/common/AnalyticsCard';
import type { Drawing, DrawingAnalytics } from '../types';

export default function DrawingDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [drawing, setDrawing] = useState<Drawing | null>(null);
  const [analytics, setAnalytics] = useState<DrawingAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showShareOptions, setShowShareOptions] = useState(false);

  useEffect(() => {
    fetchDrawingDetail();
  }, [id]);

  const fetchDrawingDetail = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<Drawing>(`/drawings/${id}`);
      setDrawing(response.data);

      // Fetch analytics if owner
      if (response.data.owner_id === user?.id) {
        fetchAnalytics();
      }
    } catch (err: any) {
      console.error('Failed to fetch drawing:', err);
      setError(err.response?.data?.error || 'Failed to load drawing');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const response = await api.get<DrawingAnalytics>(`/drawings/${id}/analytics`);
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
      setAnalytics(null);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const isOwner = drawing?.owner_id === user?.id;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-ice-gold-400 text-xl">Loading drawing details...</div>
      </div>
    );
  }

  if (error || !drawing) {
    return (
      <div className="card text-center py-12">
        <p className="text-red-400 mb-4 text-lg">{error || 'Drawing not found'}</p>
        <Link to="/drawings">
          <Button>Back to Drawings</Button>
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-ice-gold-400 mb-2">{drawing.name}</h1>
            {drawing.description && (
              <p className="text-ice-navy-400 text-base max-w-2xl mb-3">{drawing.description}</p>
            )}
            <div className="flex items-center gap-4 text-sm text-ice-navy-500">
              <span>By {drawing.owner_name}</span>
              <span>Created {new Date(drawing.created_at).toLocaleDateString()}</span>
              <span>Updated {new Date(drawing.updated_at).toLocaleDateString()}</span>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <span
                className={`text-xs px-2 py-1 rounded ${
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
                <span className="text-xs px-2 py-1 rounded bg-purple-900/30 text-purple-400">
                  Template
                </span>
              )}
            </div>
          </div>

          {isOwner && (
            <div className="flex gap-2">
              <Link to={`/drawings/${drawing.id}`}>
                <Button>Edit Drawing</Button>
              </Link>
              <button
                onClick={() => setShowShareOptions(!showShareOptions)}
                className="px-4 py-2 rounded-lg bg-ice-navy-800 text-ice-gold-400 hover:bg-ice-navy-700 transition-colors"
              >
                {showShareOptions ? 'Hide Options' : 'Share'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Share Options */}
      {isOwner && showShareOptions && (
        <div className="card mb-6">
          <h3 className="text-lg font-semibold text-ice-gold-400 mb-4">Share Options</h3>
          <p className="text-ice-navy-400 text-sm mb-4">
            Configure how this drawing can be shared with others. Use the Edit Drawing option to set the visibility and sharing settings.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-ice-navy-850 border border-ice-navy-700">
              <div className="text-sm font-medium text-ice-gold-400 mb-1">Visibility</div>
              <div className="text-ice-navy-400 text-sm capitalize">{drawing.visibility}</div>
            </div>
            <div className="p-4 rounded-lg bg-ice-navy-850 border border-ice-navy-700">
              <div className="text-sm font-medium text-ice-gold-400 mb-1">Status</div>
              <div className="text-ice-navy-400 text-sm capitalize">{drawing.visibility}</div>
            </div>
            <div className="p-4 rounded-lg bg-ice-navy-850 border border-ice-navy-700 flex items-end">
              <Link to={`/drawings/${drawing.id}`} className="w-full">
                <Button className="w-full">Edit Sharing</Button>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Drawing Preview */}
      <div className="card mb-6">
        <h3 className="text-lg font-semibold text-ice-gold-400 mb-4">Preview</h3>
        <div className="h-96 md:h-[500px] bg-ice-navy-850 rounded-lg flex items-center justify-center border-2 border-ice-navy-700 overflow-hidden">
          {drawing.thumbnail_url ? (
            <img
              src={drawing.thumbnail_url}
              alt={drawing.name}
              className="w-full h-full object-contain"
            />
          ) : (
            <div className="text-center">
              <svg
                className="w-24 h-24 text-ice-navy-600 mx-auto mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <p className="text-ice-navy-400 text-sm">No preview available</p>
            </div>
          )}
        </div>
      </div>

      {/* Analytics Section (Owner Only) */}
      {isOwner && (
        <AnalyticsCard
          analytics={analytics}
          isLoading={analyticsLoading}
          title="Drawing Analytics"
        />
      )}

      {/* Information Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-ice-gold-400 mb-4">Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-ice-navy-400 font-medium">Owner</label>
            <p className="text-ice-gold-400 mt-1">{drawing.owner_name}</p>
          </div>
          <div>
            <label className="text-sm text-ice-navy-400 font-medium">Visibility</label>
            <p className="text-ice-gold-400 mt-1 capitalize">{drawing.visibility}</p>
          </div>
          <div>
            <label className="text-sm text-ice-navy-400 font-medium">Created</label>
            <p className="text-ice-gold-400 mt-1">
              {new Date(drawing.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <label className="text-sm text-ice-navy-400 font-medium">Last Updated</label>
            <p className="text-ice-gold-400 mt-1">
              {new Date(drawing.updated_at).toLocaleString()}
            </p>
          </div>
          {drawing.group_name && (
            <div>
              <label className="text-sm text-ice-navy-400 font-medium">Group</label>
              <p className="text-ice-gold-400 mt-1">{drawing.group_name}</p>
            </div>
          )}
          <div>
            <label className="text-sm text-ice-navy-400 font-medium">Type</label>
            <p className="text-ice-gold-400 mt-1">
              {drawing.is_template ? 'Template' : 'Drawing'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
