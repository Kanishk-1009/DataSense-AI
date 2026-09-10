import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Rocket,
  ShieldCheck,
  Layers,
  Scale,
  AlertTriangle,
  Target,
  CheckCircle,
  TrendingUp,
  Crosshair,
  Hash,
} from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { GaugeScore } from '../../components/common/RadialScore';
import { ProgressStat } from '../../components/common/StatCard';
import { Badge, Tabs } from '../../components/common/UIComponents';
import { FeatureImportanceChart } from '../../components/charts/FeatureImportanceChart';
import { useDataset } from '../../hooks/useDataset';
import type { MLTask, PreprocessingRecommendation } from '../../types/analysis';

function computeMLReadinessScore(eda: ReturnType<typeof useDataset>['edaResult']): {
  overall: number;
  categories: Array<{
    label: string;
    score: number;
    icon: typeof ShieldCheck;
    color: string;
    description: string;
  }>;
  recommendations: string[];
} {
  if (!eda) return { overall: 0, categories: [], recommendations: [] };

  const quality = eda.quality_score?.score || 0;
  const missingPct = eda.missingness?.summary?.overall_missing_percentage || 0;
  const outlierCount = Object.values(eda.outliers || {}).filter((o) => (o as {count: number}).count > 0).length;
  const totalNumeric = Object.keys(eda.numeric_statistics || {}).length;
  const highCorr = eda.correlation_analysis?.highly_correlated_pairs?.length || 0;
  const totalFeatures = eda.feature_summary?.count || 1;

  const dataQuality = Math.max(0, Math.min(100, quality));
  const featureCompleteness = Math.max(0, Math.min(100, 100 - missingPct * 2));

  // Class balance approximation
  const targetAnalysis = eda.target_analysis;
  const classBalance = targetAnalysis ? 75 : 60;

  const featureDiversity = Math.max(0, Math.min(100,
    (totalFeatures > 5 ? 80 : totalFeatures * 16) + (highCorr === 0 ? 20 : 0)
  ));

  const outlierRisk = Math.max(0, Math.min(100,
    100 - (outlierCount / Math.max(totalNumeric, 1)) * 100
  ));

  const categories = [
    { label: 'Data Quality', score: dataQuality, icon: ShieldCheck, color: 'text-green-400', description: 'Based on missing values, duplicates, and overall integrity' },
    { label: 'Feature Completeness', score: featureCompleteness, icon: Layers, color: 'text-accent-cyan', description: 'Percentage of complete feature values across the dataset' },
    { label: 'Class Balance', score: classBalance, icon: Scale, color: 'text-accent-purple', description: 'Distribution balance of target variable classes' },
    { label: 'Feature Diversity', score: featureDiversity, icon: Target, color: 'text-accent-blue', description: 'Variety and independence of features' },
    { label: 'Outlier Risk', score: outlierRisk, icon: AlertTriangle, color: outlierRisk > 70 ? 'text-green-400' : 'text-amber-400', description: 'Risk posed by statistical outliers to model training' },
  ];

  const overall = Math.round(
    categories.reduce((sum, c) => sum + c.score, 0) / categories.length
  );

  const recommendations: string[] = [];
  if (missingPct > 0) recommendations.push(`Handle missing values (${missingPct.toFixed(1)}% overall missing).`);
  if (outlierCount > 0) recommendations.push(`Review outliers in ${outlierCount} numeric feature(s).`);
  if (highCorr > 0) recommendations.push(`Address ${highCorr} highly correlated feature pair(s).`);
  recommendations.push('Standardize numerical features before training.');
  if (eda.feature_summary) {
    const catCount = Object.values(eda.feature_summary.features || {}).filter(
      (f) => (f as {column_type: string}).column_type === 'categorical' || (f as {column_type: string}).column_type === 'binary'
    ).length;
    if (catCount > 0) recommendations.push(`Encode ${catCount} categorical variable(s).`);
  }

  return { overall, categories, recommendations };
}

