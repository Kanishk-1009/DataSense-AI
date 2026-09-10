import { motion } from 'framer-motion';
import { BarChart3, Brain, GitBranch, Loader2, CheckCircle } from 'lucide-react';
import type { UploadStage } from '../../types/api';

const stageOrder: Array<{ key: UploadStage; label: string }> = [
  { key: 'uploading', label: 'Uploading' },
  { key: 'profiling', label: 'Profiling' },
  { key: 'analyzing', label: 'Analyzing' },
];

function getStageLabel(stage: UploadStage): string {
  switch (stage) {
    case 'uploading': return 'Uploading dataset…';
    case 'profiling': return 'Profiling dataset structure…';
    case 'analyzing': return 'Running analysis pipeline…';
    default: return 'Processing…';
  }
}

function getStageHint(stage: UploadStage): string {
  switch (stage) {
    case 'uploading':
      return 'Uploading your CSV to the backend';
    case 'profiling':
      return 'Reading schema, types, and missing values';
    case 'analyzing':
      return 'Computing EDA, quality score, and correlations';
    default:
      return '';
  }
}

export function ProgressStageBar({ stage }: { stage: 'uploading' | 'profiling' | 'analyzing' | 'success' | 'error' }) {
  const activeIndex = stageOrder.findIndex((s) => s.key === stage);
  const done = stage === 'success' || stage === 'error' ? stageOrder.length : activeIndex;

  return (
    <div className="flex items-center gap-2">
      {stageOrder.map((s, i) => {
        const state = i < done || stage === 'success' ? 'done' : i === activeIndex ? 'active' : 'pending';
        const isLast = i === stageOrder.length - 1;
        return (
          <div key={s.key} className={`flex items-center gap-2 ${isLast ? '' : 'flex-1'}`}>
            <div className="flex items-center gap-2">
              <div
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-300
                  ${
                    state === 'done'
                      ? 'bg-green-500/10 text-green-400 border-green-500/20'
                      : state === 'active'
                        ? 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30 animate-pulse-slow'
                        : 'bg-bg-glass text-text-muted border-border-primary'
                  }
                `}
              >
                {state === 'done' ? (
                  <CheckCircle size={12} />
                ) : state === 'active' ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-current" />
                )}
                {s.label}
              </div>
            </div>
            {!isLast && (
              <div
                className={`h-px flex-1 transition-colors duration-500 ${
                  i < done || stage === 'success' ? 'bg-green-500/40' : 'bg-border-primary'
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

interface UploadProgressProps {
  stage: UploadStage;
  pipeline?: 'eda' | 'single-agent' | 'multi-agent';
  progress?: number;
}

export function UploadProgress({ stage, pipeline, progress = 0 }: UploadProgressProps) {
  const isActive = stage === 'uploading' || stage === 'profiling' || stage === 'analyzing';

  if (stage === 'success') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="rounded-xl border border-green-500/20 bg-green-500/5 p-6 text-center"
      >
        <CheckCircle size={36} className="text-green-400 mx-auto mb-3" />
        <p className="text-text-primary font-medium">Analysis Complete</p>
        <p className="text-sm text-text-muted mt-1">Navigating to dashboard…</p>
      </motion.div>
    );
  }

  if (stage === 'error') {
    return null;
  }

  if (!isActive) return null;

  const stageLabel =
    pipeline === 'single-agent' || pipeline === 'multi-agent'
      ? stage === 'analyzing'
        ? 'AI analysis in progress — this can take 30–120s'
        : getStageLabel(stage)
      : getStageLabel(stage);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-accent-cyan/20 bg-accent-cyan/5 p-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <Loader2 size={20} className="animate-spin text-accent-cyan shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary">{stageLabel}</p>
          <p className="text-xs text-text-muted mt-0.5">{getStageHint(stage)}</p>
        </div>
      </div>

      <ProgressStageBar stage={stage} />

      {progress > 0 && (
        <div className="mt-4 h-1.5 rounded-full bg-bg-glass overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-accent-cyan to-accent-blue"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.4 }}
          />
        </div>
      )}

      <div className="mt-4 flex items-center gap-2 text-xs text-text-muted">
        {pipeline === 'single-agent' && <Brain size={14} className="text-accent-cyan" />}
        {pipeline === 'multi-agent' && <GitBranch size={14} className="text-accent-purple" />}
        {pipeline === 'eda' && <BarChart3 size={14} className="text-text-muted" />}
        {pipeline === 'single-agent' ? '1 LLM call (LangChain baseline)'
          : pipeline === 'multi-agent' ? '7 specialist nodes (LangGraph)'
          : 'Deterministic EDA — no LLM required'}
      </div>
    </motion.div>
  );
}