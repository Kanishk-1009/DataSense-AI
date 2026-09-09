import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Brain,
  AlertTriangle,
  BarChart3,
  Sparkles,
  CheckCircle,
  Lightbulb,
  TrendingUp,
  GitBranch,
  Activity,
  Layers,
  Cpu,
  ChevronDown,
  Zap,
  Info,
} from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { Badge } from '../../components/common/UIComponents';
import { useDataset } from '../../hooks/useDataset';
import { useDatasetStore } from '../../store/datasetStore';
import type { AgentResponse } from '../../types/analysis';
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

const insightIcons: Record<string, typeof Brain> = {
  missing: AlertTriangle,
  outlier: AlertTriangle,
  correlation: TrendingUp,
  quality: CheckCircle,
  default: Lightbulb,
};

function getInsightIcon(text: string): typeof Brain {
  const lower = text.toLowerCase();
  if (lower.includes('missing')) return insightIcons.missing;
  if (lower.includes('outlier')) return insightIcons.outlier;
  if (lower.includes('correlat')) return insightIcons.correlation;
  if (lower.includes('quality') || lower.includes('score')) return insightIcons.quality;
  return insightIcons.default;
}

function getInsightSeverity(text: string): 'warning' | 'info' | 'success' {
  const lower = text.toLowerCase();
  if (lower.includes('missing') || lower.includes('outlier') || lower.includes('duplicate') || lower.includes('imbalanced')) return 'warning';
  if (lower.includes('no ') || lower.includes('score is') || lower.includes('contains')) return 'success';
  return 'info';
}

interface SpecialistOutput {
  findings: string | null;
  risk_level: string;
  recommendations: string[];
  error?: string;
}

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
  { key: 'preprocessing_planner_agent', label: 'Preprocessing Agent', icon: Layers, color: 'text-accent-purple' },
  { key: 'algorithm_recommendation_agent', label: 'Algorithm Agent', icon: Cpu, color: 'text-green-400' },
  { key: 'critic_synthesizer', label: 'Critic & Synthesizer', icon: Sparkles, color: 'text-accent-cyan' },
];

function riskBadge(level: string) {
  const l = level.toLowerCase();
  if (l.includes('high')) return <Badge variant="red">High</Badge>;
  if (l.includes('medium') || l.includes('moderate')) return <Badge variant="amber">Medium</Badge>;
  if (l.includes('low')) return <Badge variant="green">Low</Badge>;
  return <Badge>{level}</Badge>;
}

