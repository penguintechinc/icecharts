import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Card from '../components/Card';
import type { Drawing, Group } from '../types';

export default function Dashboard() {
  const { user } = useAuth();
  const [recentDrawings, setRecentDrawings] = useState<Drawing[]>([]);
  const [recentGroups, setRecentGroups] = useState<Group[]>([]);
  const [stats, setStats] = useState({
    totalDrawings: 0,
    totalGroups: 0,
    sharedDrawings: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        const [drawingsRes, groupsRes, statsRes] = await Promise.all([
          api.get('/drawings?limit=6&sort=updated_at'),
          api.get('/groups?limit=4&sort=updated_at'),
          api.get('/dashboard/stats'),
        ]);

        setRecentDrawings(drawingsRes.data.items || []);
        setRecentGroups(groupsRes.data.items || []);
        setStats(statsRes.data || stats);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gold-400">Dashboard</h1>
        <p className="text-dark-400 mt-1">
          Welcome back, {user?.full_name || 'User'}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card title="My Drawings">
          {isLoading ? (
            <div className="animate-pulse h-12 bg-dark-700 rounded"></div>
          ) : (
            <div className="flex items-end justify-between">
              <div className="text-3xl font-bold text-gold-400">
                {stats.totalDrawings}
              </div>
              <Link
                to="/drawings"
                className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
              >
                View all →
              </Link>
            </div>
          )}
        </Card>

        <Card title="My Groups">
          {isLoading ? (
            <div className="animate-pulse h-12 bg-dark-700 rounded"></div>
          ) : (
            <div className="flex items-end justify-between">
              <div className="text-3xl font-bold text-gold-400">
                {stats.totalGroups}
              </div>
              <Link
                to="/groups"
                className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
              >
                View all →
              </Link>
            </div>
          )}
        </Card>

        <Card title="Shared with Me">
          {isLoading ? (
            <div className="animate-pulse h-12 bg-dark-700 rounded"></div>
          ) : (
            <div className="flex items-end justify-between">
              <div className="text-3xl font-bold text-gold-400">
                {stats.sharedDrawings}
              </div>
              <span className="text-sm text-dark-400">drawings</span>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Drawings */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gold-400">Recent Drawings</h2>
          <Link
            to="/drawings"
            className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
          >
            View all →
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-32 bg-dark-700 rounded mb-3"></div>
                <div className="h-4 bg-dark-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-dark-700 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : recentDrawings.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recentDrawings.map((drawing) => (
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

                {/* Drawing Info */}
                <h3 className="font-medium text-gold-400 group-hover:text-gold-300 truncate mb-1">
                  {drawing.name}
                </h3>
                <p className="text-xs text-dark-400">
                  Updated {new Date(drawing.updated_at).toLocaleDateString()}
                </p>
                {drawing.group_name && (
                  <p className="text-xs text-dark-500 mt-1">
                    Group: {drawing.group_name}
                  </p>
                )}
              </Link>
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <p className="text-dark-400 mb-4">No drawings yet</p>
            <Link
              to="/drawings/new"
              className="inline-block px-4 py-2 bg-gold-600 hover:bg-gold-700 text-white rounded-lg transition-colors"
            >
              Create Your First Drawing
            </Link>
          </div>
        )}
      </div>

      {/* Recent Groups */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gold-400">My Groups</h2>
          <Link
            to="/groups"
            className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
          >
            View all →
          </Link>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-4 bg-dark-700 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-dark-700 rounded w-full mb-2"></div>
                <div className="h-3 bg-dark-700 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : recentGroups.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recentGroups.map((group) => (
              <Link
                key={group.id}
                to={`/groups/${group.id}`}
                className="card hover:bg-dark-850 transition-colors"
              >
                <h3 className="font-medium text-gold-400 mb-2">{group.name}</h3>
                {group.description && (
                  <p className="text-sm text-dark-400 mb-3 line-clamp-2">
                    {group.description}
                  </p>
                )}
                <div className="flex items-center gap-4 text-xs text-dark-500">
                  <span>{group.member_count} members</span>
                  <span>•</span>
                  <span>{group.drawing_count} drawings</span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <p className="text-dark-400 mb-4">No groups yet</p>
            <Link
              to="/groups/new"
              className="inline-block px-4 py-2 bg-gold-600 hover:bg-gold-700 text-white rounded-lg transition-colors"
            >
              Create Your First Group
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
