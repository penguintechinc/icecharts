import React from 'react';
import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface TopDrawing {
  drawing_id: string;
  title: string;
  share_count: number;
}

interface TopDrawingsTableProps {
  title?: string;
  subtitle?: string;
  data: TopDrawing[];
  isLoading?: boolean;
  maxRows?: number;
}

export default function TopDrawingsTable({
  title = 'Top Drawings',
  subtitle = 'By share count',
  data,
  isLoading = false,
  maxRows = 10,
}: TopDrawingsTableProps) {
  if (isLoading) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center h-64">
          <Spinner text="Loading data..." />
        </div>
      </Card>
    );
  }

  const displayData = data.slice(0, maxRows);

  if (!displayData || displayData.length === 0) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-400">No data available</p>
        </div>
      </Card>
    );
  }

  const maxShares = Math.max(...displayData.map((d) => d.share_count));

  return (
    <Card title={title} subtitle={subtitle} padding="lg">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Rank</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Title</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Drawing ID</th>
              <th className="text-right py-3 px-4 font-semibold text-slate-300">Shares</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Popularity</th>
            </tr>
          </thead>
          <tbody>
            {displayData.map((drawing, index) => {
              const percentage = (drawing.share_count / maxShares) * 100;
              return (
                <tr
                  key={drawing.drawing_id}
                  className="border-b border-slate-800 hover:bg-slate-700/50 transition-colors"
                >
                  <td className="py-3 px-4 text-slate-400">#{index + 1}</td>
                  <td className="py-3 px-4">
                    <span className="font-medium text-white truncate max-w-xs block">
                      {drawing.title}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-xs">
                    {drawing.drawing_id.substring(0, 12)}...
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-block px-3 py-1 rounded-full bg-ice-blue-500/20 text-ice-blue-300 font-semibold">
                      {drawing.share_count.toLocaleString()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2 w-24">
                      <div className="flex-1 h-2 rounded-full bg-slate-700 overflow-hidden">
                        <div
                          className="h-full bg-ice-blue-500 transition-all duration-300"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-400">{percentage.toFixed(0)}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
