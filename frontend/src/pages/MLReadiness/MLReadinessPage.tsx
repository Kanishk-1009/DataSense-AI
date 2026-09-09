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
} from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { GaugeScore } from '../../components/common/RadialScore';
import { ProgressStat } from '../../components/common/StatCard';
import { Badge } from '../../components/common/UIComponents';
import { useDataset } from '../../hooks/useDataset';

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
    </div>
  );
}
