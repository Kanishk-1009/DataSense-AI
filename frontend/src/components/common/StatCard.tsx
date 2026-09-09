import { type LucideIcon } from 'lucide-react';
import { motion } from 'framer-motion';

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  sublabel?: string;
  color?: string;
  index?: number;
}

export function StatCard({ icon: Icon, label, value, sublabel, color = 'text-accent-cyan', index = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: index * 0.06 }}
      className="rounded-xl border border-border-primary bg-bg-card p-5 hover:bg-bg-card-hover transition-colors duration-200"
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-text-muted mb-2">{label}</p>
          <p className="text-3xl font-bold text-text-primary leading-none">{value}</p>
          {sublabel && (
            <p className="text-sm text-text-secondary mt-1.5">{sublabel}</p>
          )}
        </div>
        <div className={`p-2.5 rounded-lg bg-bg-glass ${color}`}>
          <Icon size={20} />
        </div>
      </div>
    </motion.div>
  );
}

interface KpiCardProps {
  icon: LucideIcon;
  label: string;
  value: number;
  total?: number;
  color?: string;
}

export function KpiCard({ icon: Icon, label, value, total, color = 'text-accent-cyan' }: KpiCardProps) {
  return (
    <div className="rounded-xl border border-border-primary bg-bg-card p-5 hover:border-border-secondary transition-colors duration-200">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg bg-bg-glass ${color}`}>
          <Icon size={18} />
        </div>
        <span className="text-sm font-medium text-text-secondary">{label}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-text-primary">
          {value.toLocaleString()}
        </span>
        {total !== undefined && (
          <span className="text-sm text-text-muted">/ {total.toLocaleString()}</span>
        )}
      </div>
    </div>
  );
}

interface ProgressStatProps {
  label: string;
  value: number;
  max?: number;
  color?: string;
  icon?: LucideIcon;
}

export function ProgressStat({ label, value, max = 100, color = 'bg-accent-cyan', icon: Icon }: ProgressStatProps) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-text-secondary">
          {Icon && <Icon size={14} />}
          <span>{label}</span>
        </div>
        <span className="font-medium text-text-primary">{Math.round(pct)}%</span>
      </div>
      <div className="h-2 rounded-full bg-bg-glass overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className={`h-full rounded-full ${color}`}
        />
      </div>
    </div>
  );
}
