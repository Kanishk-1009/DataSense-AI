import { motion } from 'framer-motion';
import { BarChart3, Brain, GitBranch, HelpCircle, Server } from 'lucide-react';

export type PipelineMode = 'eda' | 'single-agent' | 'multi-agent';

const pipelineOptions: Array<{
  value: PipelineMode;
  label: string;
  icon: typeof BarChart3;
  accent: string;
  badge: string;
  desc: string;
  llmCalls: string;
}> = [
  {
    value: 'eda',
    label: 'EDA Only',
    icon: BarChart3,
    accent: 'text-accent-cyan border-accent-cyan/30 bg-accent-cyan/10',
    badge: 'border-accent-cyan/20 text-accent-cyan',
    desc: 'Deterministic analysis only. No LLM required.',
    llmCalls: '0 LLM calls',
  },
  {
    value: 'single-agent',
    label: 'Single Agent',
    icon: Brain,
    accent: 'text-accent-purple border-accent-purple/30 bg-accent-purple/10',
    badge: 'border-accent-purple/20 text-accent-purple',
    desc: 'EDA + 1 LangChain LLM narrative.',
    llmCalls: '1 LLM call',
  },
  {
    value: 'multi-agent',
    label: 'Multi Agent',
    icon: GitBranch,
    accent: 'text-accent-blue border-accent-blue/30 bg-accent-blue/10',
    badge: 'border-accent-blue/30 text-accent-blue',
    desc: 'EDA + 7 specialist LangGraph nodes.',
    llmCalls: '7 LLM calls',
  },
];

function Field({
  label,
  value,
  onChange,
  placeholder,
  hint,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  hint?: string;
}) {
  return (
    <div>
      <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors w-full font-mono"
      />
      {hint && <p className="text-xs text-text-muted mt-1">{hint}</p>}
    </div>
  );
}

interface PipelineSelectorProps {
  pipeline: PipelineMode;
  onPipelineChange: (p: PipelineMode) => void;
  target: string;
  onTargetChange: (t: string) => void;
  model: string;
  onModelChange: (m: string) => void;
  ollamaUrl: string;
  onOllamaUrlChange: (u: string) => void;
}

export function PipelineSelector({
  pipeline,
  onPipelineChange,
  target,
  onTargetChange,
  model,
  onModelChange,
  ollamaUrl,
  onOllamaUrlChange,
}: PipelineSelectorProps) {
  const selected = pipelineOptions.find((o) => o.value === pipeline);

  return (
    <div className="space-y-4">
      {/* Target */}
      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">
          Target Column{' '}
          <span className="inline-flex items-center gap-0.5 normal-case font-normal text-text-muted">
            <HelpCircle size={12} />
            <span className="underline decoration-dotted underline-offset-2" title="Optional target column for supervised analysis. Leave blank for unsupervised.">
              optional
            </span>
          </span>
        </label>
        <input
          type="text"
          value={target}
          onChange={(e) => onTargetChange(e.target.value)}
          placeholder="e.g. Survived, price"
          className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors w-full"
        />
        <p className="text-xs text-text-muted mt-1">Leave blank for unsupervised analysis.</p>
      </div>

      {/* Pipeline */}
      <div>
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Analysis Pipeline</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {pipelineOptions.map((opt) => (
            <motion.button
              key={opt.value}
              type="button"
              whileHover={{ y: -2 }}
              onClick={() => onPipelineChange(opt.value)}
              className={`flex flex-col items-start gap-2 rounded-xl border p-3 text-left transition-all duration-200 ${
                pipeline === opt.value
                  ? `${opt.accent} shadow-lg`
                  : 'border-border-primary bg-bg-glass text-text-secondary hover:border-border-secondary hover:bg-bg-glass-hover'
              }`}
            >
              <div className="flex items-center gap-2 w-full">
                <opt.icon size={18} className={pipeline === opt.value ? 'text-current' : 'text-text-muted'} />
                <span className={`text-xs font-semibold ${pipeline === opt.value ? 'text-current' : ''}`}>{opt.label}</span>
              </div>
              <span className={`text-[11px] rounded-full border px-2 py-0.5 ${pipeline === opt.value ? opt.badge : 'border-border-primary text-text-muted'}`}>
                {opt.llmCalls}
              </span>
            </motion.button>
          ))}
        </div>
        <p className="text-xs text-text-muted mt-1.5">{selected?.desc}</p>
      </div>

      {/* Ollama config for agent pipelines */}
      {(pipeline === 'single-agent' || pipeline === 'multi-agent') && (
        <div className="space-y-3 rounded-lg border border-border-primary bg-bg-glass/50 p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-text-secondary">
            <Server size={14} className="text-accent-cyan" />
            Ollama Configuration
          </div>
          <Field
            label="Ollama Model"
            value={model}
            onChange={onModelChange}
            placeholder="llama3.1:8b"
          />
          <Field
            label="Ollama Server URL"
            value={ollamaUrl}
            onChange={onOllamaUrlChange}
            placeholder="http://localhost:11434"
          />
          <p className="text-xs text-text-muted">
            Ollama must be running locally. If unavailable, EDA results are still returned.
          </p>
        </div>
      )}
    </div>
  );
}