export default function MLReadinessPage() {
  const { edaResult } = useDataset();
  const { overall, categories, recommendations } = computeMLReadinessScore(edaResult);
  const mlRec = edaResult?.ml_recommendation;
  const mlTask = edaResult?.ml_task;
  const featureImportance = edaResult?.feature_importance;
  const [fiTab, setFiTab] = useState('random_forest');

  const ftabs = [
    { id: 'random_forest', label: 'Random Forest' },
    { id: 'mutual_information', label: 'Mutual Information' },
  ];

  const preprocessing = edaResult?.preprocessing?.recommendations || [];
  const priorityGroups: Record<string, PreprocessingRecommendation[]> = { high: [], medium: [], low: [] };
  preprocessing.forEach((rec: PreprocessingRecommendation) => {
    const key = rec.priority in priorityGroups ? rec.priority : 'medium';
    priorityGroups[key].push(rec);
  });

  const taskStatusMeta = (task: MLTask | undefined) => {
    if (!task) return { variant: 'default' as const, label: 'Unknown', desc: 'No ML task analysis available.' };
    switch (task.status) {
      case 'detected':
        return { variant: 'cyan' as const, label: 'Detected', desc: task.reason };
      case 'target_required':
        return { variant: 'amber' as const, label: 'Target Required', desc: 'Select a target column to detect the ML task.' };
      case 'invalid_target':
        return { variant: 'red' as const, label: 'Invalid Target', desc: task.reason };
      case 'unsupported':
        return { variant: 'purple' as const, label: 'Unsupported', desc: task.reason };
      default:
        return { variant: 'default' as const, label: 'Unknown', desc: 'No ML task analysis available.' };
    }
  };

  const taskMeta = taskStatusMeta(mlTask);
  const taskConfidencePct = mlTask?.confidence != null ? Math.round(mlTask.confidence * 100) : null;

  return (
    <div className="page-container">
      <PageHeader
        title="ML Readiness"
        subtitle="Assess your dataset's readiness for machine learning"
      />

      {/* Readiness Score */}
      <Card className="mb-8">
        <CardContent className="py-8 flex flex-col items-center">
          <GaugeScore score={overall} size={240} label="ML Readiness Score" />
          <p className="text-text-secondary mt-4 text-center max-w-md">
            {overall >= 80
              ? 'Your dataset is well-prepared for machine learning. Minor preprocessing may still be needed.'
              : overall >= 60
              ? 'Your dataset needs some preparation before training models. Review the categories below.'
              : 'Significant preprocessing is required before your dataset is ready for machine learning.'}
          </p>
        </CardContent>
      </Card>

      {/* Category Scores */}
      <SectionHeader title="Readiness Categories" subtitle="Detailed breakdown of ML readiness factors" />
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {categories.map((cat, i) => (
          <motion.div
            key={cat.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="rounded-xl border border-border-primary bg-bg-card p-5"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-bg-glass">
                <cat.icon size={18} className={cat.color} />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-text-primary text-sm">{cat.label}</h4>
              </div>
              <span className="text-lg font-bold text-text-primary">{Math.round(cat.score)}</span>
            </div>
            <ProgressStat
              label=""
              value={cat.score}
              color={
                cat.score >= 80 ? 'bg-green-400' :
                cat.score >= 60 ? 'bg-accent-cyan' :
                cat.score >= 40 ? 'bg-amber-400' : 'bg-red-400'
              }
            />
            <p className="text-xs text-text-muted mt-3">{cat.description}</p>
          </motion.div>
        ))}
      </div>

      {/* Feature Importance */}
      {featureImportance && (featureImportance.status === 'available') && (
        <>
          <SectionHeader
            title="Feature Importance"
            subtitle="Top predictors identified by model-agnostic analysis"
            action={
              <Tabs
                tabs={ftabs}
                activeTab={fiTab}
                onChange={setFiTab}
              />
            }
          />
          <Card className="mb-8">
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <TrendingUp size={16} className={fiTab === 'random_forest' ? 'text-accent-cyan' : 'text-accent-purple'} />
                  {fiTab === 'random_forest' ? 'Random Forest Importance' : 'Mutual Information Scores'}
                </h3>
                <Badge variant={fiTab === 'random_forest' ? 'cyan' : 'purple'}>
                  {featureImportance.target ? `target: ${featureImportance.target}` : featureImportance.task_type || 'all features'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <FeatureImportanceChart
                data={
                  fiTab === 'random_forest'
                    ? featureImportance.random_forest.map((f) => ({ feature: f.feature, importance: f.importance, rank: f.rank }))
                    : featureImportance.mutual_information.map((f) => ({ feature: f.feature, importance: f.normalized_score, rank: f.rank }))
                }
                method={fiTab === 'random_forest' ? 'random_forest' : 'mutual_information'}
                maxItems={10}
                height={280}
              />
            </CardContent>
          </Card>
        </>
      )}

      {/* Recommendations */}
      <SectionHeader title="Recommendations" subtitle="Steps to improve ML readiness" />
      <Card className="mb-8">
        <CardContent>
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
                className="flex items-start gap-3 p-3 rounded-lg bg-bg-glass border border-border-primary"
              >
                <div className="p-1 rounded bg-accent-cyan/10 text-accent-cyan mt-0.5">
                  <TrendingUp size={14} />
                </div>
                <p className="text-sm text-text-secondary">{rec}</p>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ML Task Detection */}
      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        <Card className="lg:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <Crosshair size={16} className="text-accent-cyan" />
                Detected ML Task
              </h3>
              <Badge variant={taskMeta.variant}>{taskMeta.label}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {mlTask ? (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-bg-glass border border-border-primary">
                  <p className="text-xs text-text-muted mb-1">Task Type</p>
                  <p className="text-2xl font-bold text-text-primary capitalize">
                    {mlTask.task_type ? mlTask.task_type.replace('_', ' ') : mlTask.task || 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1.5 uppercase tracking-wider">Confidence</p>
                  <div className="flex items-center gap-3">
                    <div className="h-2 flex-1 rounded-full bg-bg-glass overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${taskConfidencePct === null ? 'bg-text-muted' : taskConfidencePct > 70 ? 'bg-green-400' : taskConfidencePct > 40 ? 'bg-amber-400' : 'bg-red-400'}`}
                        style={{ width: `${taskConfidencePct ?? 0}%` }}
                      />
                    </div>
                    <span className="text-sm font-semibold text-text-primary">
                      {taskConfidencePct === null ? 'N/A' : `${taskConfidencePct}%`}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">{taskMeta.desc}</p>
              </div>
            ) : (
              <p className="text-sm text-text-muted">No ML task analysis available.</p>
            )}
          </CardContent>
        </Card>

        {mlTask && (
          <div className="lg:col-span-2 grid sm:grid-cols-2 gap-4">
            {[
              { label: 'Target Column', value: mlTask.target || '—', icon: Target },
              { label: 'Target Type', value: mlTask.target_type || '—', icon: Hash },
              { label: 'Unique Classes', value: mlTask.unique_classes?.toLocaleString() ?? '—', icon: Layers },
              { label: 'Missing in Target', value: mlTask.missing_count != null ? `${mlTask.missing_count} (${mlTask.missing_percentage ?? 0}%)` : '—', icon: AlertTriangle },
            ].map((info) => (
              <motion.div
                key={info.label}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-border-primary bg-bg-card p-4"
              >
                <div className="flex items-center gap-2 mb-2">
                  <info.icon size={14} className="text-accent-cyan" />
                  <p className="text-xs text-text-muted uppercase tracking-wider">{info.label}</p>
                </div>
                <p className="text-text-primary font-medium truncate" title={String(info.value)}>{info.value}</p>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Recommended Models */}
      {mlRec?.status === 'available' && mlRec.recommended_models.length > 0 && (
        <>
          <SectionHeader title="Recommended Models" subtitle="Models suggested for this dataset and task" />
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {mlRec.recommended_models.map((m: {model: string; reason: string}, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="rounded-xl border border-border-primary bg-bg-card p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Rocket size={16} className="text-accent-cyan" />
                  <Badge variant="cyan">{mlRec.task}</Badge>
                </div>
                <h4 className="font-semibold text-text-primary mb-1">{m.model}</h4>
                <p className="text-sm text-text-secondary">{m.reason}</p>
              </motion.div>
            ))}
          </div>
        </>
      )}

      {/* ML Reasoning */}
      {mlRec?.reasoning && mlRec.reasoning.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="font-semibold text-text-primary">Analysis Reasoning</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {mlRec.reasoning.map((r: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                  <CheckCircle size={14} className="text-accent-cyan mt-0.5 shrink-0" />
                  {r}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Preprocessing Plan */}
      {preprocessing.length > 0 && (
        <>
          <SectionHeader title="Preprocessing Plan" subtitle="Recommended steps to prepare the dataset for modeling" />
          <div className="grid md:grid-cols-3 gap-4 mb-8">
            {(['high', 'medium', 'low'] as const).map((priority) => {
              const group = priorityGroups[priority];
              if (!group || group.length === 0) return null;
              const meta = {
                high: { label: 'High', variant: 'red' as const, color: 'border-red-500/20 bg-red-500/5', text: 'text-red-400', badge: 'bg-red-500/10' },
                medium: { label: 'Medium', variant: 'amber' as const, color: 'border-amber-500/20 bg-amber-500/5', text: 'text-amber-400', badge: 'bg-amber-500/10' },
                low: { label: 'Low', variant: 'cyan' as const, color: 'border-accent-cyan/20 bg-accent-cyan/5', text: 'text-accent-cyan', badge: 'bg-accent-cyan/10' },
              }[priority];
              return (
                <motion.div
                  key={priority}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`rounded-xl border ${meta.color} p-4`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className={`text-sm font-semibold ${meta.text}`}>{meta.label} Priority</span>
                    <span className={`px-2 py-0.5 rounded-md text-xs text-text-secondary ${meta.badge}`}>{group.length} steps</span>
                  </div>
                  <div className="space-y-2">
                    {group.map((rec: PreprocessingRecommendation, i: number) => (
                      <div key={i} className="flex items-start gap-2 text-xs text-text-secondary leading-relaxed">
                        <span className={`mt-1 w-1.5 h-1.5 rounded-full shrink-0 ${meta.text}`} />
                        <span>
                          {rec.column && <span className="text-text-primary font-medium">{rec.column}: </span>}
                          {rec.action}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
