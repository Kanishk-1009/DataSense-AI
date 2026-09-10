import { motion } from 'framer-motion';
import {
  AlertTriangle,
  Activity,
  ChevronDown,
  Cpu,
  GitBranch,
  Layers,
  Sparkles,
  TrendingUp,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import { Badge } from '../common/UIComponents';
import type { AgentResponse } from '../../types/analysis';

const specialistMeta: Array<{
  key: string;
  label: string;
  icon: typeof AlertTriangle;
  color: string;
}> = [
  { key: 'missing_value_agent', label: 'Missing Value Agent', icon: AlertTriangle, color: 'text-amber-400' },
  { key: 'correlation_agent', label: 'Correlation Agent', icon: GitBranch, color: 'text-blue-400' },
  { key: 'outlier_agent', label: 'Outlier Agent', icon: Activity, color: 'text-red-400' },
  { key: 'feature_importance_agent', label: 'Feature Importance Agent', icon: TrendingUp, color: 'text-accent-cyan' },
  { key: 'preprocessing_planner_agent', label: 'Preprocessing Planner', icon: Layers, color: 'text-accent-purple' },
  { key: 'algorithm_recommendation_agent', label: 'Algorithm Recommender', icon: Cpu, color: 'text-green-400' },
  { key: 'critic_synthesizer', label: 'Critic & Synthesizer', icon: Sparkles, color: 'text-accent-cyan' },
];

function riskBadge(level: string) {
  const l = level.toLowerCase();
  if (l.includes('high')) return <Badge variant="red">High</Badge>;
  if (l.includes('medium') || l.includes('moderate')) return <Badge variant="amber">Medium</Badge>;
  if (l.includes('low')) return <Badge variant="green">Low</Badge>;
  return <Badge>{level}</Badge>;
}

function PipelineTopology() {
  return (
    <div className="mb-6 rounded-xl border border-border-primary bg-bg-card p-5">
      <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-3">Pipeline Topology</h4>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {specialistMeta.map((n) => (
          <span key={n.key} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-bg-glass border border-border-primary">
            <n.icon size={12} className={n.color} />
            {n.label}
          </span>
        ))}
      </div>
      <p className="text-xs text-text-muted mt-3">
        Parallel fan-in from the first 3 specialist nodes, sequential through feature importance → preprocessing → algorithm → critic.
      </p>
    </div>
  );
}

export function SpecialistGrid({ agent }: { agent: AgentResponse }) {
  const [expandedNode, setExpandedNode] = useState<string | null>(null);
  const extra = agent.extra ?? {};
  const perNodeTime = (extra.per_node_time as Record<string, number> | undefined) ?? {};
  const specialistOutputs = (extra.specialist_outputs as Record<string, {
    findings: string | null;
    risk_level: string;
    recommendations: string[];
    error?: string;
  }> | undefined) ?? {};

  return (
    <>
      <PipelineTopology />
      <div className="rounded-xl border border-border-primary bg-bg-card overflow-hidden">
        {specialistMeta.map((meta, i) => {
          const output = specialistOutputs[meta.key];
          const nodeTime = perNodeTime[meta.key];
          if (!output) return null;
          const isOpen = expandedNode === meta.key;
          return (
            <div key={meta.key} className={i > 0 ? 'border-t border-border-primary' : ''}>
              <button
                onClick={() => setExpandedNode(isOpen ? null : meta.key)}
                className="w-full flex items-center justify-between gap-3 px-5 py-3.5 text-left hover:bg-bg-glass transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <meta.icon size={16} className={`${meta.color} shrink-0`} />
                  <span className="text-sm font-medium text-text-primary">{meta.label}</span>
                  {riskBadge(output.risk_level)}
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  {nodeTime !== undefined && (
                    <span className="text-xs text-text-muted font-mono">{nodeTime.toFixed(2)}s</span>
                  )}
                  <ChevronDown
                    size={16}
                    className={`text-text-muted transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                  />
                </div>
              </button>
              {isOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="px-5 pb-5 pt-3 border-t border-border-primary overflow-hidden"
                >
                  {output.findings && (
                    <p className="text-sm text-text-secondary leading-relaxed mb-3">{output.findings}</p>
                  )}
                  {output.recommendations.length > 0 && (
                    <div className="space-y-1.5">
                      {output.recommendations.map((rec, j) => (
                        <div key={j} className="flex items-start gap-2 text-sm text-text-secondary">
                          <span className="text-accent-cyan mt-0.5">→</span>
                          {rec}
                        </div>
                      ))}
                    </div>
                  )}
                  {output.error && (
                    <div className="mt-3 rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-sm text-red-400">
                      {output.error}
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          );
        })}
      </div>
      {Object.keys(perNodeTime).length > 0 && (
        <div className="mt-4 flex items-center gap-2 text-xs text-text-muted">
          <Zap size={12} className="text-amber-400" />
          Per-node execution times shown on each specialist row.
        </div>
      )}
    </>
  );
}