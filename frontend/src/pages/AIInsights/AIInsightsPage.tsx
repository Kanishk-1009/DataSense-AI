import { motion } from 'framer-motion';
import {
  Brain,
  AlertTriangle,
  BarChart3,
  Sparkles,
  CheckCircle,
  Lightbulb,
  TrendingUp,
} from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { Badge } from '../../components/common/UIComponents';
import { AgentRunPanel } from '../../components/analysis/AgentRunPanel';
import { useDataset } from '../../hooks/useDataset';
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

export default function AIInsightsPage() {
  const { edaResult } = useDataset();
  const insights = edaResult?.insights?.insights || [];
  const quality = edaResult?.quality_score;
  const featureImportance = edaResult?.feature_importance;
  const mlRecommendation = edaResult?.ml_recommendation;

  const importanceData = (featureImportance?.random_forest || []).slice(0, 10);

  return (
    <div className="page-container">
      <PageHeader
        title="AI Dataset Intelligence"
        subtitle="Let AI explain what your dataset is telling you"
      />

      {/* AI Agent Panel: results or run prompt */}
      <AgentRunPanel />

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