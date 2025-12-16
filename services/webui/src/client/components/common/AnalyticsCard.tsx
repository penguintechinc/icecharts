import React from 'react';
import type { CollectionAnalytics, DrawingAnalytics } from '../../types';

interface AnalyticsCardProps {
  analytics: CollectionAnalytics | DrawingAnalytics | null;
  isLoading?: boolean;
  title?: string;
}

/**
 * Reusable Analytics Card component that displays view count, unique viewers,
 * and recent access information for drawings and collections.
 */
export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({
  analytics,
  isLoading = false,
  title = 'Analytics',
}) => {
  if (isLoading) {
    return (
      <div className="card p-6 mb-6">
        <h3 className="text-lg font-semibold text-ice-gold-400 mb-4">{title}</h3>
        <div className="space-y-4">
          <div className="h-20 bg-ice-navy-800 rounded animate-pulse"></div>
          <div className="h-20 bg-ice-navy-800 rounded animate-pulse"></div>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  // Handle both collection and drawing analytics formats
  const viewCount = (analytics as any).view_count ?? (analytics as any).total_views ?? 0;
  const uniqueViewers = (analytics as any).unique_viewers ?? 0;
  const lastAccessed = (analytics as any).last_accessed;
  const recentAccesses = (analytics as any).recent_accesses ?? [];

  return (
    <div className="card p-6 mb-6">
      <h3 className="text-lg font-semibold text-ice-gold-400 mb-4">{title}</h3>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Total Views */}
        <div className="p-4 rounded-lg bg-ice-navy-850 border border-ice-navy-700 hover:border-ice-gold-400 transition-colors">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm text-ice-navy-400 font-medium mb-1">Total Views</div>
              <div className="text-3xl font-bold text-ice-gold-400">{viewCount.toLocaleString()}</div>
            </div>
            <div className="p-2 rounded-lg bg-ice-navy-900">
              <svg
                className="w-5 h-5 text-ice-gold-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Unique Viewers */}
        <div className="p-4 rounded-lg bg-ice-navy-850 border border-ice-navy-700 hover:border-ice-gold-400 transition-colors">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm text-ice-navy-400 font-medium mb-1">Unique Viewers</div>
              <div className="text-3xl font-bold text-ice-gold-400">{uniqueViewers.toLocaleString()}</div>
            </div>
            <div className="p-2 rounded-lg bg-ice-navy-900">
              <svg
                className="w-5 h-5 text-ice-gold-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4.354a4 4 0 110 5.292M15 10H9m6 0a6 6 0 11-12 0 6 6 0 0112 0z"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Last Accessed */}
        <div className="p-4 rounded-lg bg-ice-navy-850 border border-ice-navy-700 hover:border-ice-gold-400 transition-colors">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-sm text-ice-navy-400 font-medium mb-1">Last Accessed</div>
              <div className="text-ice-gold-400 font-medium">
                {lastAccessed
                  ? new Date(lastAccessed).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })
                  : 'Never'}
              </div>
              {lastAccessed && (
                <div className="text-xs text-ice-navy-500 mt-1">
                  {new Date(lastAccessed).toLocaleTimeString(undefined, {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              )}
            </div>
            <div className="p-2 rounded-lg bg-ice-navy-900">
              <svg
                className="w-5 h-5 text-ice-gold-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Access List */}
      {recentAccesses && recentAccesses.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-ice-gold-400 mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Recent Access
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {recentAccesses.slice(0, 10).map((access: any, index: number) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-ice-navy-850 border border-ice-navy-700 hover:border-ice-navy-600 transition-colors"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="p-2 rounded-lg bg-ice-navy-900">
                    <svg
                      className="w-4 h-4 text-ice-gold-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    {access.user_name || access.ip_address || access.access_ip ? (
                      <>
                        <div className="text-sm text-ice-gold-400 font-medium">
                          {access.user_name || 'Anonymous User'}
                        </div>
                        {(access.ip_address || access.access_ip) && (
                          <div className="text-xs text-ice-navy-500 truncate">
                            {access.ip_address || access.access_ip}
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-sm text-ice-navy-400">Anonymous Access</div>
                    )}
                  </div>
                </div>
                <div className="text-xs text-ice-navy-500 whitespace-nowrap ml-2">
                  {access.accessed_at
                    ? new Date(access.accessed_at).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : 'N/A'}
                </div>
              </div>
            ))}
          </div>
          {recentAccesses.length > 10 && (
            <div className="mt-3 text-xs text-ice-navy-400 text-center py-2">
              +{recentAccesses.length - 10} more accesses
            </div>
          )}
        </div>
      )}

      {/* No Data State */}
      {viewCount === 0 && recentAccesses.length === 0 && (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <svg
              className="w-12 h-12 text-ice-navy-600 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-ice-navy-400 text-sm">No access data yet</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsCard;
