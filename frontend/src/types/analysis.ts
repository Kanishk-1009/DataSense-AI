import type { NumericStats } from './dataset';

export interface OutlierMethod {
  count: number;
  percentage: number;
  threshold?: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface OutlierInfo {
  iqr: OutlierMethod;
  zscore: OutlierMethod;
  isolation_forest: OutlierMethod;
  count: number;
  percentage: number;
  lower_bound: number;
  upper_bound: number;
  consensus_count: number;
}

export interface CorrelationPair {
  column_a: string;
  column_b: string;
  correlation: number;
  method: 'pearson' | 'cramers_v' | 'point_biserial';
}

export interface CramersVPair {
  column_a: string;
  column_b: string;
  cramers_v: number;
}

export interface PointBiserialPair {
  binary_column: string;
  numeric_column: string;
  point_biserial: number;
}

export interface CorrelationAnalysis {
  matrix: Record<string, Record<string, number | null>>;
  highly_correlated_pairs: CorrelationPair[];
  cramers_v: CramersVPair[];
  point_biserial: PointBiserialPair[];
}

export interface ColumnMissingness {
  missing_count: number;
  missing_percentage: number;
  indicator: 'complete' | 'likely_mcar' | 'likely_mar' | 'unknown';
  max_spearman_correlation: number | null;
  note: string;
  warning?: string;
}

export interface MissingnessSummary {
  total_missing_cells: number;
  total_cells: number;
  overall_missing_percentage: number;
  columns_with_missing: number;
  likely_mar_columns: string[];
  likely_mcar_columns: string[];
  complete_columns: number;
  heuristic_note: string;
}

export interface MissingnessAnalysis {
  summary: MissingnessSummary;
  columns: Record<string, ColumnMissingness>;
}

export interface FeatureSummaryItem {
  column: string;
  column_type: 'numeric' | 'categorical' | 'binary' | 'datetime' | 'unknown';
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  is_constant: boolean;
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  q1?: number;
  q3?: number;
  skewness?: number;
  kurtosis?: number;
  outlier_count: number;
  outlier_percentage: number;
  target_correlation?: number | null;
}

export interface FeatureSummary {
  count: number;
  features: Record<string, FeatureSummaryItem>;
}

export interface QualityScore {
  score: number;
  grade: 'Excellent' | 'Good' | 'Fair' | 'Poor' | 'Critical';
  status: string;
  strengths: string[];
  issues: string[];
  recommendations: string[];
}

export interface DatasetInsights {
  count: number;
  insights: string[];
}

export interface MLTask {
  target: string | null;
  target_type: string | null;
  unique_classes?: number;
  missing_count?: number;
  missing_percentage?: number;
  task: 'classification' | 'regression' | null;
  task_type: 'binary_classification' | 'multiclass_classification' | 'regression' | null;
  confidence: number;
  reason: string;
  status: 'target_required' | 'invalid_target' | 'detected' | 'unsupported';
}

export interface MLRecommendation {
  status: 'available' | 'unavailable' | 'unsupported';
  task: string | null;
  task_type: string | null;
  target: string | null;
  recommended_models: Array<{ model: string; reason: string }>;
  preprocessing: string[];
  reasoning: string[];
}

export interface PreprocessingRecommendation {
  column: string | null;
  type: string;
  priority: 'high' | 'medium' | 'low';
  action: string;
  message: string;
  columns?: string[];
  correlation?: number;
}

export interface Preprocessing {
  status: string;
  recommendation_count: number;
  dataset_status: string;
  recommendations: PreprocessingRecommendation[];
}

export interface FeatureImportance {
  status: 'available' | 'error' | 'insufficient_data' | 'unavailable';
  error?: string;
  task_type?: string;
  target?: string;
  feature_count?: number;
  random_forest: Array<{ feature: string; importance: number; rank: number }>;
  mutual_information: Array<{ feature: string; score: number; normalized_score: number; rank: number }>;
}

export interface TargetAnalysis {
  [key: string]: unknown;
}

export interface EDAResult {
  numeric_statistics: Record<string, NumericStats>;
  correlation_analysis: CorrelationAnalysis;
  outliers: Record<string, OutlierInfo>;
  missingness: MissingnessAnalysis;
  target_analysis: TargetAnalysis | null;
  quality_score: QualityScore;
  insights: DatasetInsights;
  feature_summary: FeatureSummary;
  ml_task: MLTask;
  ml_recommendation: MLRecommendation;
  preprocessing: Preprocessing;
  feature_importance: FeatureImportance;
  report: {
    dataset: { rows: number; columns: number };
    quality: { score: number; grade: string; status: string };
    ml_task: MLTask;
    key_findings: string[];
    recommended_models: string[];
    preprocessing: string[];
  };
}

export interface SpecialistAgentOutput {
  findings: string | null;
  risk_level: string;
  recommendations: string[];
  error?: string;
}

export interface AgentExtra {
  llm_call_count?: number;
  per_node_time?: Record<string, number>;
  specialist_outputs?: Record<string, SpecialistAgentOutput>;
  [key: string]: unknown;
}

export interface AgentResponse {
  status: 'success' | 'error' | 'unavailable';
  model: string;
  pipeline: 'single_agent' | 'multi_agent';
  execution_time_seconds: number;
  narrative: string | null;
  key_risks: string[];
  recommendations: string[];
  confidence: number | null;
  error: string | null;
  extra: AgentExtra;
}

export interface FullAnalysisResult {
  eda: EDAResult;
  agent: AgentResponse;
}
