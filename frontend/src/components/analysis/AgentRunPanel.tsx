import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Brain,
  GitBranch,
  Atom,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Loader2,
  Sparkles,
  Home,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../common/Card';
import { Badge } from '../common/UIComponents';
import { NarrativeCard } from './NarrativeCard';
import { SpecialistGrid } from './SpecialistGrid';
import { useDatasetStore } from '../../store/datasetStore';
import { runSingleAgent, runMultiAgent } from '../../services/analysisApi';
import type { AgentResponse } from '../../types/analysis';

interface AgentRunPanelProps {
  file?: File | null;
}

export function AgentRunPanel({ file }: AgentRunPanelProps) {
  const navigate = useNavigate();
  const {
    agentResult,
    setAgentResult,
    edaResult,
    setEdaResult,
    setUploadStage,
  } = useDatasetStore();
  const [pipeline, setPipeline] = useState<'single-agent' | 'multi-agent'>('single-agent');
  const [model, setModel] = useState('llama3.1:8b');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = useCallback(async () => {
    if (!file) return;
    setRunning(true);
    setError(null);
    setUploadStage('analyzing');
    try {
      const result =
        pipeline === 'single-agent'
          ? await runSingleAgent(file, undefined, model, ollamaUrl)
          : await runMultiAgent(file, undefined, model, ollamaUrl);
      setEdaResult(result.eda);
      setAgentResult(result.agent);
      setUploadStage('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'AI analysis failed');
      setUploadStage('error');
    } finally {
      setRunning(false);
    }
  }, [file, pipeline, model, ollamaUrl, setUploadStage, setEdaResult, setAgentResult]);

  const renderResult = (agent: AgentResponse) => (
    <>
      {agent.status === 'error' && (
        <div className="mb-6 rounded-xl border border-red-500/20 bg-red-500/5 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-red-400 mt-0.5 shrink-0" />
            <div>
              <h3 className="font-semibold text-text-primary mb-1">AI Analysis Failed</h3>
              <p className="text-sm text-text-secondary">{agent.error || 'An unknown error occurred.'}</p>
              <p className="text-xs text-text-muted mt-2">EDA results below are still available.</p>
            </div>
          </div>
        </div>
      )}
      {agent.status === 'success' && (
        <>
          <NarrativeCard agent={agent} />
          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            {agent.key_risks.length > 0 && (
              <Card>
                <CardHeader>
                  <h3 className="font-semibold text-text-primary flex items-center gap-2">
                    <AlertTriangle size={16} className="text-amber-400" />
                    Key Risks
                  </h3>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2.5">
                    {agent.key_risks.map((risk, i) => (
                      <div key={i} className="flex items-start gap-2.5 rounded-lg border border-amber-500/20 bg-amber-500/5 px-3 py-2.5">
                        <AlertTriangle size={15} className="text-amber-400 mt-0.5 shrink-0" />
                        <p className="text-sm text-text-secondary">{risk}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
            {agent.recommendations.length > 0 && (
              <Card>
                <CardHeader>
                  <h3 className="font-semibold text-text-primary flex items-center gap-2">
                    <CheckCircle size={16} className="text-green-400" />
                    Recommendations
                  </h3>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2.5">
                    {agent.recommendations.map((rec, i) => (
                      <div key={i} className="flex items-start gap-2.5 rounded-lg border border-green-500/20 bg-green-500/5 px-3 py-2.5">
                        <CheckCircle size={15} className="text-green-400 mt-0.5 shrink-0" />
                        <p className="text-sm text-text-secondary">{rec}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
          {agent.pipeline === 'multi_agent' && <SpecialistGrid agent={agent} />}
        </>
      )}
    </>
  );

  if (agentResult) {
    return renderResult(agentResult);
  }

  // No agent result yet
  if (file) {
    return (
      <Card className="mb-8">
        <CardContent className="p-6">
          <div className="flex items-start gap-3 mb-4">
            <div className="p-2.5 rounded-xl bg-accent-purple/10 text-accent-purple border border-accent-purple/20">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 className="font-semibold text-text-primary">Run AI Analysis</h3>
              <p className="text-sm text-text-secondary mt-0.5">
                Re-run your uploaded dataset through an LLM pipeline to get AI narrative insights.
              </p>
            </div>
          </div>

          <div className="grid sm:grid-cols-3 gap-3 mb-4">
            {([
              { value: 'single-agent', label: 'Single Agent', icon: Brain, desc: '1 LLM call (LangChain)', accent: 'border-accent-purple/30 bg-accent-purple/10 text-accent-purple' },
              { value: 'multi-agent', label: 'Multi Agent', icon: GitBranch, desc: '7 specialist nodes (LangGraph)', accent: 'border-accent-blue/30 bg-accent-blue/10 text-accent-blue' },
            ] as const).map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setPipeline(opt.value)}
                className={`rounded-xl border p-3 text-left transition-all duration-200 ${
                  pipeline === opt.value
                    ? opt.accent
                    : 'border-border-primary bg-bg-glass text-text-secondary hover:border-border-secondary'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <opt.icon size={16} />
                  <span className="text-xs font-semibold">{opt.label}</span>
                </div>
                <span className="text-[11px] text-text-muted">{opt.desc}</span>
              </button>
            ))}
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 flex items-center gap-2">
              <Atom size={16} className="text-amber-400 shrink-0" />
              <span className="text-xs text-text-secondary">Requires Ollama running locally</span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            <div>
              <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Ollama Model</label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="llama3.1:8b"
                className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50 transition-colors w-full font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-1 block">Ollama Server URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                placeholder="http://localhost:11434"
                className="bg-bg-card border border-border-primary rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-cyan/50 transition-colors w-full font-mono"
              />
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <button
            onClick={handleRun}
            disabled={running}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-accent-purple to-accent-blue text-white font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed w-full"
          >
            {running ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Running AI analysis... (30–120s)
              </>
            ) : (
              <>
                Run AI Analysis
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </CardContent>
      </Card>
    );
  }

  // No file reference available
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 rounded-xl border border-blue-500/20 bg-blue-500/5 p-6"
    >
      <div className="flex items-start gap-3">
        <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 shrink-0">
          <Sparkles size={18} />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-text-primary mb-1">AI Analysis Not Run</h3>
          <p className="text-sm text-text-secondary leading-relaxed">
            To run AI analysis, go back to the Home page and select Single Agent or Multi Agent mode.
          </p>
          <button
            onClick={() => navigate('/')}
            className="mt-3 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-colors text-sm font-medium"
          >
            <Home size={15} />
            Go to Home
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
      {edaResult && (
        <div className="mt-4 pt-3 border-t border-blue-500/10">
          <Badge variant="cyan">EDA results available</Badge>
          <span className="text-xs text-text-muted ml-2">Deterministic insights shown below.</span>
        </div>
      )}
    </motion.div>
  );
}