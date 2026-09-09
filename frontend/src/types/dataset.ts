export interface ColumnProfile {
  dtype: string;
  column_type: 'numeric' | 'categorical' | 'binary' | 'datetime' | 'unknown';
  unique_values: number;
}

export interface MissingValueInfo {
  count: number;
  percentage: number;
}

export interface CategoricalStats {
  most_frequent: string | number | null;
  frequency: number;
}

export interface NumericStats {
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  q1: number;
  q3: number;
  skewness: number;
  kurtosis: number;
}

export interface DatasetProfile {
  dataset_info: {
    rows: number;
    columns: number;
    duplicate_rows: number;
  };
  columns: Record<string, ColumnProfile>;
  missing_values: Record<string, MissingValueInfo>;
  numeric_statistics: Record<string, NumericStats>;
  categorical_statistics: Record<string, CategoricalStats>;
  warnings: string[];
}
