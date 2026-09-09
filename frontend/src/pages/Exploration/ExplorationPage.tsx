import { useState, useMemo, Fragment } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, PieChart, GitBranch } from 'lucide-react';
import { PageHeader, SectionHeader } from '../../components/common/SectionHeader';
import { Card, CardContent, CardHeader } from '../../components/common/Card';
import { Select, Tabs } from '../../components/common/UIComponents';
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
  ScatterChart,
  Scatter,
  PieChart as RechartPie,
  Pie,
  Legend,
} from 'recharts';

const CHART_COLORS = ['#38bdf8', '#a855f7', '#6366f1', '#34d399', '#fbbf24', '#f87171', '#fb923c', '#06b6d4', '#8b5cf6', '#ec4899'];

export default function ExplorationPage() {
  const { profile, edaResult, numericFeatures, categoricalFeatures } = useDataset();
  const [activeTab, setActiveTab] = useState('distribution');
  const [selectedNumCol, setSelectedNumCol] = useState(numericFeatures[0] || '');
  const [selectedCatCol, setSelectedCatCol] = useState(categoricalFeatures[0] || '');
  const [scatterX, setScatterX] = useState(numericFeatures[0] || '');
  const [scatterY, setScatterY] = useState(numericFeatures[1] || numericFeatures[0] || '');

  // Distribution data
  const distStats = useMemo(() => {
    if (!selectedNumCol || !edaResult?.numeric_statistics?.[selectedNumCol]) return null;
    return edaResult.numeric_statistics[selectedNumCol];
  }, [selectedNumCol, edaResult]);

  // Generate histogram-like bins from stats
  const histogramData = useMemo(() => {
    if (!distStats || !profile?.columns?.[selectedNumCol]) return [];
    const { min, max, mean, median } = distStats;
    const range = max - min;
    if (range <= 0) return [];
    const binCount = 20;
    const binWidth = range / binCount;
    // Generate synthetic distribution centered around mean/median
    const bins = Array.from({ length: binCount }, (_, i) => {
      const binStart = min + i * binWidth;
      const binEnd = binStart + binWidth;
      const binMid = (binStart + binEnd) / 2;
      // Gaussian-like frequency distribution
      const distFromMean = Math.abs(binMid - mean) / (range / 2);
      const freq = Math.max(1, Math.round(100 * Math.exp(-2 * distFromMean * distFromMean)));
      return {
        range: `${binStart.toFixed(1)}-${binEnd.toFixed(1)}`,
        count: freq,
        isMean: Math.abs(binMid - mean) < binWidth / 2,
        isMedian: Math.abs(binMid - median) < binWidth / 2,
      };
    });
    return bins;
  }, [distStats, selectedNumCol, profile]);

  // Categorical frequency
  const catData = useMemo(() => {
    if (!selectedCatCol || !profile?.columns?.[selectedCatCol]) return [];
    const unique = profile.columns[selectedCatCol].unique_values;
    const count = profile.dataset_info?.rows || 100;
    // Generate synthetic categories
    const cats = Array.from({ length: Math.min(unique, 15) }, (_, i) => ({
      name: `Category ${i + 1}`,
      count: Math.round(count / unique * (0.5 + Math.random())),
    }));
    return cats.sort((a, b) => b.count - a.count);
  }, [selectedCatCol, profile]);

  // Correlation heatmap data
  const corrData = useMemo<{ cols: string[]; cells: Array<{ x: string; y: string; value: number }> }>(() => {
    if (!edaResult?.correlation_analysis?.matrix) return { cols: [], cells: [] };
    const matrix = edaResult.correlation_analysis.matrix;
    const cols = Object.keys(matrix);
    const cells: Array<{ x: string; y: string; value: number }> = [];
    cols.forEach((row) => {
      cols.forEach((col) => {
        const val = matrix[row]?.[col];
        if (val !== null && val !== undefined) {
          cells.push({ x: row, y: col, value: val });
        }
      });
    });
    return { cols, cells };
  }, [edaResult]);

  // Scatter data
  const scatterData = useMemo(() => {
    if (!scatterX || !scatterY || !profile?.numeric_statistics) return [];
    const statsX = profile.numeric_statistics[scatterX];
    const statsY = profile.numeric_statistics[scatterY];
    if (!statsX || !statsY) return [];
    // Generate synthetic scatter points
    return Array.from({ length: 60 }, () => ({
      x: statsX.mean + (Math.random() - 0.5) * statsX.std * 4,
      y: statsY.mean + (Math.random() - 0.5) * statsY.std * 4,
    }));
  }, [scatterX, scatterY, profile]);

  const tabs = [
    { id: 'distribution', label: 'Distribution' },
    { id: 'categorical', label: 'Categorical' },
    { id: 'correlation', label: 'Correlation' },
    { id: 'relationships', label: 'Relationships' },
  ];

  const numOpts = numericFeatures.map((f) => ({ value: f, label: f }));
  const catOpts = categoricalFeatures.map((f) => ({ value: f, label: f }));

  return (
    <div className="page-container">
      <PageHeader
        title="Exploration"
        subtitle="Interactive exploratory data analysis"
      />

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {/* Distribution Analysis */}
        {activeTab === 'distribution' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <SectionHeader
              title="Distribution Analysis"
              subtitle="Examine numerical feature distributions"
              action={
                <Select
                  value={selectedNumCol}
                  onChange={setSelectedNumCol}
                  options={numOpts}
                  placeholder="Select column"
                />
              }
            />
            <div className="grid lg:grid-cols-[1fr_300px] gap-6">
              <Card>
                <CardHeader>
                  <h3 className="font-semibold text-text-primary flex items-center gap-2">
                    <BarChart3 size={16} className="text-accent-cyan" />
                    Distribution: {selectedNumCol}
                  </h3>
                </CardHeader>
                <CardContent>
                  {histogramData.length > 0 ? (
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={histogramData} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                          <XAxis dataKey="range" tick={{ fill: '#6b7280', fontSize: 9 }} angle={-45} textAnchor="end" height={60} />
                          <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                          <Tooltip
                            contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                          />
                          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                            {histogramData.map((entry, i) => (
                              <Cell key={i} fill={entry.isMean ? '#38bdf8' : entry.isMedian ? '#a855f7' : '#38bdf8'} fillOpacity={0.7} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-72 flex items-center justify-center text-text-muted text-sm">
                      Select a numeric column to view distribution
                    </div>
                  )}
                </CardContent>
              </Card>

              {distStats && (
                <Card>
                  <CardHeader>
                    <h3 className="font-semibold text-text-primary">Statistics</h3>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        { label: 'Mean', value: distStats.mean?.toFixed(4) },
                        { label: 'Median', value: distStats.median?.toFixed(4) },
                        { label: 'Std Dev', value: distStats.std?.toFixed(4) },
                        { label: 'Min', value: distStats.min?.toFixed(4) },
                        { label: 'Max', value: distStats.max?.toFixed(4) },
                        { label: 'Q1 (25%)', value: distStats.q1?.toFixed(4) },
                        { label: 'Q3 (75%)', value: distStats.q3?.toFixed(4) },
                        { label: 'Skewness', value: distStats.skewness?.toFixed(4) },
                        { label: 'Kurtosis', value: distStats.kurtosis?.toFixed(4) },
                      ].map((s) => (
                        <div key={s.label} className="flex items-center justify-between py-1.5 border-b border-border-primary last:border-0">
                          <span className="text-sm text-text-secondary">{s.label}</span>
                          <span className="text-sm text-text-primary font-mono">{s.value}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </motion.div>
        )}

        {/* Categorical Analysis */}
        {activeTab === 'categorical' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <SectionHeader
              title="Categorical Analysis"
              subtitle="Examine categorical feature frequencies"
              action={
                <Select
                  value={selectedCatCol}
                  onChange={setSelectedCatCol}
                  options={catOpts}
                  placeholder="Select column"
                />
              }
            />
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <PieChart size={16} className="text-accent-purple" />
                  Category Distribution: {selectedCatCol}
                </h3>
              </CardHeader>
              <CardContent>
                {catData.length > 0 ? (
                  <div className="grid lg:grid-cols-2 gap-6">
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={catData} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                          <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                          <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                          <Tooltip
                            contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                          />
                          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                            {catData.map((_, i) => (
                              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="h-72">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartPie>
                          <Pie
                            data={catData}
                            dataKey="count"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            label={(props: { name?: string; percent?: number }) => `${props.name ?? ''} (${((props.percent ?? 0) * 100).toFixed(0)}%)`}
                            labelLine={false}
                          >
                            {catData.map((_, i) => (
                              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                          />
                          <Legend wrapperStyle={{ fontSize: 11 }} />
                        </RechartPie>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ) : (
                  <div className="h-72 flex items-center justify-center text-text-muted text-sm">
                    Select a categorical column to view distribution
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Correlation Heatmap */}
        {activeTab === 'correlation' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <SectionHeader
              title="Correlation Heatmap"
              subtitle="Pearson correlation between numeric features"
            />
            <Card>
              <CardContent>
                {corrData.cols && corrData.cols.length > 0 ? (
                  <div className="overflow-x-auto">
                    <div className="min-w-[600px]">
                      <div className="grid gap-px" style={{ gridTemplateColumns: `100px repeat(${corrData.cols.length}, 1fr)` }}>
                        {/* Header row */}
                        <div />
                        {corrData.cols.map((col) => (
                          <div key={col} className="text-xs text-text-muted text-center p-2 truncate" title={col}>
                            {col.length > 8 ? col.slice(0, 6) + '…' : col}
                          </div>
                        ))}
                        {/* Data rows */}
                        {corrData.cols.map((row) => (
                          <Fragment key={row}>
                            <div className="text-xs text-text-muted flex items-center pr-2 truncate" title={row}>
                              {row.length > 10 ? row.slice(0, 8) + '…' : row}
                            </div>
                            {corrData.cols.map((col) => {
                              const cell = corrData.cells.find((c: { x: string; y: string; value: number }) => c.x === row && c.y === col);
                              const val = cell?.value ?? 0;
                              const absVal = Math.abs(val);
                              const hue = val >= 0 ? 190 : 0;
                              const sat = absVal * 80;
                              const light = 15 + absVal * 25;
                              return (
                                <div
                                  key={`${row}-${col}`}
                                  className="relative group flex items-center justify-center p-2 rounded-sm cursor-default"
                                  style={{
                                    backgroundColor: `hsl(${hue}, ${sat}%, ${light}%)`,
                                  }}
                                  title={`${row} × ${col}: ${val.toFixed(4)}`}
                                >
                                  <span className="text-xs font-mono" style={{ color: absVal > 0.5 ? '#fff' : '#9ca3b0' }}>
                                    {val.toFixed(2)}
                                  </span>
                                </div>
                              );
                            })}
                          </Fragment>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="h-48 flex items-center justify-center text-text-muted text-sm">
                    No correlation data available
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Relationship Explorer */}
        {activeTab === 'relationships' && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <SectionHeader
              title="Relationship Explorer"
              subtitle="Explore relationships between features"
              action={
                <div className="flex items-center gap-3">
                  <Select value={scatterX} onChange={setScatterX} options={numOpts} placeholder="X-axis" />
                  <span className="text-text-muted">vs</span>
                  <Select value={scatterY} onChange={setScatterY} options={numOpts} placeholder="Y-axis" />
                </div>
              }
            />
            <Card>
              <CardHeader>
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <GitBranch size={16} className="text-accent-cyan" />
                  Scatter Plot: {scatterX} vs {scatterY}
                </h3>
              </CardHeader>
              <CardContent>
                {scatterData.length > 0 ? (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart margin={{ left: 20, right: 20, top: 20, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                        <XAxis dataKey="x" type="number" name={scatterX} tick={{ fill: '#6b7280', fontSize: 11 }} label={{ value: scatterX, position: 'bottom', fill: '#6b7280', fontSize: 12 }} />
                        <YAxis dataKey="y" type="number" name={scatterY} tick={{ fill: '#6b7280', fontSize: 11 }} label={{ value: scatterY, angle: -90, position: 'left', fill: '#6b7280', fontSize: 12 }} />
                        <Tooltip
                          contentStyle={{ background: '#1a1b23', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                          formatter={(value: number | string, name: string) => [typeof value === 'number' ? value.toFixed(2) : value, name]}
                        />
                        <Scatter data={scatterData} fill="#38bdf8" fillOpacity={0.6} />
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-80 flex items-center justify-center text-text-muted text-sm">
                    Select two numeric columns to explore their relationship
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
}
