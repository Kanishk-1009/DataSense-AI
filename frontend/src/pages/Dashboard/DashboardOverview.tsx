import { Fragment, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Database,
  Columns3,
  AlertTriangle,
  Copy,
  Hash,
  Tag,
  Search,
  ChevronDown,
  ChevronUp,
  Info,
  ShieldCheck,
  Compass,
  Brain,
  Rocket,
  ArrowRight,
  Sparkles,
  MessageSquare,
} from 'lucide-react';
import { PageHeader } from '../../components/common/SectionHeader';
import { StatCard } from '../../components/common/StatCard';
import { RadialScore } from '../../components/common/RadialScore';
import { Badge, Select } from '../../components/common/UIComponents';
import { Card, CardContent } from '../../components/common/Card';
import { useDataset } from '../../hooks/useDataset';
import { useDatasetStore } from '../../store/datasetStore';
import type { ColumnProfile, MissingValueInfo } from '../../types/dataset';

type SortKey = 'name' | 'type' | 'missing' | 'unique';
type SortDir = 'asc' | 'desc';

const quickNav = [
  { to: '/dashboard/quality', label: 'Data Quality', icon: ShieldCheck, desc: 'Quality score, missingness & outliers', color: 'text-accent-cyan', bg: 'bg-accent-cyan/10' },
  { to: '/dashboard/exploration', label: 'Exploration', icon: Compass, desc: 'Distributions, correlations & relationships', color: 'text-accent-blue', bg: 'bg-accent-blue/10' },
  { to: '/dashboard/insights', label: 'AI Insights', icon: Brain, desc: 'Narrative analysis & feature importance', color: 'text-accent-purple', bg: 'bg-accent-purple/10' },
  { to: '/dashboard/ml-readiness', label: 'ML Readiness', icon: Rocket, desc: 'Task detection & model recommendations', color: 'text-accent-green', bg: 'bg-accent-green/10' },
];

