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

interface FeatureImportanceChartProps {
  data: Array<{ feature: string; importance: number; rank?: number; normalized_score?: number }>;
  method: 'random_forest' | 'mutual_information';
  maxItems?: number;
  height?: number;
}

const COLORS = {
  random_forest: [
    '#38bdf8', '#3ec9e8', '#38bdf8', '#4fc3f7', '#53c1f0',
    '#38bdf8', '#38bdf8', '#4fc3f7', '#38bdf8', '#3ec9e8',
  ],
  mutual_information: [
    '#a855f7', '#9333ea', '#a855f7', '#b46af7', '#a855f7',
    '#9333ea', '#a855f7', '#b46af7', '#a855f7', '#9333ea',
  ],
};

export function FeatureImportanceChart({
  data,
  method,
  maxItems = 10,
  height = 260,
}: FeatureImportanceChartProps) {
  const items = [...data].sort((a, b) => b.importance - a.importance).slice(0, maxItems);
  const key = method === 'random_forest' ? 'importance' : 'normalized_score';

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center text-text-muted text-sm" style={{ height }}>
        No feature importance data available
      </div>
    );
  }

  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={items} layout="vertical" margin={{ left: 8, right: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
          <YAxis dataKey="feature" type="category" width={95} tick={{ fill: '#6b7280', fontSize: 11 }} />
          <Tooltip
            cursor={{ fill: 'rgba(255,255,255,0.03)' }}
            contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#f0f0f5' }}
            formatter={(value: any, _name: any, _item: any, _index: number, tooltipPayload: any) => {
              const row = tooltipPayload?.payload as { rank?: number } | undefined;
              return [(typeof value === 'number' ? value.toFixed(4) : String(value)), row?.rank ? `#${row.rank}` : ''];
            }}
          />
          <Bar dataKey={key} radius={[0, 4, 4, 0]}>
            {items.map((_, i) => (
              <Cell key={i} fill={COLORS[method][i % COLORS[method].length]} fillOpacity={0.9 - i * 0.04} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}