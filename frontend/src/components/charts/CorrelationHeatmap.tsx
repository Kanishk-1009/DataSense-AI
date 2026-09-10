import { Fragment, useMemo } from 'react';

function correlationColor(value: number): { background: string; color: string } {
  const abs = Math.abs(value);
  if (value >= 0) {
    return {
      background: `rgba(56, 189, 248, ${0.06 + abs * 0.75})`,
      color: abs > 0.5 ? '#f0f0f5' : '#9ca3b0',
    };
  }
  return {
    background: `rgba(248, 113, 113, ${0.06 + abs * 0.75})`,
    color: abs > 0.5 ? '#f0f0f5' : '#9ca3b0',
  };
}

function formatValue(v: number | null): string {
  if (v === null || v === undefined) return '—';
  return v.toFixed(2);
}

interface CorrelationHeatmapProps {
  matrix: Record<string, Record<string, number | null>>;
  threshold?: number;
}

/**
 * Color-coded correlation heatmap rendered as a CSS grid.
 * Cyan cells = positive correlation, red cells = negative correlation.
 */
export function CorrelationHeatmap({ matrix, threshold = 0.5 }: CorrelationHeatmapProps) {
  const cols = useMemo(() => Object.keys(matrix), [matrix]);

  if (cols.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-text-muted text-sm">
        No correlation data available
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[560px]">
        <div
          className="grid gap-px"
          style={{ gridTemplateColumns: `110px repeat(${cols.length}, minmax(44px, 1fr))` }}
        >
          <div />
          {cols.map((col) => (
            <div key={col} className="text-xs text-text-muted text-center p-1.5 truncate" title={col}>
              {col.length > 9 ? col.slice(0, 7) + '…' : col}
            </div>
          ))}
          {cols.map((row) => (
            <Fragment key={row}>
              <div className="text-xs text-text-muted flex items-center pr-2 truncate" title={row}>
                {row.length > 12 ? row.slice(0, 10) + '…' : row}
              </div>
              {cols.map((col) => {
                const val = matrix[row]?.[col];
                const display = formatValue(val);
                let style: { background: string; color: string } = { background: 'rgba(255,255,255,0.02)', color: '#6b7280' };
                if (val !== null && val !== undefined) {
                  style = correlationColor(val);
                }
                const strong = val !== null && val !== undefined && Math.abs(val) >= threshold;
                return (
                  <div
                    key={`${row}-${col}`}
                    className="flex items-center justify-center p-1.5 rounded-sm"
                    style={style}
                    title={val === null || val === undefined ? undefined : `${row} × ${col}: ${val.toFixed(4)}`}
                  >
                    <span className={`text-[11px] font-mono ${strong ? 'font-semibold' : ''}`}>{display}</span>
                  </div>
                );
              })}
            </Fragment>
          ))}
        </div>
      </div>
      {/* Legend */}
      <div className="flex items-center gap-3 mt-4 text-xs text-text-muted">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm" style={{ background: 'rgba(56,189,248,0.85)' }} />
          Positive
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm" style={{ background: 'rgba(248,113,113,0.85)' }} />
          Negative
        </span>
        <span className="text-text-muted">
          Threshold: |r| ≥ {threshold} highlighted
        </span>
      </div>
    </div>
  );
}