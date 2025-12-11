import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../client/lib/api';

interface Drawing {
  id: string;
  name: string;
  description: string;
  updated_at: string;
  created_at: string;
  owner_id: string;
}

interface ActivityItem {
  id: string;
  type: 'created' | 'updated' | 'shared' | 'commented';
  drawing: { id: string; name: string };
  user: { name: string; email: string };
  timestamp: string;
  details?: string;
}

const Dashboard: React.FC = () => {
  const [recentDrawings, setRecentDrawings] = useState<Drawing[]>([]);
  const [activityFeed, setActivityFeed] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError('');

    try {
      // Fetch recent drawings
      const drawingsResponse = await api.get<{ drawings?: Drawing[]; items?: Drawing[] }>('/drawings?page=1&per_page=5');
      const drawings = drawingsResponse.data.drawings || drawingsResponse.data.items || [];
      setRecentDrawings(drawings.slice(0, 5));

      // TODO: Fetch activity feed when dashboard stats endpoint is ready
      // For now, create mock activity from recent drawings
      const mockActivity: ActivityItem[] = drawings.slice(0, 5).map((drawing, index) => ({
        id: `activity_${index}`,
        type: index === 0 ? 'created' : 'updated',
        drawing: { id: drawing.id, name: drawing.name },
        user: { name: 'You', email: 'user@example.com' },
        timestamp: drawing.updated_at || drawing.created_at,
        details: index === 0 ? 'created a new diagram' : 'updated the diagram',
      }));
      setActivityFeed(mockActivity);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load dashboard data');
      console.error('Dashboard error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-ice-navy-900 text-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-ice-gold-400 mb-2">Dashboard</h1>
          <p className="text-ice-navy-300">
            Welcome back! Here's an overview of your recent activity.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-8">
            {/* Skeleton loaders */}
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse bg-ice-navy-800 rounded-lg h-32" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Recent Diagrams Section - Spans 2 columns */}
            <div className="lg:col-span-2">
              <div className="bg-ice-navy-800 rounded-lg border border-ice-navy-700 overflow-hidden">
                <div className="p-6 border-b border-ice-navy-700">
                  <h2 className="text-xl font-semibold text-ice-gold-400">Recent Diagrams</h2>
                  <p className="text-sm text-ice-navy-400 mt-1">Your 5 most recently updated diagrams</p>
                </div>

                {recentDrawings.length > 0 ? (
                  <div className="divide-y divide-ice-navy-700">
                    {recentDrawings.map((drawing) => (
                      <Link
                        key={drawing.id}
                        to={`/drawings/${drawing.id}`}
                        className="flex items-start justify-between p-4 hover:bg-ice-navy-700 transition-colors group"
                      >
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-white group-hover:text-ice-gold-400 transition-colors truncate">
                            {drawing.name}
                          </h3>
                          <p className="text-sm text-ice-navy-400 mt-1 truncate">
                            {drawing.description || 'No description'}
                          </p>
                          <p className="text-xs text-ice-navy-500 mt-2">
                            Updated {formatDate(drawing.updated_at)}
                          </p>
                        </div>
                        <svg className="w-4 h-4 text-ice-navy-500 group-hover:text-ice-gold-400 transition-colors flex-shrink-0 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center">
                    <svg className="w-12 h-12 text-ice-navy-600 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-ice-navy-400">No diagrams yet</p>
                    <Link to="/drawings/new" className="mt-3 inline-block px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 rounded-lg font-medium transition-colors">
                      Create Your First Diagram
                    </Link>
                  </div>
                )}
              </div>
            </div>

            {/* Activity Feed Section */}
            <div>
              <div className="bg-ice-navy-800 rounded-lg border border-ice-navy-700 overflow-hidden h-full">
                <div className="p-6 border-b border-ice-navy-700">
                  <h2 className="text-xl font-semibold text-ice-gold-400">Activity Feed</h2>
                  <p className="text-sm text-ice-navy-400 mt-1">Recent diagram activity</p>
                </div>

                {activityFeed.length > 0 ? (
                  <div className="divide-y divide-ice-navy-700 max-h-96 overflow-y-auto">
                    {activityFeed.map((item) => (
                      <Link
                        key={item.id}
                        to={`/drawings/${item.drawing.id}`}
                        className="p-4 hover:bg-ice-navy-700 transition-colors block group"
                      >
                        <div className="flex items-start gap-3">
                          <div className="w-2 h-2 rounded-full bg-ice-gold-400 mt-2 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white group-hover:text-ice-gold-400 transition-colors">
                              <span className="font-medium">{item.user.name}</span>{' '}
                              <span className="text-ice-navy-400">{item.details}</span>
                            </p>
                            <p className="text-xs text-ice-navy-500 mt-1 truncate">
                              {item.drawing.name}
                            </p>
                            <p className="text-xs text-ice-navy-600 mt-1">
                              {formatDate(item.timestamp)}
                            </p>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center">
                    <svg className="w-10 h-10 text-ice-navy-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-ice-navy-400 text-sm">No activity yet</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link
            to="/drawings/new"
            className="p-6 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 rounded-lg transition-colors font-medium text-center"
          >
            <svg className="w-6 h-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create New Diagram
          </Link>

          <Link
            to="/drawings"
            className="p-6 bg-ice-navy-800 hover:bg-ice-navy-700 border border-ice-navy-700 rounded-lg transition-colors font-medium text-center text-ice-gold-400"
          >
            <svg className="w-6 h-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h12a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" />
            </svg>
            Browse Diagrams
          </Link>

          <Link
            to="/templates"
            className="p-6 bg-ice-navy-800 hover:bg-ice-navy-700 border border-ice-navy-700 rounded-lg transition-colors font-medium text-center text-ice-gold-400"
          >
            <svg className="w-6 h-6 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.5a2 2 0 00-1 .267V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4z" />
            </svg>
            Browse Templates
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
