import { useCallback } from 'react';
import { useDatasetStore } from '../store/datasetStore';

export function useDataset() {
  const {
    profile,
    edaResult,
    fileName,
    setProfile,
    setEdaResult,
    setFileName,
    clearDataset,
    isLoaded,
  } = useDatasetStore();

  const featureNames = profile ? Object.keys(profile.columns) : [];
  const numericFeatures = profile
    ? featureNames.filter((f) => profile.columns[f]?.column_type === 'numeric')
    : [];
  const categoricalFeatures = profile
    ? featureNames.filter(
        (f) =>
          profile.columns[f]?.column_type === 'categorical' ||
          profile.columns[f]?.column_type === 'binary',
      )
    : [];

  const healthScore = edaResult?.quality_score?.score ?? 0;
  const healthGrade = edaResult?.quality_score?.grade ?? 'Unknown';

  const getDistributionData = useCallback(
    (col: string) => {
      if (!edaResult?.numeric_statistics?.[col]) return null;
      const stats = edaResult.numeric_statistics[col];
      return stats;
    },
    [edaResult],
  );

  const getOutlierData = useCallback(
    (col: string) => {
      return edaResult?.outliers?.[col] ?? null;
    },
    [edaResult],
  );

  const getCorrelationMatrix = useCallback(() => {
    return edaResult?.correlation_analysis?.matrix ?? {};
  }, [edaResult]);

  return {
    profile,
    edaResult,
    fileName,
    featureNames,
    numericFeatures,
    categoricalFeatures,
    healthScore,
    healthGrade,
    isLoaded,
    setProfile,
    setEdaResult,
    setFileName,
    clearDataset,
    getDistributionData,
    getOutlierData,
    getCorrelationMatrix,
  };
}
