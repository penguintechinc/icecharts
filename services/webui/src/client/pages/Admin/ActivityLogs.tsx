import { useState, useEffect } from 'react';
import api from '../../lib/api';
import Button from '../../components/Button';
import type { ActivityLog } from '../../types';

export default function AdminActivityLogs() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState('');
  const [selectedAction, setSelectedAction] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<Array<{ id: number; name: string; email: string }>>([]);
  const [actions, setActions] = useState<string[]>([]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch logs when filters change
  useEffect(() => {
    setCurrentPage(1);
    fetchLogs(1);
  }, [debouncedSearch, selectedUser, selectedAction, dateFrom, dateTo]);

  // Fetch logs on page change
  useEffect(() => {
    if (currentPage !== 1) {
      fetchLogs(currentPage);
    }
  }, [currentPage]);

  // Fetch available users and actions on mount
  useEffect(() => {
    fetchFiltersData();
  }, []);

  const fetchLogs = async (page: number = 1) => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('per_page', '25');

      if (debouncedSearch) {
        params.append('search', debouncedSearch);
      }
      if (selectedUser) {
        params.append('user_id', selectedUser);
      }
      if (selectedAction) {
        params.append('action', selectedAction);
      }
      if (dateFrom) {
        params.append('date_from', dateFrom);
      }
      if (dateTo) {
        params.append('date_to', dateTo);
      }

      const response = await api.get<{
        items: ActivityLog[];
        total: number;
        page: number;
        per_page: number;
        pages: number;
      }>(`/admin/activity?${params.toString()}`);

      setLogs(response.data.items || []);
      setTotal(response.data.total || 0);
      setTotalPages(response.data.pages || 1);
    } catch (err) {
      console.error('Failed to fetch activity logs:', err);
      setError('Failed to load activity logs');
      setLogs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchFiltersData = async () => {
    try {
      const response = await api.get<{
        users: Array<{ id: number; name: string; email: string }>;
        actions: string[];
      }>('/admin/activity/filters');
      setUsers(response.data.users || []);
      setActions(response.data.actions || []);
    } catch (err) {
      console.error('Failed to fetch filter data:', err);
    }
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedUser('');
    setSelectedAction('');
    setDateFrom('');
    setDateTo('');
    setCurrentPage(1);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString(),
    };
  };

  const hasActiveFilters = Boolean(
    debouncedSearch || selectedUser || selectedAction || dateFrom || dateTo
  );

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">Activity Logs</h1>
          <p className="text-dark-400 mt-1">
            View user activity and system events
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gold-400 mb-2">
              Search
            </label>
            <div className="relative">
              <input
                type="text"
                placeholder="Search resource name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input w-full pl-10"
              />
              <svg
                className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-dark-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
          </div>

          {/* User Filter */}
          <div>
            <label className="block text-sm font-medium text-gold-400 mb-2">
              User
            </label>
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="input w-full"
            >
              <option value="">All Users</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.name || user.email}
                </option>
              ))}
            </select>
          </div>

          {/* Action Filter */}
          <div>
            <label className="block text-sm font-medium text-gold-400 mb-2">
              Action
            </label>
            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="input w-full"
            >
              <option value="">All Actions</option>
              {actions.map((action) => (
                <option key={action} value={action}>
                  {action}
                </option>
              ))}
            </select>
          </div>

          {/* Date From */}
          <div>
            <label className="block text-sm font-medium text-gold-400 mb-2">
              From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Date To */}
          <div>
            <label className="block text-sm font-medium text-gold-400 mb-2">
              To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="input w-full"
            />
          </div>
        </div>

        {/* Filter Actions */}
        {hasActiveFilters && (
          <div className="flex justify-end">
            <Button
              onClick={handleResetFilters}
              className="bg-dark-800 hover:bg-dark-700"
              size="sm"
            >
              Clear Filters
            </Button>
          </div>
        )}
      </div>

      {/* Activity Logs Table */}
      {isLoading ? (
        <div className="card animate-pulse">
          <div className="h-8 bg-dark-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-dark-700 rounded"></div>
            ))}
          </div>
        </div>
      ) : logs.length > 0 ? (
        <>
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-dark-700">
                    <th className="text-left py-4 px-6 text-gold-400 font-medium">
                      Timestamp
                    </th>
                    <th className="text-left py-4 px-6 text-gold-400 font-medium">
                      User
                    </th>
                    <th className="text-left py-4 px-6 text-gold-400 font-medium">
                      Action
                    </th>
                    <th className="text-left py-4 px-6 text-gold-400 font-medium">
                      Resource
                    </th>
                    <th className="text-left py-4 px-6 text-gold-400 font-medium">
                      IP Address
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => {
                    const { date, time } = formatTimestamp(log.timestamp);
                    return (
                      <tr key={log.id} className="border-b border-dark-800 hover:bg-dark-850">
                        <td className="py-4 px-6">
                          <div className="text-sm text-gold-400">{date}</div>
                          <div className="text-xs text-dark-400">{time}</div>
                        </td>
                        <td className="py-4 px-6">
                          <div className="text-gold-400 font-medium text-sm">
                            {log.user_name || '—'}
                          </div>
                          <div className="text-xs text-dark-400">{log.user_email}</div>
                        </td>
                        <td className="py-4 px-6">
                          <span className="inline-block px-3 py-1 bg-blue-900/30 text-blue-400 text-xs rounded-full">
                            {log.action}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <div className="text-sm text-dark-300">
                            {log.resource_type}
                          </div>
                          {log.resource_name && (
                            <div className="text-xs text-dark-400">
                              {log.resource_name}
                            </div>
                          )}
                        </td>
                        <td className="py-4 px-6 text-sm text-dark-400">
                          {log.ip_address || '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Info */}
          <div className="mt-4 flex items-center justify-between text-sm text-dark-400">
            <div>
              Showing {(currentPage - 1) * 25 + 1} to{' '}
              {Math.min(currentPage * 25, total)} of {total} logs
            </div>
            {totalPages > 1 && (
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  size="sm"
                  className="bg-dark-800 hover:bg-dark-700 disabled:opacity-50"
                >
                  Previous
                </Button>
                <div className="text-dark-400">
                  Page {currentPage} of {totalPages}
                </div>
                <Button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  size="sm"
                  className="bg-dark-800 hover:bg-dark-700 disabled:opacity-50"
                >
                  Next
                </Button>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="card">
          <div className="text-center py-12">
            <div className="text-dark-400 text-lg">No activity logs found</div>
            {hasActiveFilters && (
              <div className="mt-3">
                <Button
                  onClick={handleResetFilters}
                  className="bg-dark-800 hover:bg-dark-700"
                  size="sm"
                >
                  Clear Filters
                </Button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
