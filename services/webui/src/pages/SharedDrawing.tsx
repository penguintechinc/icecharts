import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../client/lib/api';
import Button from '../client/components/Button';
import { AnalyticsCard } from '../client/components/common/AnalyticsCard';
import type { Drawing, DrawingAnalytics } from '../client/types';

export default function SharedDrawing() {
  const { token } = useParams<{ token: string }>();
  const [drawing, setDrawing] = useState<Drawing | null>(null);
  const [analytics, setAnalytics] = useState<DrawingAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSharedDrawing();
  }, [token]);

  const fetchSharedDrawing = async () => {
    if (!token) {
      setError('Invalid drawing token');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<Drawing>(`/drawings/shared/${token}`);
      setDrawing(response.data);

      // Try to fetch analytics for the shared drawing
      try {
        setAnalyticsLoading(true);
        const analyticsRes = await api.get<DrawingAnalytics>(`/drawings/${response.data.id}/analytics`);
        setAnalytics(analyticsRes.data);
      } catch (err) {
        console.error('Failed to fetch analytics:', err);
        // Analytics fetch failure is not critical for shared view
      } finally {
        setAnalyticsLoading(false);
      }
    } catch (err: any) {
      console.error('Failed to fetch shared drawing:', err);
      if (err.response?.status === 404) {
        setError('Drawing not found');
      } else if (err.response?.status === 403) {
        setError('This drawing is not shared');
      } else {
        setError('Failed to load drawing');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-ice-navy-900 flex items-center justify-center">
        <div className="text-ice-gold-400 text-xl">Loading drawing...</div>
      </div>
    );
  }

  if (error || !drawing) {
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
              d="M12 9v2m0 4v2m0 0v2m0-6v-2m0 0v-2m0 4V7a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p className="text-red-400 mb-6 text-lg font-medium">
            {error || 'Drawing not found'}
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
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-ice-gold-400 mb-2">
              {drawing.name}
            </h1>
            {drawing.description && (
              <p className="text-ice-navy-400 text-sm">
                {drawing.description}
              </p>
            )}
            <div className="flex items-center gap-4 mt-3 text-sm text-ice-navy-500">
              <span>By {drawing.owner_name}</span>
              <span>
                Created {new Date(drawing.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
          <Link to="/">
            <Button variant="secondary">Close</Button>
          </Link>
        </div>
      </div>

      {/* Drawing Viewer */}
      <div className="max-w-7xl mx-auto p-4">
        <div className="card p-6 mb-6">
          <div className="h-96 md:h-[600px] bg-ice-navy-800 rounded-lg flex items-center justify-center border-2 border-ice-navy-700 overflow-hidden">
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
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <p className="text-ice-navy-400">No preview available</p>
              </div>
            )}
          </div>

          {/* Drawing Details */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg bg-ice-navy-850">
              <div className="text-sm text-ice-navy-400 mb-1">Owner</div>
              <div className="text-ice-gold-400 font-medium">{drawing.owner_name}</div>
            </div>
            <div className="p-4 rounded-lg bg-ice-navy-850">
              <div className="text-sm text-ice-navy-400 mb-1">Visibility</div>
              <div className="text-ice-gold-400 font-medium capitalize">
                {drawing.visibility}
              </div>
            </div>
            <div className="p-4 rounded-lg bg-ice-navy-850">
              <div className="text-sm text-ice-navy-400 mb-1">Last Updated</div>
              <div className="text-ice-gold-400 font-medium">
                {new Date(drawing.updated_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>

        {/* Analytics Section */}
        <AnalyticsCard
          analytics={analytics}
          isLoading={analyticsLoading}
          title="Drawing Analytics"
        />
      </div>
    </div>
  );
}
