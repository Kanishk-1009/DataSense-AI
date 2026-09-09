import { useState, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  Upload,
  Menu,
  X,
  Home,
  BarChart3,
  ShieldCheck,
  Compass,
  Brain,
  Rocket,
} from 'lucide-react';
import { useDatasetStore } from '../../store/datasetStore';

const navLinks = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { to: '/dashboard/quality', label: 'Quality', icon: ShieldCheck },
  { to: '/dashboard/exploration', label: 'Exploration', icon: Compass },
  { to: '/dashboard/insights', label: 'AI Insights', icon: Brain },
  { to: '/dashboard/ml-readiness', label: 'ML Readiness', icon: Rocket },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { isLoaded, fileName, setUploadStage } = useDatasetStore();
  const loaded = isLoaded();

  const handleUploadClick = useCallback(() => {
    setUploadStage('idle');
  }, [setUploadStage]);

  return (
    <nav className="sticky top-0 z-50 border-b border-border-primary bg-bg-primary/80 backdrop-blur-xl">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2.5 shrink-0">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-blue">
              <Database size={20} className="text-white" />
            </div>
            <span className="text-lg font-bold text-text-primary hidden sm:block">
              DataSense <span className="text-accent-cyan">AI</span>
            </span>
          </Link>

          <div className="hidden lg:flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => {
              const active = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to) && (to !== '/dashboard' || location.pathname === '/dashboard');
              return (
                <Link
                  key={to}
                  to={to}
                  className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                    ${
                      active
                        ? 'bg-bg-glass text-accent-cyan'
                        : 'text-text-secondary hover:text-text-primary hover:bg-bg-glass'
                    }
                  `}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center gap-3">
            {loaded && fileName && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-bg-glass border border-border-primary text-sm">
                <Database size={14} className="text-accent-cyan" />
                <span className="text-text-secondary truncate max-w-[120px]">{fileName}</span>
              </div>
            )}
            <Link
              to="/#upload"
              onClick={handleUploadClick}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 hover:bg-accent-cyan/20 transition-colors text-sm font-medium"
            >
              <Upload size={16} />
              <span className="hidden sm:block">Upload</span>
            </Link>

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-glass transition-colors"
              aria-label="Toggle navigation"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden border-t border-border-primary bg-bg-primary/95 backdrop-blur-xl overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              {navLinks.map(({ to, label, icon: Icon }) => {
                const active = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
                return (
                  <Link
                    key={to}
                    to={to}
                    onClick={() => setMobileOpen(false)}
                    className={`
                      flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                      ${active ? 'bg-bg-glass text-accent-cyan' : 'text-text-secondary hover:text-text-primary'}
                    `}
                  >
                    <Icon size={18} />
                    {label}
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