function AgentSuccessBlock({ agent }: { agent: AgentResponse }) {
  const [expandedNode, setExpandedNode] = useState<string | null>(null);
  const isMulti = agent.pipeline === 'multi_agent';
  const extra = agent.extra ?? {};
  const llmCallCount = (extra.llm_call_count as number | undefined) ?? 0;
  const perNodeTime = (extra.per_node_time as Record<string, number> | undefined) ?? {};
  const specialistOutputs = (extra.specialist_outputs as Record<string, SpecialistOutput> | undefined) ?? {};

  const confidencePct = agent.confidence != null ? Math.round(agent.confidence * 100) : null;
  const confidenceColor =
    confidencePct === null ? 'bg-text-muted' : confidencePct > 70 ? 'bg-green-400' : confidencePct > 40 ? 'bg-amber-400' : 'bg-red-400';

  const timingData = Object.entries(perNodeTime).map(([name, t]) => ({
    name: name.replace('_agent', '').replace('_', ' '),
    time: t,
  }));

  return (
    <>
      {/* Pipeline Info Banner */}
      <Card className="mb-6">
        <CardContent className="py-5">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
            <Badge variant={isMulti ? 'purple' : 'cyan'} size="md">
              {isMulti ? 'Multi Agent' : 'Single Agent'}
            </Badge>
            <span className="font-mono text-sm text-text-primary">{agent.model}</span>
            <span className="text-sm text-text-secondary">{agent.execution_time_seconds.toFixed(1)}s execution</span>
            {isMulti && (
              <span className="flex items-center gap-1.5 text-sm text-text-secondary">
                <Zap size={14} className="text-amber-400" />
                {llmCallCount} LLM calls
              </span>
            )}
            <div className="flex items-center gap-3 flex-1 min-w-[220px]">
              <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Confidence</span>
              <div className="h-2 flex-1 rounded-full bg-bg-glass overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${confidenceColor}`}
                  style={{ width: `${confidencePct ?? 0}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-text-primary">
                {confidencePct === null ? 'N/A' : `${confidencePct}%`}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Narrative */}
      {agent.narrative && (
        <Card className="mb-6">
          <CardHeader>
            <h3 className="font-semibold text-text-primary flex items-center gap-2">
              <Brain size={16} className="text-accent-cyan" />
              AI Narrative Analysis
            </h3>
          </CardHeader>
          <CardContent>
            {agent.narrative
              .split(/\n\n+/)
              .filter((p) => p.trim())
              .map((p, i) => (
                <p key={i} className="leading-relaxed text-text-secondary mb-3 last:mb-0">
                  {p}
                </p>
              ))}
          </CardContent>
        </Card>
      )}

      {/* Key Risks + Recommendations */}
      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {agent.key_risks.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-400" />
                Key Risks
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-2.5">
                {agent.key_risks.map((risk, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2.5"
                  >
                    <AlertTriangle size={15} className="text-amber-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-text-secondary">{risk}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        {agent.recommendations.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <CheckCircle size={16} className="text-green-400" />
                Recommendations
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-2.5">
                {agent.recommendations.map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2.5 rounded-lg border border-green-500/20 bg-green-500/5 px-3 py-2.5"
                  >
                    <CheckCircle size={15} className="text-green-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-text-secondary">{rec}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Multi-Agent Specialist Breakdown */}
      {isMulti && (
        <>
          <SectionHeader title="Specialist Agent Outputs" subtitle="Each agent analyzed a specific EDA slice" />
          <div className="mb-6 rounded-xl border border-border-primary bg-bg-card overflow-hidden">
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

          {/* Per-Node Timing */}
          {timingData.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <Zap size={16} className="text-amber-400" />
                  Per-Node Execution Time
                </h3>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={timingData} layout="vertical" margin={{ left: 24, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis type="number" unit="s" tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <YAxis dataKey="name" type="category" width={130} tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                      formatter={(value) => [`${Number(value ?? 0).toFixed(2)}s`, 'Time']}
                    />
                    <Bar dataKey="time" fill="#38bdf8" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </>
  );
}

export default function AIInsightsPage() {
  const { edaResult } = useDataset();
  const agentResult = useDatasetStore((s) => s.agentResult);
  const insights = edaResult?.insights?.insights || [];
  const quality = edaResult?.quality_score;
  const featureImportance = edaResult?.feature_importance;
  const mlRecommendation = edaResult?.ml_recommendation;

  const importanceData = (featureImportance?.random_forest || []).slice(0, 10);

  return (
    <div className="page-container">
      {agentResult?.status === 'success' && <AgentSuccessBlock agent={agentResult} />}
      {agentResult?.status === 'error' && (
        <div className="mb-8 rounded-xl border border-red-500/20 bg-red-500/5 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-red-400 mt-0.5 shrink-0" />
            <div>
              <h3 className="font-semibold text-text-primary mb-1">AI Analysis Failed</h3>
              <p className="text-sm text-text-secondary">{agentResult.error || 'An unknown error occurred.'}</p>
              <p className="text-xs text-text-muted mt-2">EDA results below are still available.</p>
            </div>
          </div>
        </div>
      )}
      {!agentResult && (
        <div className="mb-8 rounded-xl border border-blue-500/20 bg-blue-500/5 p-6">
          <div className="flex items-start gap-3">
            <Info size={20} className="text-blue-400 mt-0.5 shrink-0" />
            <p className="text-sm text-text-secondary">
              No AI analysis available. To get AI insights, go back to the Home page and select Single Agent or Multi Agent pipeline mode.
            </p>
          </div>
        </div>
      )}

      <PageHeader
        title="AI Dataset Intelligence"
        subtitle="Let AI explain what your dataset is telling you"
      />

      {/* Summary */}
      <Card className="mb-8">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-gradient-to-br from-accent-cyan/20 to-accent-purple/20 border border-accent-cyan/20">
              <Brain size={24} className="text-accent-cyan" />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary mb-2">Dataset Summary</h3>
              <p className="text-text-secondary leading-relaxed">
                This dataset contains {edaResult?.report?.dataset?.rows?.toLocaleString() || 'N/A'} records
                across {edaResult?.report?.dataset?.columns || 'N/A'} features.
                {edaResult?.report?.ml_task?.task && (
                  <> The detected ML task is <strong className="text-accent-cyan">{edaResult.report.ml_task.task}</strong>.</>
                )}
                {' '}
                Quality score: <strong className={quality && quality.score >= 75 ? 'text-green-400' : 'text-amber-400'}>
                  {quality?.score}/100 ({quality?.grade})
                </strong>.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Findings */}
      <SectionHeader title="Key Findings" subtitle="AI-generated insights from your dataset" />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {insights.map((insight: string, i: number) => {
          const Icon = getInsightIcon(insight);
          const severity = getInsightSeverity(insight);
          const colors = {
            warning: { bg: 'bg-amber-500/5', border: 'border-amber-500/20', icon: 'text-amber-400' },
            info: { bg: 'bg-blue-500/5', border: 'border-blue-500/20', icon: 'text-blue-400' },
            success: { bg: 'bg-green-500/5', border: 'border-green-500/20', icon: 'text-green-400' },
          };
          const c = colors[severity];

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className={`rounded-xl border ${c.border} ${c.bg} p-4`}
            >
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 ${c.icon}`}>
                  <Icon size={18} />
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">{insight}</p>
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Feature Importance */}
        {featureImportance?.status === 'available' && importanceData.length > 0 && (
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <TrendingUp size={16} className="text-accent-cyan" />
                Feature Importance (Random Forest)
              </h3>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={importanceData} layout="vertical" margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <YAxis dataKey="feature" type="category" width={90} tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                      formatter={(value) => [typeof value === 'number' ? value.toFixed(4) : String(value ?? ''), 'Importance']}
                    />
                    <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                      {importanceData.map((_item: {feature: string; importance: number}, i: number) => (
                        <Cell key={i} fill="#38bdf8" fillOpacity={0.8 - i * 0.06} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quality Breakdown */}
        {quality && (
          <Card>
            <CardHeader>
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <Sparkles size={16} className="text-accent-purple" />
                Quality Breakdown
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {quality.strengths.map((s: string, i: number) => (
                  <div key={`s-${i}`} className="flex items-start gap-3">
                    <CheckCircle size={16} className="text-green-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-text-secondary">{s}</p>
                  </div>
                ))}
                {quality.issues.map((s: string, i: number) => (
                  <div key={`i-${i}`} className="flex items-start gap-3">
                    <AlertTriangle size={16} className="text-amber-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-text-secondary">{s}</p>
                  </div>
                ))}
                <div className="pt-2 border-t border-border-primary">
                  <h4 className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Recommendations</h4>
                  {quality.recommendations.map((r: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-text-secondary mb-1.5">
                      <span className="text-accent-cyan mt-0.5">→</span>
                      {r}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* ML Recommendation */}
      {mlRecommendation?.status === 'available' && (
        <>
          <SectionHeader title="ML Recommendations" subtitle="Suggested models and preprocessing" />
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {mlRecommendation.recommended_models.map((m: {model: string; reason: string}, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="rounded-xl border border-border-primary bg-bg-card p-5"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-accent-cyan/10">
                    <BarChart3 size={16} className="text-accent-cyan" />
                  </div>
                  <Badge variant="cyan">{mlRecommendation.task}</Badge>
                </div>
                <h4 className="font-semibold text-text-primary mb-1">{m.model}</h4>
                <p className="text-sm text-text-secondary">{m.reason}</p>
              </motion.div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}