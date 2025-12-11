import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Card from '../components/Card';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Types
interface DashboardStats {
  // User statistics
  total_users: number;
  active_users: number;
  new_users: number;
  verified_users: number;

  // Drawing statistics
  total_drawings: number;
  drawings_created: number;
  public_drawings: number;
  template_drawings: number;

  // Collection statistics
  total_collections: number;
  collections_created: number;

  // Share statistics
  total_drawing_shares: number;
  shares_by_type: {
    user: number;
    group: number;
    public: number;
  };
  shares_by_permission: {
    viewer: number;
    editor: number;
    admin: number;
  };

  // Collaboration statistics
  active_collaborations: number;
  total_collaboration_sessions: number;

  // Authentication statistics
  login_count: number;
  email_verifications_sent: number;
  email_verifications_completed: number;
  email_verification_rate: number;

  // Share analytics
  share_views: number;
  share_views_by_type: {
    drawing: number;
    collection: number;
  };

  // System health
  database_size_mb: number;
  storage_used_gb: number;
}

interface TimeSeriesData {
  timestamp: string;
  value: number;
}

interface TopUser {
  user_id: number;
  username: string;
  drawing_count: number;
}

interface TopDrawing {
  drawing_id: number;
  title: string;
  share_count: number;
}

type TimeRange = '1h' | '24h' | '7d' | '30d' | '90d' | 'all';

