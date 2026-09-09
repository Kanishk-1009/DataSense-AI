import { useMemo } from 'react';
import {
  AlertTriangle,
  Copy,
  Info,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { RadialScore } from '../../components/common/RadialScore';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { IssueCard, EmptyState } from '../../components/common/IssueCard';
import { Badge } from '../../components/common/UIComponents';
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

interface MissingColumn {
  missing_count: number;
  missing_percentage: number;
}

interface OutlierData {
  count: number;
  percentage: number;
}

interface ColumnProfile {
  unique_values: number;
}

interface Recommendation {
  priority: string;
  column?: string;
  message: string;
}

export default function DataQualityPage() {
  const { profile, edaResult } = useDataset();

  const quality = edaResult?.quality_score;
  const missingness = edaResult?.missingness;
  const outliers = edaResult?.outliers;

  const duplicateCount = profile?.dataset_info?.duplicate_rows || 0;
  const totalRows = profile?.dataset_info?.rows || 1;
  const duplicatePct = ((duplicateCount / totalRows) * 100).toFixed(1);

  const missingChartData = useMemo(() => {
    if (!missingness?.columns) return [];
    return (Object.entries(missingness.columns) as [string, MissingColumn][])
      .filter(([, v]) => v.missing_count > 0)
      .map(([name, v]) => ({
        name: name.length > 12 ? name.slice(0, 10) + '…' : name,
        fullName: name,
        count: v.missing_count,
        percentage: v.missing_percentage,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 15);
  }, [missingness]);

  const outlierChartData = useMemo(() => {
    if (!outliers) return [];
    return (Object.entries(outliers) as [string, OutlierData][])
      .filter(([, v]) => v.count > 0)
      .map(([name, v]) => ({
        name: name.length > 12 ? name.slice(0, 10) + '…' : name,
        fullName: name,
        count: v.count,
        percentage: v.percentage,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 15);
  }, [outliers]);

  const outlierCount = outlierChartData.reduce((sum, d) => sum + d.count, 0);

  const constantCols = useMemo(() => {
    if (!profile?.columns) return [];
    return (Object.entries(profile.columns) as [string, ColumnProfile][])
      .filter(([, v]) => v.unique_values <= 1)
      .map(([name]) => name);
  }, [profile]);

  const issues = useMemo(() => {
    const list: Array<{ severity: 'critical' | 'warning' | 'info' | 'success'; title: string; message: string }> = [];

    if (quality?.issues) {
      quality.issues.forEach((issue: string) => {
        const sev = issue.toLowerCase().includes('critical') ? 'critical' as const
          : issue.toLowerCase().includes('duplicate') || issue.toLowerCase().includes('outlier') ? 'warning' as const
          : 'info' as const;
        list.push({ severity: sev, title: 'Data Quality Issue', message: issue });
      });
    }

    if (constantCols.length > 0) {
      list.push({
        severity: 'warning',
        title: 'Constant Columns',
        message: `${constantCols.length} column(s) have no variation: ${constantCols.join(', ')}.`,
      });
    }

    if (duplicateCount > 0) {
      list.push({
        severity: 'warning',
        title: 'Duplicate Records',
        message: `${duplicateCount} duplicate row(s) detected (${duplicatePct}% of dataset).`,
      });
    }

    return list;
  }, [quality, constantCols, duplicateCount, duplicatePct]);

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    if (score >= 60) return 'Fair';
    if (score >= 40) return 'Poor';
    return 'Critical';
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Data Quality"
        subtitle="Comprehensive data quality assessment"
      />

      {/* Quality Score + Missing + Duplicates row */}
      <div className="grid lg:grid-cols-[280px_1fr_1fr] gap-6 mb-8">
        <Card>
          <CardContent className="flex flex-col items-center py-8">
            <RadialScore
              score={quality?.score || 0}
              size={160}
              strokeWidth={12}
              label={quality?.grade || getScoreLabel(quality?.score || 0)}
              sublabel="Quality Score"
            />
            {quality && (
              <div className="mt-4 space-y-1.5 w-full">
                {quality.strengths.slice(0, 2).map((s: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-green-400">
                    <CheckCircle size={12} className="mt-0.5 shrink-0" />
                    <span>{s}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Missing Values */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-400" />
                Missing Values
              </h3>
              <Badge variant="amber">
                {missingness?.summary?.total_missing_cells || 0} cells
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="p-3 rounded-lg bg-bg-glass border border-border-primary">
                <p className="text-xs text-text-muted">Affected Columns</p>
                <p className="text-lg font-bold text-text-primary">{missingness?.summary?.columns_with_missing || 0}</p>
              </div>
              <div className="p-3 rounded-lg bg-bg-glass border border-border-primary">
                <p className="text-xs text-text-muted">Overall Missing</p>
                <p className="text-lg font-bold text-text-primary">{missingness?.summary?.overall_missing_percentage || 0}%</p>
              </div>
            </div>
            {missingChartData.length > 0 ? (
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={missingChartData} layout="vertical" margin={{ left: 8, right: 8, top: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <YAxis dataKey="name" type="category" width={80} tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                      labelStyle={{ color: '#f0f0f5' }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter={(_value: any, _name: any, props: { payload: { fullName: string; percentage: number } }) => [`${_value} (${props.payload.percentage}%)`, props.payload.fullName]}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {missingChartData.map((_, i) => (
                        <Cell key={i} fill="#fbbf24" fillOpacity={0.8 - i * 0.04} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState icon={<CheckCircle size={24} />} title="No Missing Values" message="All cells are complete." />
            )}
          </CardContent>
        </Card>

        {/* Duplicates */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-text-primary flex items-center gap-2">
                <Copy size={16} className="text-red-400" />
                Duplicate Records
              </h3>
              <Badge variant={duplicateCount > 0 ? 'red' : 'green'}>
                {duplicateCount} rows
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-bg-glass border border-border-primary text-center">
                <p className="text-4xl font-bold text-text-primary">{duplicateCount}</p>
                <p className="text-sm text-text-secondary mt-1">{duplicatePct}% of dataset</p>
              </div>
              <div className="h-2 rounded-full bg-bg-glass overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(parseFloat(duplicatePct), 100)}%`,
                    backgroundColor: duplicateCount > 0 ? '#f87171' : '#34d399',
                  }}
                />
              </div>
              {duplicateCount > 0 ? (
                <p className="text-sm text-text-secondary">
                  Review duplicate rows before model training to avoid data leakage.
                </p>
              ) : (
                <p className="text-sm text-green-400 flex items-center gap-2">
                  <CheckCircle size={14} />
                  No duplicate records detected.
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Outliers */}
      <SectionHeader title="Outlier Analysis" subtitle="Statistical outliers detected across numeric features" />
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-text-primary">Outlier Distribution</h3>
              <Badge variant="amber">{outlierCount} total outliers</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {outlierChartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={outlierChartData} margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter={(_value: any, _name: any, props: { payload: { fullName: string; percentage: number } }) => [`${_value} (${props.payload.percentage}%)`, props.payload.fullName]}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {outlierChartData.map((_, i) => (
                        <Cell key={i} fill="#fb923c" fillOpacity={0.8 - i * 0.04} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <EmptyState icon={<CheckCircle size={24} />} title="No Outliers" message="No statistical outliers detected." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-semibold text-text-primary flex items-center gap-2">
              <Info size={16} className="text-accent-cyan" />
              Missingness Pattern
            </h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="p-3 rounded-lg bg-bg-glass border border-border-primary">
                <p className="text-text-muted text-xs mb-1">Heuristic Note</p>
                <p className="text-text-secondary">{missingness?.summary?.heuristic_note || 'No missingness analysis available.'}</p>
              </div>
              {missingness?.summary?.likely_mar_columns && missingness.summary.likely_mar_columns.length > 0 && (
                <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                  <p className="text-amber-400 text-xs font-medium mb-1">Likely MAR (Missing at Random)</p>
                  <p className="text-text-secondary">{missingness.summary.likely_mar_columns.join(', ')}</p>
                </div>
              )}
              {missingness?.summary?.likely_mcar_columns && missingness.summary.likely_mcar_columns.length > 0 && (
                <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20">
                  <p className="text-blue-400 text-xs font-medium mb-1">Likely MCAR (Missing Completely at Random)</p>
                  <p className="text-text-secondary">{missingness.summary.likely_mcar_columns.join(', ')}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Issues & Recommendations */}
      {issues.length > 0 && (
        <>
          <SectionHeader title="Issues & Recommendations" subtitle="Detected problems and suggested actions" />
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
            {issues.map((issue, i: number) => (
              <IssueCard key={i} {...issue} />
            ))}
          </div>
        </>
      )}

      {/* Preprocessing Recommendations */}
      {edaResult?.preprocessing?.recommendations && edaResult.preprocessing.recommendations.length > 0 && (
        <>
          <SectionHeader title="Preprocessing Recommendations" subtitle="Suggested data preprocessing steps" />
          <Card className="mb-8">
            <CardContent>
              <div className="space-y-3">
                {edaResult.preprocessing.recommendations.slice(0, 8).map((rec: Recommendation, i: number) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded-lg bg-bg-glass border border-border-primary"
                  >
                    <div className={`mt-0.5 p-1 rounded ${rec.priority === 'high' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'}`}>
                      {rec.priority === 'high' ? <XCircle size={14} /> : <AlertTriangle size={14} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        {rec.column && <Badge variant="cyan" size="sm">{rec.column}</Badge>}
                        <Badge variant={rec.priority === 'high' ? 'red' : 'amber'} size="sm">{rec.priority}</Badge>
                      </div>
                      <p className="text-sm text-text-secondary">{rec.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
