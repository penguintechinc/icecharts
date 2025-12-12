import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface BarData {
  name: string;
  [key: string]: string | number;
}

interface BarChartProps {
  title?: string;
  subtitle?: string;
  data: BarData[];
  bars: Array<{
    key: string;
    color: string;
    name: string;
  }>;
  isLoading?: boolean;
  height?: number;
}

export default function BarChart({
  title = 'Comparison',
  subtitle,
  data,
  bars,
  isLoading = false,
  height = 300,
}: BarChartProps) {
  if (isLoading) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
          <Spinner text="Loading data..." />
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
          <p className="text-slate-400">No data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card title={title} subtitle={subtitle} padding="lg">
      <ResponsiveContainer width="100%" height={height}>
        <RechartsBarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
          <XAxis
            dataKey="name"
            stroke="#9fb3c8"
            tick={{ fontSize: 12 }}
          />
          <YAxis stroke="#9fb3c8" tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#243b53',
              border: '1px solid #334e68',
              borderRadius: '8px',
              color: '#e0e7ff',
            }}
            cursor={{ fill: '#334e68', opacity: 0.5 }}
          />
          <Legend
            wrapperStyle={{ color: '#9fb3c8' }}
          />
          {bars.map((bar) => (
            <Bar
              key={bar.key}
              dataKey={bar.key}
              fill={bar.color}
              name={bar.name}
              radius={[8, 8, 0, 0]}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </Card>
  );
}