export default function DashboardOverview() {
  const navigate = useNavigate();
  const { profile, edaResult, fileName, healthScore, healthGrade } = useDataset();
  const agentResult = useDatasetStore((s) => s.agentResult);
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [expandedCol, setExpandedCol] = useState<string | null>(null);

  const info = profile?.dataset_info;
  const columns = useMemo(() => profile?.columns || {}, [profile]);
  const missingVals = useMemo(() => profile?.missing_values || {}, [profile]);
  const warnings = profile?.warnings || [];

  const numericCount = useMemo(
    () => Object.values(columns).filter((c: ColumnProfile) => c.column_type === 'numeric').length,
    [columns],
  );
  const catCount = useMemo(
    () => Object.values(columns).filter((c: ColumnProfile) => c.column_type === 'categorical' || c.column_type === 'binary').length,
    [columns],
  );
  const totalMissing = useMemo(
    () => Object.values(missingVals).reduce((sum: number, v: MissingValueInfo) => sum + v.count, 0),
    [missingVals],
  );

  const schemaData = useMemo(() => {
    const rows = Object.entries(columns).map(([name, col]: [string, ColumnProfile]) => ({
      name,
      type: col.column_type,
      dtype: col.dtype,
      missing: missingVals[name]?.count || 0,
      missingPct: missingVals[name]?.percentage || 0,
      unique: col.unique_values,
      quality: missingVals[name]?.percentage === 0 ? 'good' : missingVals[name]?.percentage < 10 ? 'warning' : 'critical',
      stats: profile?.numeric_statistics?.[name],
    }));

    const filtered = rows.filter((r) =>
      r.name.toLowerCase().includes(search.toLowerCase()),
    );

    filtered.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'name': cmp = a.name.localeCompare(b.name); break;
        case 'type': cmp = a.type.localeCompare(b.type); break;
        case 'missing': cmp = a.missing - b.missing; break;
        case 'unique': cmp = a.unique - b.unique; break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });

    return filtered;
  }, [columns, missingVals, search, sortKey, sortDir, profile]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const typeBadge = (type: string) => {
    const map: Record<string, 'cyan' | 'purple' | 'green' | 'amber' | 'default'> = {
      numeric: 'cyan',
      categorical: 'purple',
      binary: 'green',
      datetime: 'amber',
      unknown: 'default',
    };
    return <Badge variant={map[type] || 'default'}>{type}</Badge>;
  };

  const qualityDot = (q: string) => {
    const colors: Record<string, string> = {
      good: 'bg-green-400',
      warning: 'bg-amber-400',
      critical: 'bg-red-400',
    };
    return <span className={`inline-block w-2 h-2 rounded-full ${colors[q] || 'bg-gray-400'}`} />;
  };

  const keyFindings = edaResult?.report?.key_findings || edaResult?.insights?.insights || [];
  const keyFindingsCount = keyFindings.length;

  if (!profile) return null;

  return (
    <div className="page-container">
      <PageHeader
        title="Dataset Overview"
        subtitle={`Analyzing ${fileName || 'dataset'} · Last analyzed just now`}
      >
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/10 text-green-400 text-sm font-medium border border-green-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Analysis Complete
          </span>
        </div>
      </PageHeader>

      {/* AI Analysis Ready banner */}
      {agentResult?.status === 'success' && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 rounded-xl border border-accent-purple/20 bg-accent-purple/5 p-5"
        >
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <div className="p-2.5 rounded-xl bg-accent-purple/10 border border-accent-purple/20 shrink-0">
                <Sparkles size={18} className="text-accent-purple" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-text-primary">
                  AI Analysis Ready
                </p>
                <p className="text-xs text-text-secondary mt-0.5">
                  {agentResult.pipeline === 'multi_agent' ? 'Multi Agent' : 'Single Agent'} · {agentResult.model} · {agentResult.execution_time_seconds.toFixed(1)}s — {agentResult.key_risks.length} risks · {agentResult.recommendations.length} recommendations
                </p>
              </div>
            </div>
            <button
              onClick={() => navigate('/dashboard/insights')}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-purple/10 text-accent-purple border border-accent-purple/20 hover:bg-accent-purple/20 transition-colors text-sm font-medium shrink-0"
            >
              View AI Insights
              <ArrowRight size={15} />
            </button>
          </div>
        </motion.div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <StatCard icon={Database} label="Rows" value={(info?.rows || 0).toLocaleString()} sublabel="Total records" color="text-accent-cyan" index={0} />
        <StatCard icon={Columns3} label="Columns" value={info?.columns || 0} sublabel="Features" color="text-accent-blue" index={1} />
        <StatCard icon={AlertTriangle} label="Missing" value={totalMissing.toLocaleString()} sublabel="Cells affected" color="text-amber-400" index={2} />
        <StatCard icon={Copy} label="Duplicates" value={info?.duplicate_rows || 0} sublabel="Duplicate rows" color="text-red-400" index={3} />
        <StatCard icon={Hash} label="Numeric" value={numericCount} sublabel="Features" color="text-cyan-400" index={4} />
        <StatCard icon={Tag} label="Categorical" value={catCount} sublabel="Features" color="text-purple-400" index={5} />
      </div>

      {/* Quick-nav cards */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {quickNav.map((q, i) => (
          <motion.button
            key={q.to}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.05 }}
            onClick={() => navigate(q.to)}
            className="text-left rounded-xl border border-border-primary bg-bg-card p-5 hover:border-border-secondary hover:bg-bg-card-hover transition-colors group cursor-pointer"
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2.5 rounded-lg ${q.bg} ${q.color}`}>
                <q.icon size={18} />
              </div>
              <ArrowRight size={15} className="text-text-muted group-hover:text-accent-cyan group-hover:translate-x-0.5 transition-all" />
            </div>
            <h4 className="font-medium text-text-primary text-sm mb-1">{q.label}</h4>
            <p className="text-xs text-text-muted leading-relaxed">{q.desc}</p>
          </motion.button>
        ))}
      </div>

      {/* Key Findings (report summary) */}
      {keyFindingsCount > 0 && (
        <div className="mb-8 rounded-xl border border-border-primary bg-gradient-to-br from-accent-cyan/5 to-accent-purple/5 p-5">
          <div className="flex items-center gap-2 mb-3">
            <Info size={15} className="text-accent-cyan" />
            <h3 className="font-semibold text-text-primary text-sm">Report Summary — Key Findings</h3>
            <Badge variant="cyan">{keyFindingsCount}</Badge>
          </div>
          <div className="grid gap-2">
            {keyFindings.slice(0, 6).map((f: string, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex items-start gap-2.5 text-sm text-text-secondary"
              >
                <span className="text-accent-cyan mt-0.5 shrink-0">→</span>
                {f}
              </motion.div>
            ))}
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-[1fr_280px] gap-6">
        {/* Schema Table */}
        <Card>
          <div className="px-5 py-4 border-b border-border-primary">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <h3 className="font-semibold text-text-primary">Dataset Schema</h3>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search columns..."
                    className="pl-8 pr-3 py-1.5 rounded-lg bg-bg-glass border border-border-primary text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors w-48"
                  />
                </div>
                <Select
                  value={sortKey}
                  onChange={(v) => setSortKey(v as SortKey)}
                  options={[
                    { value: 'name', label: 'Name' },
                    { value: 'type', label: 'Type' },
                    { value: 'missing', label: 'Missing' },
                    { value: 'unique', label: 'Unique' },
                  ]}
                  className="w-28"
                />
              </div>
            </div>
          </div>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-primary bg-bg-glass">
                    <th className="px-4 py-3 text-left font-medium text-text-secondary cursor-pointer hover:text-text-primary" onClick={() => handleSort('name')}>
                      Column {sortKey === 'name' && (sortDir === 'asc' ? <ChevronUp size={12} className="inline" /> : <ChevronDown size={12} className="inline" />)}
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary">Type</th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary cursor-pointer hover:text-text-primary" onClick={() => handleSort('missing')}>
                      Missing {sortKey === 'missing' && (sortDir === 'asc' ? <ChevronUp size={12} className="inline" /> : <ChevronDown size={12} className="inline" />)}
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary cursor-pointer hover:text-text-primary" onClick={() => handleSort('unique')}>
                      Unique {sortKey === 'unique' && (sortDir === 'asc' ? <ChevronUp size={12} className="inline" /> : <ChevronDown size={12} className="inline" />)}
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary">Mean / Mode</th>
                    <th className="px-4 py-3 text-left font-medium text-text-secondary">Quality</th>
                    <th className="px-4 py-3 w-8" />
                  </tr>
                </thead>
                <tbody>
                  {schemaData.map((col) => (
                    <Fragment key={col.name}>
                      <tr
                        className="border-b border-border-primary last:border-0 hover:bg-bg-glass transition-colors cursor-pointer"
                        onClick={() => setExpandedCol(expandedCol === col.name ? null : col.name)}
                      >
                        <td className="px-4 py-3 font-medium text-text-primary">{col.name}</td>
                        <td className="px-4 py-3">{typeBadge(col.type)}</td>
                        <td className="px-4 py-3">
                          <span className={col.missing > 0 ? 'text-amber-400' : 'text-text-secondary'}>
                            {col.missing} ({col.missingPct}%)
                          </span>
                        </td>
                        <td className="px-4 py-3 text-text-secondary">{col.unique.toLocaleString()}</td>
                        <td className="px-4 py-3 text-text-secondary font-mono text-xs">
                          {col.stats?.mean !== undefined ? col.stats.mean.toFixed(2) : '-'}
                        </td>
                        <td className="px-4 py-3">{qualityDot(col.quality)}</td>
                        <td className="px-4 py-3">
                          {expandedCol === col.name ? <ChevronUp size={14} className="text-text-muted" /> : <ChevronDown size={14} className="text-text-muted" />}
                        </td>
                      </tr>
                      {expandedCol === col.name && (
                        <tr className="border-b border-border-primary bg-bg-glass/50">
                          <td colSpan={7} className="px-4 py-4">
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                              <div>
                                <span className="text-text-muted text-xs">Dtype</span>
                                <p className="text-text-primary font-mono">{col.dtype}</p>
                              </div>
                              <div>
                                <span className="text-text-muted text-xs">Unique Values</span>
                                <p className="text-text-primary">{col.unique.toLocaleString()}</p>
                              </div>
                              {col.stats && (
                                <>
                                  <div>
                                    <span className="text-text-muted text-xs">Min / Max</span>
                                    <p className="text-text-primary font-mono">{col.stats.min?.toFixed(2)} / {col.stats.max?.toFixed(2)}</p>
                                  </div>
                                  <div>
                                    <span className="text-text-muted text-xs">Std Dev</span>
                                    <p className="text-text-primary font-mono">{col.stats.std?.toFixed(2)}</p>
                                  </div>
                                  <div>
                                    <span className="text-text-muted text-xs">Q1 / Q3</span>
                                    <p className="text-text-primary font-mono">{col.stats.q1?.toFixed(2)} / {col.stats.q3?.toFixed(2)}</p>
                                  </div>
                                  <div>
                                    <span className="text-text-muted text-xs">Skewness</span>
                                    <p className="text-text-primary font-mono">{col.stats.skewness?.toFixed(2)}</p>
                                  </div>
                                  <div>
                                    <span className="text-text-muted text-xs">Kurtosis</span>
                                    <p className="text-text-primary font-mono">{col.stats.kurtosis?.toFixed(2)}</p>
                                  </div>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Side column: Health + Warnings */}
        <div className="space-y-6">
          <Card>
            <CardContent className="flex flex-col items-center py-8">
              <RadialScore
                score={healthScore}
                size={160}
                strokeWidth={12}
                label={healthGrade}
                sublabel="Dataset Health"
              />
              {edaResult?.quality_score && (
                <div className="mt-6 w-full space-y-2">
                  {edaResult.quality_score.strengths.slice(0, 3).map((s: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                      <span className="text-green-400 mt-0.5">&#10003;</span>
                      {s}
                    </div>
                  ))}
                  {edaResult.quality_score.issues.slice(0, 2).map((s: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                      <span className="text-amber-400 mt-0.5">&#9888;</span>
                      {s}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Warnings panel */}
          {warnings.length > 0 && (
            <Card>
              <div className="px-5 py-4 border-b border-border-primary">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <AlertTriangle size={16} className="text-amber-400" />
                  Warnings
                  <Badge variant="amber">{warnings.length}</Badge>
                </h3>
              </div>
              <CardContent>
                <div className="space-y-2.5">
                  {warnings.map((w, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                      className="flex items-start gap-2 text-xs text-text-secondary"
                    >
                      <AlertTriangle size={13} className="text-amber-400 mt-0.5 shrink-0" />
                      {w}
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {edaResult?.insights && (
            <Card>
              <div className="px-5 py-4 border-b border-border-primary">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <MessageSquare size={16} className="text-accent-cyan" />
                  Key Insights
                </h3>
              </div>
              <CardContent>
                <div className="space-y-3">
                  {edaResult.insights.insights.slice(0, 5).map((insight: string, i: number) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="text-sm text-text-secondary leading-relaxed"
                    >
                      {insight}
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}