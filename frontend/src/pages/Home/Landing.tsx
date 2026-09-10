import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  AlertCircle,
  ArrowRight,
  Database,
  Sparkles,
  UploadCloud,
  CheckCircle,
  XCircle,
  Cpu,
} from 'lucide-react';
import { useDatasetStore } from '../../store/datasetStore';
import { getDemoDataset, getDemoDatasetNames } from '../../data/demo';
import { uploadDataset } from '../../services/datasetApi';
import { runEDA, runSingleAgent, runMultiAgent } from '../../services/analysisApi';
import { FileDropzone } from '../../components/upload/FileDropzone';
import { UploadProgress } from '../../components/upload/UploadProgress';
import { PipelineSelector, type PipelineMode } from '../../components/upload/PipelineSelector';
import type { UploadStage } from '../../types/api';

const features = [
  { icon: Database, title: 'Schema Analysis', desc: 'Understand column types, missing values, and data structure.', gradient: 'from-accent-cyan/20 to-accent-blue/20 border-accent-cyan/20' },
  { icon: Cpu, title: 'Data Quality', desc: 'Get quality scores, detect outliers, and identify issues.', gradient: 'from-accent-green/20 to-accent-cyan/20 border-accent-green/20' },
  { icon: Sparkles, title: 'AI Insights', desc: 'Receive intelligent analysis and recommendations.', gradient: 'from-accent-purple/20 to-accent-blue/20 border-accent-purple/20' },
  { icon: AlertCircle, title: 'ML Readiness', desc: 'Assess your dataset for machine learning readiness.', gradient: 'from-accent-amber/20 to-accent-purple/20 border-accent-amber/20' },
];

const stats = [
  { value: '5+', label: 'Demo Datasets' },
  { value: '50+', label: 'Quality Checks' },
  { value: 'AI', label: 'Powered Insights' },
  { value: '100%', label: 'Open Source' },
];

const stepDefs = [
  { step: 1, title: 'Upload', desc: 'Drag & drop a CSV file' },
  { step: 2, title: 'Configure', desc: 'Target, pipeline, model' },
  { step: 3, title: 'Analyze', desc: 'One click — full EDA' },
];

