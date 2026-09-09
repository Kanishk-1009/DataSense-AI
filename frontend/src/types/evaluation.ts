export interface RubricCheckResult {
  condition_id: string;
  condition_description: string;
  condition_triggered: boolean;
  expected_keywords: string[];
  recommendation_matched: boolean;
}

export interface PipelineMetrics {
  pipeline: string;
  output_completeness: number;
  narrative_length_chars: number;
  key_risk_count: number;
  recommendation_count: number;
  confidence_score: number | null;
  execution_time_seconds: number;
  llm_call_count: number;
  recommendation_accuracy: number | null;
  rubric_checks: RubricCheckResult[];
  status: string;
  error: string | null;
}

export interface MetricComparison {
  metric: string;
  category: 'STRUCTURAL' | 'DESCRIPTIVE' | 'EFFICIENCY' | 'SELF-REPORTED' | 'CORRECTNESS';
  m4_value: unknown;
  m5_value: unknown;
  better_pipeline: string | null;
  note: string | null;
}

export interface EvaluationResult {
  run_id: string;
  dataset_name: string;
  dataset_hash: string;
  model: string;
  timestamp: string;
  m4: PipelineMetrics;
  m5: PipelineMetrics;
  comparison: MetricComparison[];
  research_note: string;
}
