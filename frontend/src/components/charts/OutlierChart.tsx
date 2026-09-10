import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { OutlierInfo } from '../../types/analysis';

interface OutlierChartProps {
  outliers: Record<string, OutlierInfo>;
  maxBars?: number;
  height?: number;
}

export function OutlierChart({ outliers, maxBars = 10, height = 280 }: OutlierChartProps) {
  const data = useMemo(() => {
    return (Object.entries(outliers) as [string, OutlierInfo][])
      .filter(([, v]) => v.count > 0)
      .map(([name, v]) => ({
        name: name.length > 12 ? name.slice(0, 10) + '…' : name,
        fullName: name,
        count: v.count,
        percentage: v.percentage,
        consensus: v.consensus_count,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, maxBars);
  }, [outliers, maxBars]);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted text-sm" style={{ height }}>
        No outliers detected in numeric features
      </div>
    );
  }

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
          <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
            contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#f0f0f5' }}
            formatter={(value: any, _name: any, _item: any, _index: number, tooltipPayload: any) => {
              const row = tooltipPayload?.payload as { fullName?: string; percentage?: number; consensus?: number } | undefined;
              return [`${value} (${row?.percentage ?? 0}%)`, row?.fullName ?? 'Outliers'];
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill="#fb923c" fillOpacity={0.85 - i * 0.05} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}