function HeroTerminal() {
  const rows = [
    { label: 'rows', value: '1,289,032', color: 'text-text-primary' },
    { label: 'columns', value: '24', color: 'text-text-primary' },
    { label: 'quality_score', value: '87 / 100', color: 'text-green-400' },
    { label: 'ml_task', value: 'binary_classification', color: 'text-accent-purple' },
    { label: 'missing_pct', value: '3.2%', color: 'text-amber-400' },
    { label: 'correlation', value: '+0.84 (fare ↔ class)', color: 'text-accent-cyan' },
    { label: 'recommended_model', value: 'Gradient Boosting', color: 'text-green-400' },
  ];
  return (
    <div className="relative h-[350px] lg:h-[450px]">
      <div className="absolute inset-0 rounded-2xl border border-border-primary bg-bg-card/60 backdrop-blur-sm overflow-hidden shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-br from-accent-cyan/5 to-accent-purple/5" />
        {/* Terminal chrome */}
        <div className="absolute top-0 left-0 right-0 flex items-center gap-2 px-4 py-3 border-b border-border-primary bg-bg-glass">
          <span className="w-3 h-3 rounded-full bg-red-500/70" />
          <span className="w-3 h-3 rounded-full bg-amber-500/70" />
          <span className="w-3 h-3 rounded-full bg-green-500/70" />
          <span className="ml-3 text-xs font-mono text-text-muted">datasense-eda --csv dataset.csv</span>
        </div>
        {/* Terminal body */}
        <div className="absolute inset-x-4 top-14 bottom-4 flex flex-col gap-2.5 overflow-hidden font-mono text-xs">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-accent-cyan"
          >
            <span className="text-green-400">$</span> profiling dataset...
          </motion.div>
          {rows.map((r, i) => (
            <motion.div
              key={r.label}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 + i * 0.12 }}
              className="flex items-center gap-3"
            >
              <span className="w-32 text-text-muted truncate shrink-0">
                {r.label}
                <span className="text-text-muted">:</span>
              </span>
              <span className={`${r.color} truncate`}>{r.value}</span>
              {i === rows.length - 1 && (
                <span className="inline-block w-1.5 h-3.5 bg-accent-cyan animate-pulse-slow ml-1" />
              )}
            </motion.div>
          ))}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 + rows.length * 0.12 + 0.2 }}
            className="text-green-400"
          >
            ✓ EDA complete — quality checks passed
          </motion.div>
        </div>
        {/* Floating accent */}
        <div className="absolute -bottom-6 -right-6 w-40 h-40 rounded-full bg-accent-cyan/10 blur-3xl animate-float" />
      </div>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { setProfile, setEdaResult, setFileName, setAgentResult, setUploadStage } = useDatasetStore();

  const handleLoadDemo = useCallback(
    (name: string) => {
      const demo = getDemoDataset(name);
      if (!demo) return;
      setAgentResult(null);
      setProfile(demo.analysis.profile);
      setEdaResult(demo.analysis.eda);
      setFileName(demo.name);
      setUploadStage('success');
      navigate('/dashboard');
    },
    [navigate, setProfile, setEdaResult, setFileName, setAgentResult, setUploadStage],
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

        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28">
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
            >
              <HeroTerminal />
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
                whileHover={{ y: -4 }}
                className={`rounded-xl border bg-gradient-to-br ${f.gradient} p-6 backdrop-blur-sm hover:shadow-lg transition-all duration-300`}
              >
                <div className="p-3 rounded-lg bg-bg-card w-fit mb-4">
                  <f.icon size={22} className="text-accent-cyan" />
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
              Upload your CSV or explore one of our demo datasets. Choose a pipeline, then dive into the results.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* Upload area */}
            <UploadFlow />

            {/* Demo datasets */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="rounded-xl border border-border-primary bg-bg-card p-6"
            >
              <h3 className="font-semibold text-text-primary mb-4">Demo Datasets</h3>
              <p className="text-sm text-text-secondary mb-4">
                No file needed — explore with pre-baked EDA results.
              </p>
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

function UploadFlow() {
  const navigate = useNavigate();
  const {
    setProfile,
    setEdaResult,
    setFileName,
    setUploadStage,
    setAgentResult,
    setUploadProgress,
    uploadStage,
  } = useDatasetStore();

  const [file, setFile] = useState<File | null>(null);
  const [target, setTarget] = useState('');
  const [pipeline, setPipeline] = useState<PipelineMode>('eda');
  const [model, setModel] = useState('llama3.1:8b');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const progressTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (progressTimer.current) window.clearInterval(progressTimer.current);
    };
  }, []);

  const startProgress = useCallback(
    (from: number, to: number, duration = 1800) => {
      if (progressTimer.current) window.clearInterval(progressTimer.current);
      setUploadProgress(from);
      const start = Date.now();
      progressTimer.current = window.setInterval(() => {
        const elapsed = Date.now() - start;
        const ratio = Math.min(1, elapsed / duration);
        const value = from + (to - from) * (0.9 * ratio);
        setUploadProgress(Math.round(value));
        if (ratio >= 1 && progressTimer.current) {
          window.clearInterval(progressTimer.current);
          progressTimer.current = null;
        }
      }, 80);
    },
    [setUploadProgress],
  );

  const handleAnalyze = useCallback(async () => {
    if (!file) return;
    setErrorMessage(null);

    const runAgentStage = (stage: UploadStage) => {
      setUploadStage(stage);
      if (stage === 'uploading') startProgress(0, 30, 1200);
      if (stage === 'profiling') startProgress(30, 55, 1500);
      if (stage === 'analyzing') startProgress(55, 95, 20000);
    };

    runAgentStage('uploading');
    try {
      const profile = await uploadDataset(file);
      setProfile(profile);
      runAgentStage('profiling');

      if (pipeline === 'eda') {
        const eda = await runEDA(file, target || undefined);
        setEdaResult(eda);
        setAgentResult(null);
      } else if (pipeline === 'single-agent') {
        runAgentStage('analyzing');
        const result = await runSingleAgent(file, target || undefined, model, ollamaUrl);
        setEdaResult(result.eda);
        setAgentResult(result.agent);
      } else if (pipeline === 'multi-agent') {
        runAgentStage('analyzing');
        const result = await runMultiAgent(file, target || undefined, model, ollamaUrl);
        setEdaResult(result.eda);
        setAgentResult(result.agent);
      }

      setFileName(file.name);
      setUploadProgress(100);
      setUploadStage('success');
      navigate('/dashboard');
    } catch (err) {
      setUploadStage('error');
      setErrorMessage(err instanceof Error ? err.message : 'Analysis failed');
    }
  }, [
    file,
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
    setUploadProgress,
    startProgress,
  ]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ type: 'spring', stiffness: 200, damping: 24 }}
      className="rounded-xl border border-border-primary bg-bg-card overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-border-primary flex items-center justify-between">
        <h3 className="font-semibold text-text-primary flex items-center gap-2">
          <UploadCloud size={16} className="text-accent-cyan" />
          Analyze Your Dataset
        </h3>
        {uploadStage === 'success' && (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-green-400">
            <CheckCircle size={14} />
            Done
          </span>
        )}
        {uploadStage === 'error' && (
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-400">
            <XCircle size={14} />
            Failed
          </span>
        )}
      </div>

      <div className="p-5">
        {/* Step indicator */}
        <div className="flex items-center gap-2 mb-5">
          {stepDefs.map((s, i) => (
            <div key={s.step} className={`flex items-center gap-2 ${i < stepDefs.length - 1 ? 'flex-1' : ''}`}>
              <div
                className={`flex items-center gap-2 rounded-lg px-3 py-1.5 border text-xs font-medium transition-all duration-300 ${
                  (uploadStage === 'idle' || uploadStage === 'error') && i === 0
                    ? 'border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan'
                    : 'border-border-primary bg-bg-glass text-text-muted'
                }`}
              >
                <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  i === 0 && (uploadStage === 'idle' || uploadStage === 'error') ? 'bg-accent-cyan text-bg-primary' : 'bg-bg-card text-text-muted'
                }`}>
                  {s.step}
                </span>
                <span className="hidden sm:inline">{s.title}</span>
              </div>
              {i < stepDefs.length - 1 && <div className="h-px flex-1 bg-border-primary" />}
            </div>
          ))}
        </div>

        {uploadStage === 'success' ? (
          <UploadProgress stage="success" pipeline={pipeline} />
        ) : uploadStage === 'analyzing' || uploadStage === 'profiling' || uploadStage === 'uploading' ? (
          <span className="block">
            <UploadProgress stage={uploadStage} pipeline={pipeline} />
          </span>
        ) : uploadStage === 'error' ? (
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6 text-center">
            <AlertCircle size={36} className="text-red-400 mx-auto mb-3" />
            <p className="text-text-primary font-medium">Analysis Failed</p>
            <p className="text-sm text-text-secondary mt-1 mb-4">{errorMessage || 'Please check your CSV and try again.'}</p>
            <button
              onClick={() => setUploadStage('idle')}
              className="px-4 py-2 rounded-lg bg-bg-glass border border-border-primary text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Step 1: Upload */}
            <FileDropzone
              file={file}
              onFileChange={(f) => {
                setFile(f);
                setErrorMessage(null);
              }}
            />

            {/* Step 2: Configure */}
            {file && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <PipelineSelector
                  pipeline={pipeline}
                  onPipelineChange={setPipeline}
                  target={target}
                  onTargetChange={setTarget}
                  model={model}
                  onModelChange={setModel}
                  ollamaUrl={ollamaUrl}
                  onOllamaUrlChange={setOllamaUrl}
                />
              </motion.div>
            )}

            {/* Step 3: Analyze */}
            {file && (
              <button
                onClick={handleAnalyze}
                className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-accent-cyan to-accent-blue text-white font-semibold hover:opacity-90 transition-opacity group"
              >
                Analyze Dataset
                <ArrowRight size={18} className="transition-transform group-hover:translate-x-0.5" />
              </button>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}