import { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle,
  ChevronDown,
  Info,
  Loader2,
  Trophy,
  Upload,
  XCircle,
} from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { Badge } from '../../components/common/UIComponents';
import { RadialScore } from '../../components/common/RadialScore';
import { runEvaluation } from '../../services/datasetApi';
import { useDatasetStore } from '../../store/datasetStore';
import type {
  MetricComparison,
  PipelineMetrics,
  RubricCheckResult,
} from '../../types/evaluation';

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

function formatSize(bytes: number) {
  return bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(2)} MB`;
}

const inputClass =
  'bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50 transition-colors w-full';
const labelClass = 'text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block';

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border-primary last:border-0">
      <span className="text-sm text-text-secondary">{label}</span>
      <span className="text-sm font-medium text-text-primary">{value}</span>
    </div>
  );
}

function PipelineCard({
  title,
  metrics,
  accent,
}: {
  title: string;
  metrics: PipelineMetrics;
  accent: 'cyan' | 'purple';
}) {
  const accentText = accent === 'cyan' ? 'text-accent-cyan' : 'text-accent-purple';
  const badgeVariant = metrics.status === 'success' ? 'green' : 'red';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="h-full"
    >
      <Card className={accent === 'purple' ? 'border-accent-purple/20 h-full' : 'border-accent-cyan/20 h-full'}>
        <CardContent className="flex flex-col items-center gap-4">
          <div className="flex items-center justify-between w-full">
            <h3 className={`font-semibold ${accentText}`}>{title}</h3>
            <Badge variant={badgeVariant as 'green' | 'red'}>{metrics.status}</Badge>
          </div>
          <RadialScore
            score={metrics.output_completeness * 100}
            size={120}
            label="Output Completeness"
            sublabel={`${(metrics.output_completeness * 100).toFixed(1)}%`}
          />
          <div className="w-full">
            <MetricRow label="Execution time" value={`${metrics.execution_time_seconds.toFixed(1)}s`} />
            <MetricRow label="LLM calls" value={`${metrics.llm_call_count}`} />
            <MetricRow label="Narrative length" value={`${metrics.narrative_length_chars} chars`} />
            <MetricRow label="Key risks" value={`${metrics.key_risk_count}`} />
            <MetricRow label="Recommendations" value={`${metrics.recommendation_count}`} />
            <MetricRow
              label="Confidence"
              value={metrics.confidence_score !== null ? `${(metrics.confidence_score * 100).toFixed(0)}%` : 'N/A'}
            />
            <MetricRow
              label="Recommendation accuracy"
              value={metrics.recommendation_accuracy !== null ? `${(metrics.recommendation_accuracy * 100).toFixed(0)}%` : 'N/A'}
            />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function ComparisonTable({ comparison }: { comparison: MetricComparison[] }) {
  const sorted = [...comparison].sort(
    (a, b) => categoryOrder.indexOf(a.category) - categoryOrder.indexOf(b.category),
  );

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
              {sorted.map((row, i) => {
                const label = betterLabel(row.better_pipeline);
                return (
                  <tr key={i} className="border-b border-border-primary last:border-0 hover:bg-bg-glass transition-colors">
                    <td className="px-4 py-3 font-medium text-text-primary">{row.metric}</td>
                    <td className="px-4 py-3">
                      <Badge variant={categoryVariant[row.category] ?? 'default'}>{row.category}</Badge>
                    </td>
                    <td className="px-4 py-3 text-text-secondary">{formatValue(row.m4_value)}</td>
                    <td className="px-4 py-3 text-text-secondary">{formatValue(row.m5_value)}</td>
                    <td className="px-4 py-3">
                      {label ? (
                        <span
                          className={`flex items-center gap-1.5 font-medium ${
                            label === 'M4' ? 'text-accent-cyan' : 'text-accent-purple'
                          }`}
                        >
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
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function RubricAccordion({
  title,
  checks,
  accent,
}: {
  title: string;
  checks: RubricCheckResult[];
  accent: 'cyan' | 'purple';
}) {
  const [open, setOpen] = useState(false);
  const triggered = checks.filter((c) => c.condition_triggered);

  return (
    <Card className={accent === 'purple' ? 'border-accent-purple/20' : 'border-accent-cyan/20'}>
      <button
        onClick={() => setOpen(!open)}
        className="px-5 py-4 w-full flex items-center justify-between gap-3 text-left hover:bg-bg-glass transition-colors"
      >
        <span className="font-semibold text-text-primary">{title}</span>
        <span className="flex items-center gap-3 shrink-0">
          <Badge variant={accent === 'purple' ? 'purple' : 'cyan'}>{triggered.length} checks</Badge>
          <ChevronDown
            size={16}
            className={`text-text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          />
        </span>
      </button>
      {open && (
        <div className="border-t border-border-primary px-5 py-4 space-y-3">
          {triggered.length === 0 && <p className="text-sm text-text-muted">No triggered rubric checks.</p>}
          {triggered.map((check, i) => (
            <div key={i} className="rounded-lg border border-border-primary bg-bg-glass/50 p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  {check.recommendation_matched ? (
                    <CheckCircle size={16} className="text-green-400 shrink-0" />
                  ) : (
                    <XCircle size={16} className="text-red-400 shrink-0" />
                  )}
                  <span className="text-sm font-medium text-text-primary font-mono">{check.condition_id}</span>
                </div>
                <Badge variant={check.recommendation_matched ? 'green' : 'red'}>
                  {check.recommendation_matched ? 'Matched' : 'Missed'}
                </Badge>
              </div>
              <p className="text-sm text-text-secondary mt-1.5">{check.condition_description}</p>
              {check.expected_keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {check.expected_keywords.map((kw, j) => (
                    <span
                      key={j}
                      className="px-2 py-0.5 rounded-md bg-bg-glass border border-border-primary text-[11px] text-text-muted"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function EvaluationPage() {
  const { evaluationResult, setEvaluationResult } = useDatasetStore();
  const [file, setFile] = useState<File | null>(null);
  const [target, setTarget] = useState('');
  const [model, setModel] = useState('llama3.1:8b');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await runEvaluation(file, target || undefined, model, ollamaUrl);
      setEvaluationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  }, [file, target, model, ollamaUrl, setEvaluationResult]);

  return (
    <div className="page-container">
      <PageHeader
        title="Pipeline Evaluation"
        subtitle="Compare Single Agent (M4) vs Multi Agent (M5) on identical EDA input"
      />

      {/* Upload & Config Panel */}
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Dataset CSV</label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) {
                    setFile(f);
                    setError(null);
                  }
                }}
                className="w-full text-sm text-text-secondary file:mr-4 file:px-4 file:py-2 file:rounded-lg file:border-0 file:bg-accent-cyan/10 file:text-accent-cyan file:text-sm file:font-medium hover:file:bg-accent-cyan/20 file:cursor-pointer cursor-pointer transition-colors"
              />
              {file && (
                <p className="text-xs text-text-muted mt-1 flex items-center gap-1.5">
                  <Upload size={12} />
                  {file.name} ({formatSize(file.size)})
                </p>
              )}
            </div>
            <div>
              <label className={labelClass}>Target Column (optional)</label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="e.g. Survived, price"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Ollama Model</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="llama3.1:8b"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Ollama Server URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                placeholder="http://localhost:11434"
                className={inputClass}
              />
            </div>
          </div>

          <button
            onClick={handleRun}
            disabled={!file || loading}
            className="mt-5 w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-blue text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Running both pipelines... This takes 2–5 minutes.
              </>
            ) : (
              <>
                Run Evaluation
                <Trophy size={18} />
              </>
            )}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {evaluationResult && (
        <>
          <SectionHeader title="Results" subtitle={evaluationResult.dataset_name} />

          {/* Side-by-Side Pipelines */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            <PipelineCard title="Single Agent (M4)" metrics={evaluationResult.m4} accent="cyan" />
            <PipelineCard title="Multi Agent (M5)" metrics={evaluationResult.m5} accent="purple" />
          </div>

          {/* Metric Comparison */}
          <div className="mb-6">
            <ComparisonTable comparison={evaluationResult.comparison} />
          </div>

          {/* Rubric Checks */}
          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            <RubricAccordion
              title="M4 Rubric Checks"
              checks={evaluationResult.m4.rubric_checks}
              accent="cyan"
            />
            <RubricAccordion
              title="M5 Rubric Checks"
              checks={evaluationResult.m5.rubric_checks}
              accent="purple"
            />
          </div>

          {/* Research Note */}
          {evaluationResult.research_note && (
            <div className="mb-6 rounded-xl border border-blue-500/20 bg-blue-500/5 p-6">
              <div className="flex items-start gap-3">
                <Info size={18} className="text-blue-400 mt-0.5 shrink-0" />
                <p className="text-sm text-text-secondary leading-relaxed">{evaluationResult.research_note}</p>
              </div>
            </div>
          )}

          {/* Run Details */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-text-muted">
            <span>
              run_id: <span className="font-mono text-text-secondary">{evaluationResult.run_id}</span>
            </span>
            <span>{evaluationResult.timestamp}</span>
            <span>{evaluationResult.dataset_name}</span>
            <span>
              model: <span className="font-mono text-text-secondary">{evaluationResult.model}</span>
            </span>
            <span>
              hash: <span className="font-mono text-text-secondary">{evaluationResult.dataset_hash}</span>
            </span>
          </div>
        </>
      )}
    </div>
  );
}