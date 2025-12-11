import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface TopUser {
  user_id: string;
  username: string;
  drawing_count: number;
}

interface TopUsersTableProps {
  title?: string;
  subtitle?: string;
  data: TopUser[];
  isLoading?: boolean;
  maxRows?: number;
}

export default function TopUsersTable({
  title = 'Top Users',
  subtitle = 'By drawing count',
  data,
  isLoading = false,
  maxRows = 10,
}: TopUsersTableProps) {
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

  const maxDrawings = Math.max(...displayData.map((u) => u.drawing_count));

  return (
    <Card title={title} subtitle={subtitle} padding="lg">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Rank</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Username</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-300">User ID</th>
              <th className="text-right py-3 px-4 font-semibold text-slate-300">Drawings</th>
              <th className="text-left py-3 px-4 font-semibold text-slate-300">Activity</th>
            </tr>
          </thead>
          <tbody>
            {displayData.map((user, index) => {
              const percentage = (user.drawing_count / maxDrawings) * 100;
              return (
                <tr
                  key={user.user_id}
                  className="border-b border-slate-800 hover:bg-slate-700/50 transition-colors"
                >
                  <td className="py-3 px-4 text-slate-400">#{index + 1}</td>
                  <td className="py-3 px-4">
                    <span className="font-medium text-white">{user.username}</span>
                  </td>
                  <td className="py-3 px-4 text-slate-400 font-mono text-xs">
                    {user.user_id.substring(0, 12)}...
                  </td>
                  <td className="py-3 px-4 text-right">
                    <span className="inline-block px-3 py-1 rounded-full bg-ice-gold-400/20 text-ice-gold-400 font-semibold">
                      {user.drawing_count.toLocaleString()}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2 w-24">
                      <div className="flex-1 h-2 rounded-full bg-slate-700 overflow-hidden">
                        <div
                          className="h-full bg-ice-gold-400 transition-all duration-300"
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