export default function AdminDashboard() {
  const { user, isAdmin } = useAuth();
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [drawingsTimeSeries, setDrawingsTimeSeries] = useState<TimeSeriesData[]>([]);
  const [loginsTimeSeries, setLoginsTimeSeries] = useState<TimeSeriesData[]>([]);
  const [collaborationsTimeSeries, setCollaborationsTimeSeries] = useState<TimeSeriesData[]>([]);
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [topDrawings, setTopDrawings] = useState<TopDrawing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard stats
  const fetchDashboardStats = async (range: TimeRange) => {
    try {
      const response = await api.get(`/admin/statistics/dashboard?time_range=${range}`);
      setStats(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch dashboard stats:', err);
      setError(err.response?.data?.message || 'Failed to load dashboard statistics');
    }
  };

  // Fetch time series data
  const fetchTimeSeries = async (metric: string, range: TimeRange) => {
    try {
      const response = await api.get(`/admin/statistics/time-series/${metric}?time_range=${range}&interval=1h`);
      return response.data.data || [];
    } catch (err) {
      console.error(`Failed to fetch time series for ${metric}:`, err);
      return [];
    }
  };

  // Fetch top users
  const fetchTopUsers = async () => {
    try {
      const response = await api.get('/admin/statistics/top-users?limit=10');
      setTopUsers(response.data.users || []);
    } catch (err) {
      console.error('Failed to fetch top users:', err);
    }
  };

  // Fetch top drawings
  const fetchTopDrawings = async () => {
    try {
      const response = await api.get('/admin/statistics/top-drawings?limit=10');
      setTopDrawings(response.data.drawings || []);
    } catch (err) {
      console.error('Failed to fetch top drawings:', err);
    }
  };

  // Fetch all data
  const fetchAllData = async () => {
    setIsLoading(true);
    await Promise.all([
      fetchDashboardStats(timeRange),
      fetchTimeSeries('drawings', timeRange).then(setDrawingsTimeSeries),
      fetchTimeSeries('logins', timeRange).then(setLoginsTimeSeries),
      fetchTimeSeries('collaborations', timeRange).then(setCollaborationsTimeSeries),
      fetchTopUsers(),
      fetchTopDrawings(),
    ]);
    setIsLoading(false);
  };

  // Initial load
  useEffect(() => {
    if (isAdmin()) {
      fetchAllData();
    }
  }, [timeRange]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    if (!isAdmin()) return;

    const interval = setInterval(() => {
      fetchAllData();
    }, 60000);

    return () => clearInterval(interval);
  }, [timeRange]);

  // Check admin access
  if (!isAdmin()) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-ice-gold-400 mb-4">Access Denied</h1>
          <p className="text-ice-navy-400">You do not have permission to access this page.</p>
        </div>
      </div>
    );
  }

  if (isLoading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-ice-gold-400 text-xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">Error</h1>
          <p className="text-ice-navy-400">{error}</p>
        </div>
      </div>
    );
  }

  // Chart colors
  const COLORS = ['#F4B860', '#6B9BD1', '#8FBC8F', '#D8A48F', '#B4A7D6', '#F49D9D'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ice-gold-400">Admin Dashboard</h1>
          <p className="text-ice-navy-400 mt-1">System statistics and health monitoring</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value as TimeRange)}
          className="px-4 py-2 bg-ice-navy-800 text-ice-gold-400 border border-ice-navy-700 rounded-lg focus:outline-none focus:border-ice-gold-600"
        >
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
          <option value="all">All Time</option>
        </select>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card title="Total Users">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-ice-gold-400">
              {stats?.total_users.toLocaleString() || 0}
            </div>
            {stats && stats.new_users > 0 && (
              <div className="text-sm text-green-400">
                +{stats.new_users} new
              </div>
            )}
          </div>
        </Card>

        <Card title="Active Users">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-ice-gold-400">
              {stats?.active_users.toLocaleString() || 0}
            </div>
            {stats && stats.total_users > 0 && (
              <div className="text-sm text-ice-navy-400">
                {((stats.active_users / stats.total_users) * 100).toFixed(1)}% of total
              </div>
            )}
          </div>
        </Card>

        <Card title="Total Drawings">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-ice-gold-400">
              {stats?.total_drawings.toLocaleString() || 0}
            </div>
            {stats && stats.drawings_created > 0 && (
              <div className="text-sm text-green-400">
                +{stats.drawings_created} created
              </div>
            )}
          </div>
        </Card>

        <Card title="Active Collaborations">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-ice-gold-400">
              {stats?.active_collaborations.toLocaleString() || 0}
            </div>
            {stats && (
              <div className="text-sm text-ice-navy-400">
                {stats.total_collaboration_sessions} total sessions
              </div>
            )}
          </div>
        </Card>

        <Card title="Collections">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-ice-gold-400">
              {stats?.total_collections.toLocaleString() || 0}
            </div>
            {stats && stats.collections_created > 0 && (
              <div className="text-sm text-green-400">
                +{stats.collections_created} created
              </div>
            )}
          </div>
        </Card>

        <Card title="Share Views">
          <div className="flex items-end justify-between">
            <div className="text-3xl font-bold text-ice-gold-400">
              {stats?.share_views.toLocaleString() || 0}
            </div>
            <div className="text-sm text-ice-navy-400">
              Public share access
            </div>
          </div>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Drawings Over Time">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={drawingsTimeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2C3E50" />
              <XAxis dataKey="timestamp" stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <YAxis stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A2332',
                  border: '1px solid #2C3E50',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#F4B860" strokeWidth={2} name="Drawings" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="User Activity">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={loginsTimeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2C3E50" />
              <XAxis dataKey="timestamp" stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <YAxis stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A2332',
                  border: '1px solid #2C3E50',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#6B9BD1" strokeWidth={2} name="Logins" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Collaborations">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={collaborationsTimeSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2C3E50" />
              <XAxis dataKey="timestamp" stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <YAxis stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A2332',
                  border: '1px solid #2C3E50',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#8FBC8F" strokeWidth={2} name="Sessions" />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Shares by Permission">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Viewer', value: stats?.shares_by_permission?.viewer || 0 },
                  { name: 'Editor', value: stats?.shares_by_permission?.editor || 0 },
                  { name: 'Admin', value: stats?.shares_by_permission?.admin || 0 },
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {[0, 1, 2].map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Shares by Type">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={[
                { label: 'User', value: stats?.shares_by_type?.user || 0 },
                { label: 'Group', value: stats?.shares_by_type?.group || 0 },
                { label: 'Public', value: stats?.shares_by_type?.public || 0 },
              ]}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#2C3E50" />
              <XAxis dataKey="label" stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <YAxis stroke="#8B9DC3" tick={{ fill: '#8B9DC3' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1A2332',
                  border: '1px solid #2C3E50',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="value" fill="#F4B860" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="API Latency">
          <div className="flex items-center justify-center h-[300px]">
            <div className="text-center">
              <div className="text-5xl font-bold text-ice-gold-400 mb-2">
                N/A
              </div>
              <div className="text-sm text-ice-navy-400">
                P95 Response Time (ms)
              </div>
              <div className="text-xs text-ice-navy-500 mt-2">
                Requires Prometheus integration
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Tables Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Top Active Users">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-ice-navy-700">
                  <th className="text-left py-3 px-4 text-ice-gold-400 font-semibold">#</th>
                  <th className="text-left py-3 px-4 text-ice-gold-400 font-semibold">Username</th>
                  <th className="text-right py-3 px-4 text-ice-gold-400 font-semibold">Drawings</th>
                </tr>
              </thead>
              <tbody>
                {topUsers.length > 0 ? (
                  topUsers.map((user, index) => (
                    <tr key={user.user_id} className="border-b border-ice-navy-800">
                      <td className="py-3 px-4 text-ice-navy-400">{index + 1}</td>
                      <td className="py-3 px-4 text-ice-gold-400">{user.username}</td>
                      <td className="py-3 px-4 text-right text-ice-navy-300">
                        {user.drawing_count.toLocaleString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-8 text-center text-ice-navy-400">
                      No data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Most Shared Drawings">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-ice-navy-700">
                  <th className="text-left py-3 px-4 text-ice-gold-400 font-semibold">#</th>
                  <th className="text-left py-3 px-4 text-ice-gold-400 font-semibold">Drawing</th>
                  <th className="text-right py-3 px-4 text-ice-gold-400 font-semibold">Shares</th>
                </tr>
              </thead>
              <tbody>
                {topDrawings.length > 0 ? (
                  topDrawings.map((drawing, index) => (
                    <tr key={drawing.drawing_id} className="border-b border-ice-navy-800">
                      <td className="py-3 px-4 text-ice-navy-400">{index + 1}</td>
                      <td className="py-3 px-4 text-ice-gold-400 truncate max-w-xs">
                        {drawing.title}
                      </td>
                      <td className="py-3 px-4 text-right text-ice-navy-300">
                        {drawing.share_count.toLocaleString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={3} className="py-8 text-center text-ice-navy-400">
                      No data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* System Health Section */}
      <Card title="System Health">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-ice-navy-850 rounded-lg p-4">
            <div className="text-sm text-ice-navy-400 mb-2">Database Size</div>
            <div className="text-2xl font-bold text-ice-gold-400">
              {stats?.database_size_mb?.toFixed(2) || '0.00'} MB
            </div>
            <div className="mt-2 text-xs text-green-400">Healthy</div>
          </div>

          <div className="bg-ice-navy-850 rounded-lg p-4">
            <div className="text-sm text-ice-navy-400 mb-2">Storage Used</div>
            <div className="text-2xl font-bold text-ice-gold-400">
              {stats?.storage_used_gb?.toFixed(2) || '0.00'} GB
            </div>
            <div className="mt-2 text-xs text-green-400">Healthy</div>
          </div>

          <div className="bg-ice-navy-850 rounded-lg p-4">
            <div className="text-sm text-ice-navy-400 mb-2">Email Verification Rate</div>
            <div className="text-2xl font-bold text-ice-gold-400">
              {stats?.email_verification_rate?.toFixed(1) || '0.0'}%
            </div>
            <div
              className={`mt-2 text-xs ${
                (stats?.email_verification_rate || 0) > 80 ? 'text-green-400' : 'text-yellow-400'
              }`}
            >
              {(stats?.email_verification_rate || 0) > 80 ? 'Healthy' : 'Warning'}
            </div>
          </div>

          <div className="bg-ice-navy-850 rounded-lg p-4">
            <div className="text-sm text-ice-navy-400 mb-2">Error Rate</div>
            <div className="text-2xl font-bold text-ice-gold-400">N/A</div>
            <div className="mt-2 text-xs text-ice-navy-500">
              Requires Prometheus integration
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
