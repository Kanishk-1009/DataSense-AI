import { Fragment } from 'react';
import { Card, CardContent, CardHeader } from '../common/Card';
import { Badge } from '../common/UIComponents';
import { Trophy } from 'lucide-react';
import type { MetricComparison } from '../../types/evaluation';

const categoryOrder = ['CORRECTNESS', 'STRUCTURAL', 'EFFICIENCY', 'DESCRIPTIVE', 'SELF-REPORTED'];

const categoryVariant: Record<string, 'cyan' | 'default' | 'amber' | 'purple' | 'green'> = {
  STRUCTURAL: 'cyan',
  DESCRIPTIVE: 'default',
  EFFICIENCY: 'amber',
  'SELF-REPORTED': 'purple',
  CORRECTNESS: 'green',
};

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return 'N/A';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(3);
  if (Array.isArray(v)) return `[${v.map(formatValue).join(', ')}]`;
  if (typeof v === 'object') return JSON.stringify(v);
  return String(v);
}

function betterLabel(v: string | null): string | null {
  if (!v) return null;
  const l = v.toLowerCase();
  if (l.includes('m4') || l.includes('single')) return 'M4';
  if (l.includes('m5') || l.includes('multi')) return 'M5';
  return v;
}

function groupByCategory(comparison: MetricComparison[]): { category: string; rows: MetricComparison[] }[] {
  const grouped = new Map<string, MetricComparison[]>();
  for (const row of comparison) {
    const list = grouped.get(row.category) ?? [];
    list.push(row);
    grouped.set(row.category, list);
  }
  const ordered: { category: string; rows: MetricComparison[] }[] = [];
  categoryOrder.forEach((c) => {
    if (grouped.has(c)) ordered.push({ category: c, rows: grouped.get(c)! });
  });
  grouped.forEach((rows, category) => {
    if (!categoryOrder.includes(category)) ordered.push({ category, rows });
  });
  return ordered;
}

export function MetricComparisonTable({ comparison }: { comparison: MetricComparison[] }) {
  const groups = groupByCategory(comparison);

  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold text-text-primary">Metric Comparison</h3>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto rounded-xl border border-border-primary">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border-primary bg-bg-glass">
                <th className="px-4 py-3 text-left font-medium text-text-secondary">Metric</th>
                <th className="px-4 py-3 text-left font-medium text-text-secondary">Category</th>
                <th className="px-4 py-3 text-left font-medium text-text-secondary">M4 Value</th>
                <th className="px-4 py-3 text-left font-medium text-text-secondary">M5 Value</th>
                <th className="px-4 py-3 text-left font-medium text-text-secondary">Better</th>
              </tr>
            </thead>
            <tbody>
              {groups.map((group, gi) => (
                <Fragment key={group.category}>
                  {gi > 0 && (
                    <tr className="bg-bg-primary/40">
                      <td colSpan={5} className="px-4 py-2" />
                    </tr>
                  )}
                  <tr className="border-b border-border-primary">
                    <td colSpan={5} className="px-4 py-2">
                      <Badge variant={categoryVariant[group.category] ?? 'default'}>
                        {group.category}
                      </Badge>
                    </td>
                  </tr>
                  {group.rows.map((row, i) => {
                    const label = betterLabel(row.better_pipeline);
                    return (
                      <tr key={`${group.category}-${i}`} className="border-b border-border-primary last:border-0 hover:bg-bg-glass transition-colors">
                        <td className="px-4 py-3 font-medium text-text-primary">{row.metric}</td>
                        <td className="px-4 py-3">
                          <Badge variant={categoryVariant[row.category] ?? 'default'}>{row.category}</Badge>
                        </td>
                        <td className="px-4 py-3 text-text-secondary">{formatValue(row.m4_value)}</td>
                        <td className="px-4 py-3 text-text-secondary">{formatValue(row.m5_value)}</td>
                        <td className="px-4 py-3">
                          {label ? (
                            <span className={`flex items-center gap-1.5 font-medium ${label === 'M4' ? 'text-accent-cyan' : 'text-accent-purple'}`}>
                              <Trophy size={14} />
                              {label}
                            </span>
                          ) : (
                            <span className="text-text-muted">—</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-text-muted mt-3">
          No single composite winner — metrics are presented as trade-offs only. Higher is better for STRUCTURAL &amp; CORRECTNESS; lower is better for EFFICIENCY.
        </p>
      </CardContent>
    </Card>
  );
}