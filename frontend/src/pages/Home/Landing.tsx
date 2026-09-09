import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle,
  Database,
  GitBranch,
  Loader2,
  ShieldCheck,
  Sparkles,
  Upload,
} from 'lucide-react';
import { useDatasetStore } from '../../store/datasetStore';
import { getDemoDataset, getDemoDatasetNames } from '../../data/demo';
import { runEDA, runSingleAgent, runMultiAgent } from '../../services/analysisApi';
import type { EDAResult } from '../../types/analysis';
import type { DatasetProfile } from '../../types/dataset';

const features = [
  { icon: Database, title: 'Schema Analysis', desc: 'Understand column types, missing values, and data structure.' },
  { icon: ShieldCheck, title: 'Data Quality', desc: 'Get quality scores, detect outliers, and identify issues.' },
  { icon: Sparkles, title: 'AI Insights', desc: 'Receive intelligent analysis and recommendations.' },
  { icon: Brain, title: 'ML Readiness', desc: 'Assess your dataset for machine learning readiness.' },
];

const stats = [
  { value: '5+', label: 'Demo Datasets' },
  { value: '50+', label: 'Quality Checks' },
  { value: 'AI', label: 'Powered Insights' },
  { value: '100%', label: 'Open Source' },
];

export default function Landing() {
  const navigate = useNavigate();
  const { setProfile, setEdaResult, setFileName, setUploadStage } = useDatasetStore();

  const handleLoadDemo = useCallback(
    (name: string) => {
      const demo = getDemoDataset(name);
      if (!demo) return;
      setProfile(demo.analysis.profile);
      setEdaResult(demo.analysis.eda);
      setFileName(demo.name);
      setUploadStage('success');
      navigate('/dashboard');
    },
    [navigate, setProfile, setEdaResult, setFileName, setUploadStage],
  );

  return (
    <div className="min-h-screen bg-bg-primary">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b border-border-primary bg-bg-primary/80 backdrop-blur-xl">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-accent-cyan to-accent-blue">
              <Database size={20} className="text-white" />
            </div>
            <span className="text-lg font-bold">
              DataSense <span className="text-accent-cyan">AI</span>
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => document.getElementById('upload')?.scrollIntoView({ behavior: 'smooth' })}
              className="text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Upload
            </button>
            <button
              onClick={() => handleLoadDemo('titanic.csv')}
              className="px-4 py-2 rounded-lg bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 hover:bg-accent-cyan/20 transition-colors text-sm font-medium"
            >
              Demo
            </button>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-accent-cyan/5 via-transparent to-transparent" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-accent-cyan/5 rounded-full blur-[120px]" />

        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-cyan/10 border border-accent-cyan/20 text-accent-cyan text-xs font-medium mb-6">
                <Sparkles size={14} />
                AI-Powered Dataset Intelligence
              </div>
              <h1 className="text-4xl lg:text-6xl font-bold leading-tight mb-6">
                <span className="text-gradient">Understand Your Data.</span>
                <br />
                <span className="text-text-primary">Before You Build ML.</span>
              </h1>
              <p className="text-lg text-text-secondary max-w-lg mb-8 leading-relaxed">
                DataSense AI transforms raw datasets into clear insights, visualizations, quality checks, and machine-learning recommendations.
              </p>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={() => document.getElementById('upload')?.scrollIntoView({ behavior: 'smooth' })}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-blue text-white font-semibold hover:opacity-90 transition-opacity"
                >
                  Analyze Dataset
                  <ArrowRight size={18} />
                </button>
                <button
                  onClick={() => handleLoadDemo('titanic.csv')}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl border border-border-secondary text-text-primary font-semibold hover:bg-bg-glass transition-colors"
                >
                  Explore Demo Dataset
                </button>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="relative h-[350px] lg:h-[450px]"
            >
              <div className="absolute inset-0 rounded-2xl border border-border-primary bg-bg-card/50 backdrop-blur-sm overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-accent-cyan/5 to-accent-purple/5" />
                {/* Fallback visual */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="relative w-full h-full">
                    {/* Animated grid */}
                    <div className="absolute inset-4 grid grid-cols-6 grid-rows-4 gap-2 opacity-20">
                      {Array.from({ length: 24 }).map((_, i) => (
                        <div
                          key={i}
                          className="rounded bg-accent-cyan/30"
                          style={{
                            animationDelay: `${i * 0.1}s`,
                            animation: 'pulse 3s ease-in-out infinite',
                          }}
                        />
                      ))}
                    </div>
                    {/* Floating data points */}
                    {[
                      { x: '20%', y: '30%', c: '#38bdf8', s: 12 },
                      { x: '60%', y: '20%', c: '#a855f7', s: 10 },
                      { x: '80%', y: '50%', c: '#34d399', s: 14 },
                      { x: '40%', y: '70%', c: '#fbbf24', s: 8 },
                      { x: '70%', y: '80%', c: '#6366f1', s: 11 },
                      { x: '30%', y: '50%', c: '#38bdf8', s: 9 },
                      { x: '50%', y: '40%', c: '#a855f7', s: 13 },
                      { x: '15%', y: '65%', c: '#34d399', s: 7 },
                    ].map((p, i) => (
                      <div
                        key={i}
                        className="absolute rounded-full animate-float"
                        style={{
                          left: p.x,
                          top: p.y,
                          width: p.s,
                          height: p.s,
                          backgroundColor: p.c,
                          boxShadow: `0 0 ${p.s * 2}px ${p.c}40`,
                          animationDelay: `${i * 0.7}s`,
                        }}
                      />
                    ))}
                    {/* Connection lines via SVG */}
                    <svg className="absolute inset-0 w-full h-full">
                      <line x1="20%" y1="30%" x2="60%" y2="20%" stroke="#38bdf8" strokeWidth="1" opacity="0.2" />
                      <line x1="60%" y1="20%" x2="80%" y2="50%" stroke="#a855f7" strokeWidth="1" opacity="0.2" />
                      <line x1="40%" y1="70%" x2="70%" y2="80%" stroke="#fbbf24" strokeWidth="1" opacity="0.2" />
                      <line x1="30%" y1="50%" x2="50%" y2="40%" stroke="#38bdf8" strokeWidth="1" opacity="0.2" />
                      <line x1="50%" y1="40%" x2="80%" y2="50%" stroke="#6366f1" strokeWidth="1" opacity="0.2" />
                      <line x1="15%" y1="65%" x2="40%" y2="70%" stroke="#34d399" strokeWidth="1" opacity="0.2" />
                    </svg>
                    {/* Center label */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-5xl font-bold text-gradient mb-2">DS</div>
                        <div className="text-sm text-text-muted">Data Intelligence</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-border-primary bg-bg-secondary/30">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="text-center"
              >
                <div className="text-2xl font-bold text-accent-cyan">{s.value}</div>
                <div className="text-sm text-text-secondary mt-1">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-text-primary mb-4">Everything You Need to Understand Your Data</h2>
            <p className="text-text-secondary max-w-2xl mx-auto">
              From schema analysis to ML readiness scoring, DataSense AI provides comprehensive dataset intelligence.
            </p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="rounded-xl border border-border-primary bg-bg-card p-6 hover:border-border-secondary transition-colors"
              >
                <div className="p-3 rounded-lg bg-accent-cyan/10 text-accent-cyan w-fit mb-4">
                  <f.icon size={22} />
                </div>
                <h3 className="font-semibold text-text-primary mb-2">{f.title}</h3>
                <p className="text-sm text-text-secondary leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Upload / Demo Section */}
      <section id="upload" className="py-20 border-t border-border-primary">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-text-primary mb-4">Get Started</h2>
            <p className="text-text-secondary max-w-xl mx-auto">
              Upload your CSV or explore one of our demo datasets.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* Upload area */}
            <UploadZone />

            {/* Demo datasets */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="rounded-xl border border-border-primary bg-bg-card p-6"
            >
              <h3 className="font-semibold text-text-primary mb-4">Demo Datasets</h3>
              <div className="space-y-2">
                {getDemoDatasetNames().map((name) => {
                  const demo = getDemoDataset(name);
                  return (
                    <button
                      key={name}
                      onClick={() => handleLoadDemo(name)}
                      className="w-full text-left p-3 rounded-lg border border-border-primary hover:border-border-secondary hover:bg-bg-glass transition-all duration-200 group"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="text-sm font-medium text-text-primary group-hover:text-accent-cyan transition-colors">
                            {name}
                          </span>
                          <p className="text-xs text-text-muted mt-0.5">{demo?.summary}</p>
                        </div>
                        <ArrowRight size={16} className="text-text-muted group-hover:text-accent-cyan transition-colors" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-primary py-8">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="p-1 rounded bg-gradient-to-br from-accent-cyan to-accent-blue">
              <Database size={14} className="text-white" />
            </div>
            <span className="font-semibold text-text-primary">DataSense AI</span>
          </div>
          <p className="text-sm text-text-muted">
            AI-Powered Dataset Intelligence Platform. B.Tech CSE-AIML Research Project.
          </p>
        </div>
      </footer>
    </div>
  );
}

type PipelineMode = 'eda' | 'single-agent' | 'multi-agent';

const pipelineOptions: Array<{
  value: PipelineMode;
  label: string;
  icon: typeof BarChart3;
  desc: string;
}> = [
  { value: 'eda', label: 'EDA Only', icon: BarChart3, desc: 'Deterministic analysis only. No LLM required.' },
  { value: 'single-agent', label: 'Single Agent', icon: Brain, desc: 'EDA + 1 LLM call (LangChain baseline).' },
  { value: 'multi-agent', label: 'Multi Agent', icon: GitBranch, desc: 'EDA + 7 specialist nodes (LangGraph).' },
];

function UploadZone() {
  const navigate = useNavigate();
  const {
    setProfile,
    setEdaResult,
    setFileName,
    setUploadStage,
    setAgentResult,
    uploadStage,
  } = useDatasetStore();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [target, setTarget] = useState('');
  const [pipeline, setPipeline] = useState<PipelineMode>('eda');
  const [model, setModel] = useState('llama3.1:8b');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const buildProfile = useCallback((eda: EDAResult): DatasetProfile => {
    return {
      dataset_info: {
        rows: eda.report?.dataset.rows ?? 0,
        columns: eda.report?.dataset.columns ?? 0,
        duplicate_rows: 0,
      },
      columns: Object.fromEntries(
        Object.entries(eda.feature_summary?.features ?? {}).map(([k, v]) => [
          k,
          {
            dtype: 'unknown',
            column_type: v.column_type,
            unique_values: v.unique_count,
          },
        ])
      ),
      missing_values: Object.fromEntries(
        Object.entries(eda.missingness?.columns ?? {}).map(([k, v]) => [
          k,
          { count: v.missing_count, percentage: v.missing_percentage },
        ])
      ),
      numeric_statistics: eda.numeric_statistics || {},
      categorical_statistics: {},
      warnings: [],
    };
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!selectedFile) return;
    setErrorMessage(null);
    setUploadStage('uploading');

    try {
      const edaResult = await runEDA(selectedFile, target || undefined);
      setProfile(buildProfile(edaResult));
      setEdaResult(edaResult);
      setFileName(selectedFile.name);

      if (pipeline === 'single-agent') {
        setUploadStage('analyzing');
        const result = await runSingleAgent(selectedFile, target || undefined, model, ollamaUrl);
        setAgentResult(result.agent);
        setEdaResult(result.eda);
      } else if (pipeline === 'multi-agent') {
        setUploadStage('analyzing');
        const result = await runMultiAgent(selectedFile, target || undefined, model, ollamaUrl);
        setAgentResult(result.agent);
        setEdaResult(result.eda);
      } else {
        setAgentResult(null);
      }

      setUploadStage('success');
      navigate('/dashboard');
    } catch (err) {
      setUploadStage('error');
      setErrorMessage(err instanceof Error ? err.message : 'Analysis failed');
    }
  }, [
    selectedFile,
    target,
    pipeline,
    model,
    ollamaUrl,
    navigate,
    setProfile,
    setEdaResult,
    setFileName,
    setUploadStage,
    setAgentResult,
    buildProfile,
  ]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
      setErrorMessage(null);
    }
  }, []);

  const onFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.name.endsWith('.csv')) {
      setSelectedFile(file);
      setErrorMessage(null);
    }
  }, []);

  const formatSize = (bytes: number) =>
    bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(2)} MB`;

  if (uploadStage === 'success') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: 'spring', stiffness: 200, damping: 24 }}
      >
        <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-8 text-center">
          <CheckCircle size={40} className="text-green-400 mx-auto mb-3" />
          <p className="text-text-primary font-medium">Dataset Ready — Navigating to dashboard...</p>
        </div>
      </motion.div>
    );
  }

  if (uploadStage === 'analyzing') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: 'spring', stiffness: 200, damping: 24 }}
      >
        <div className="rounded-xl border border-accent-purple/20 bg-accent-purple/5 p-8 text-center">
          <Loader2 size={32} className="animate-spin text-accent-purple mx-auto mb-4" />
          <p className="text-text-primary font-medium">🤖 Running AI Analysis (this may take 30–120s)...</p>
          <p className="text-sm text-text-muted mt-2">LLM analysis in progress — please wait</p>
        </div>
      </motion.div>
    );
  }

  if (uploadStage === 'error') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: 'spring', stiffness: 200, damping: 24 }}
      >
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-8 text-center">
          <AlertCircle size={40} className="text-red-400 mx-auto mb-3" />
          <p className="text-text-primary font-medium">Analysis Failed</p>
          <p className="text-sm text-text-secondary mt-1">{errorMessage || 'Please check your CSV and try again.'}</p>
          <button
            onClick={() => setUploadStage('idle')}
            className="mt-4 px-4 py-2 rounded-lg bg-bg-glass border border-border-primary text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            Try Again
          </button>
        </div>
      </motion.div>
    );
  }

  if (uploadStage === 'uploading') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ type: 'spring', stiffness: 200, damping: 24 }}
      >
        <div className="rounded-xl border border-accent-cyan/20 bg-accent-cyan/5 p-8 text-center">
          <Loader2 size={32} className="animate-spin text-accent-cyan mx-auto mb-4" />
          <p className="text-text-primary font-medium">📊 Running EDA Analysis...</p>
          <p className="text-sm text-text-muted mt-2">Analyzing dataset structure, quality, and correlations</p>
        </div>
      </motion.div>
    );
  }

  const selectedPipelineDesc = pipelineOptions.find((o) => o.value === pipeline)?.desc;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ type: 'spring', stiffness: 200, damping: 24 }}
      className="space-y-4"
    >
      {/* Dropzone */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        onClick={() => document.getElementById('file-upload')?.click()}
        className="rounded-xl border-2 border-dashed border-border-secondary bg-bg-card p-8 text-center hover:border-accent-cyan/30 transition-all duration-200 cursor-pointer group"
      >
        <input type="file" accept=".csv" onChange={onFileChange} className="hidden" id="file-upload" />
        <div className="p-4 rounded-xl bg-bg-glass w-fit mx-auto mb-4 group-hover:bg-accent-cyan/10 transition-colors">
          <Upload size={32} className="text-text-muted group-hover:text-accent-cyan transition-colors" />
        </div>
        <p className="text-text-primary font-medium">Drop your CSV here</p>
        <p className="text-sm text-text-muted mt-1">or browse files from your computer</p>
        <p className="text-xs text-text-muted mt-3">Accepts .csv files</p>
      </div>

      {/* Config panel */}
      {selectedFile && (
        <div className="space-y-4 rounded-xl border border-border-primary bg-bg-card p-5">
          {/* File info row */}
          <div className="flex items-center justify-between rounded-lg bg-bg-glass px-3 py-2">
            <div className="flex items-center gap-2 min-w-0">
              <Database size={16} className="text-accent-cyan shrink-0" />
              <span className="text-sm text-text-primary font-medium truncate">{selectedFile.name}</span>
            </div>
            <span className="text-xs text-text-muted shrink-0">{formatSize(selectedFile.size)}</span>
          </div>

          {/* Target input */}
          <div>
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
              Target Column (optional)
            </label>
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="e.g. Survived, price"
              className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50 transition-colors w-full"
            />
            <p className="text-xs text-text-muted mt-1">Leave blank for unsupervised analysis.</p>
          </div>

          {/* Pipeline selector */}
          <div>
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Analysis Pipeline</label>
            <div className="grid grid-cols-3 gap-2">
              {pipelineOptions.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setPipeline(opt.value)}
                  className={`flex flex-col items-center gap-1.5 rounded-lg border p-3 text-xs transition-all duration-200 ${
                    pipeline === opt.value
                      ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan'
                      : 'border-border-primary bg-bg-glass text-text-secondary hover:border-border-secondary'
                  }`}
                >
                  <opt.icon size={20} />
                  <span className="font-medium">{opt.label}</span>
                </button>
              ))}
            </div>
            <p className="text-xs text-text-muted mt-1.5">{selectedPipelineDesc}</p>
          </div>

          {/* Ollama config */}
          {(pipeline === 'single-agent' || pipeline === 'multi-agent') && (
            <div className="space-y-3 rounded-lg border border-border-primary bg-bg-glass/50 p-3">
              <div>
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Ollama Model</label>
                <input
                  type="text"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="llama3.1:8b"
                  className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50 transition-colors w-full"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Ollama Server URL</label>
                <input
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50 transition-colors w-full"
                />
              </div>
              <p className="text-xs text-text-muted">ℹ️ Ollama must be running locally. If unavailable, EDA results will still be returned.</p>
            </div>
          )}

          {/* Analyze button */}
          <button
            onClick={handleAnalyze}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-blue text-white font-semibold hover:opacity-90 transition-opacity"
          >
            Analyze Dataset
            <ArrowRight size={18} />
          </button>
        </div>
      )}
    </motion.div>
  );
}
