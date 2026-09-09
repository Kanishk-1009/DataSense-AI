import { type ReactNode } from 'react';

interface BadgeProps {
  children: ReactNode;
  variant?: 'default' | 'cyan' | 'purple' | 'green' | 'amber' | 'red';
  size?: 'sm' | 'md';
}

const variants = {
  default: 'bg-bg-glass text-text-secondary border-border-primary',
  cyan: 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/20',
  purple: 'bg-accent-purple/10 text-accent-purple border-accent-purple/20',
  green: 'bg-green-500/10 text-green-400 border-green-500/20',
  amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  red: 'bg-red-500/10 text-red-400 border-red-500/20',
};

export function Badge({ children, variant = 'default', size = 'sm' }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center rounded-full border font-medium
        ${variants[variant]}
        ${size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm'}
      `}
    >
      {children}
    </span>
  );
}

interface TabsProps {
  tabs: Array<{ id: string; label: string }>;
  activeTab: string;
  onChange: (id: string) => void;
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 p-1 rounded-lg bg-bg-glass border border-border-primary">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`
            px-4 py-2 rounded-md text-sm font-medium transition-all duration-200
            ${
              activeTab === tab.id
                ? 'bg-bg-card text-text-primary shadow-sm'
                : 'text-text-muted hover:text-text-secondary'
            }
          `}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  placeholder?: string;
  className?: string;
}

export function Select({ value, onChange, options, placeholder, className = '' }: SelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`
        px-3 py-2 rounded-lg text-sm bg-bg-card border border-border-primary
        text-text-primary focus:outline-none focus:border-accent-cyan/50
        transition-colors appearance-none cursor-pointer
        ${className}
      `}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}

export function DataTable({
  columns,
  data,
  maxRows = 20,
}: {
  columns: Array<{ key: string; label: string; sortable?: boolean }>;
  data: Record<string, unknown>[];
  maxRows?: number;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border-primary">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border-primary bg-bg-glass">
            {columns.map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left font-medium text-text-secondary"
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, maxRows).map((row, i) => (
            <tr
              key={i}
              className="border-b border-border-primary last:border-0 hover:bg-bg-glass transition-colors"
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3 text-text-primary">
                  {String(row[col.key] ?? '-')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > maxRows && (
        <div className="px-4 py-3 text-xs text-text-muted border-t border-border-primary">
          Showing {maxRows} of {data.length} rows
        </div>
      )}
    </div>
  );
}
