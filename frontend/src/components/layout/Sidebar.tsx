import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  BarChart3,
  ShieldCheck,
  Compass,
  Brain,
  Rocket,
  Activity,
  Database,
  Users,
  FileText,
  FlaskConical,
} from 'lucide-react';
import { useDataset } from '../../hooks/useDataset';

const sidebarLinks = [
  { to: '/dashboard', label: 'Overview', icon: BarChart3 },
  { to: '/dashboard/quality', label: 'Data Quality', icon: ShieldCheck },
  { to: '/dashboard/exploration', label: 'Exploration', icon: Compass },
  { to: '/dashboard/insights', label: 'AI Insights', icon: Brain },
  { to: '/dashboard/ml-readiness', label: 'ML Readiness', icon: Rocket },
  { to: '/dashboard/evaluate', label: 'Evaluation', icon: FlaskConical },
];

export default function Sidebar() {
  const { profile, fileName } = useDataset();
  const info = profile?.dataset_info;

  return (
    <motion.aside
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border-primary bg-bg-secondary/50 h-[calc(100vh-4rem)] sticky top-16 overflow-y-auto"
    >
      <div className="p-4 space-y-1">
        {sidebarLinks.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/dashboard'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-glass'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </div>

      {info && (
        <div className="mt-auto p-4 border-t border-border-primary">
          <div className="rounded-xl bg-bg-glass border border-border-primary p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-text-muted">
              <Database size={14} />
              Dataset Info
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-text-secondary flex items-center gap-2">
                  <FileText size={14} />
                  Rows
                </span>
                <span className="text-text-primary font-medium">{info.rows.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary flex items-center gap-2">
                  <Activity size={14} />
                  Columns
                </span>
                <span className="text-text-primary font-medium">{info.columns}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-text-secondary flex items-center gap-2">
                  <Users size={14} />
                  Duplicates
                </span>
                <span className="text-text-primary font-medium">{info.duplicate_rows}</span>
              </div>
            </div>
            {fileName && (
              <div className="pt-2 border-t border-border-primary">
                <p className="text-xs text-text-muted truncate" title={fileName}>
                  {fileName}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </motion.aside>
  );
}
