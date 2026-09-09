import { type ReactNode } from 'react';
import { AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';

type Severity = 'critical' | 'warning' | 'info' | 'success';

interface IssueCardProps {
  severity: Severity;
  title: string;
  message: string;
  action?: ReactNode;
}

const severityConfig: Record<Severity, { icon: typeof AlertTriangle; color: string; bg: string; border: string }> = {
  critical: {
    icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
  },
  info: {
    icon: Info,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/20',
  },
  success: {
    icon: CheckCircle,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
  },
};

export function IssueCard({ severity, title, message, action }: IssueCardProps) {
  const config = severityConfig[severity];
  const Icon = config.icon;

  return (
    <div className={`rounded-xl border ${config.border} ${config.bg} p-4`}>
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${config.color}`}>
          <Icon size={18} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-text-primary text-sm">{title}</h4>
          <p className="text-text-secondary text-sm mt-1">{message}</p>
          {action && <div className="mt-3">{action}</div>}
        </div>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  message: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="text-text-muted mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-text-primary mb-2">{title}</h3>
      <p className="text-text-secondary max-w-md">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="p-3 rounded-full bg-red-500/10 text-red-400 mb-4">
        <XCircle size={28} />
      </div>
      <h3 className="text-lg font-medium text-text-primary mb-2">Something went wrong</h3>
      <p className="text-text-secondary max-w-md mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 rounded-lg bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 hover:bg-accent-cyan/20 transition-colors text-sm font-medium"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-bg-glass rounded-lg ${className}`} />
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-border-primary bg-bg-card p-5 space-y-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
