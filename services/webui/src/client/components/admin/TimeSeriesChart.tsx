import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface TimeSeriesData {
  timestamp: string;
  [key: string]: string | number;
}

interface TimeSeriesChartProps {
  title?: string;
  subtitle?: string;
  data: TimeSeriesData[];
  lines: Array<{
    key: string;
    color: string;
    name: string;
  }>;
  isLoading?: boolean;
  height?: number;
}

export default function TimeSeriesChart({
  title = 'Time Series',
  subtitle,
  data,
  lines,
  isLoading = false,
  height = 300,
}: TimeSeriesChartProps) {
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
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334e68" />
          <XAxis
            dataKey="timestamp"
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
            cursor={{ stroke: '#fbbf24', strokeWidth: 2 }}
          />
          <Legend
            wrapperStyle={{ color: '#9fb3c8' }}
            iconType="line"
          />
          {lines.map((line) => (
            <Line
              key={line.key}
              type="monotone"
              dataKey={line.key}
              stroke={line.color}
              name={line.name}
              strokeWidth={2}
              dot={{ fill: line.color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
