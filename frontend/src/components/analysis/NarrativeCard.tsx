import { Brain } from 'lucide-react';
import { BarChart3, GitBranch, Zap } from 'lucide-react';
import { Card, CardHeader, CardContent } from '../common/Card';
import { Badge } from '../common/UIComponents';
import type { AgentResponse } from '../../types/analysis';

function confidenceColor(pct: number | null): string {
  if (pct === null) return 'bg-text-muted';
  if (pct > 70) return 'bg-green-400';
  if (pct > 40) return 'bg-amber-400';
  return 'bg-red-400';
}

export function NarrativeCard({ agent }: { agent: AgentResponse }) {
  const isMulti = agent.pipeline === 'multi_agent';
  const confidencePct = agent.confidence != null ? Math.round(agent.confidence * 100) : null;
  const llmCallCount = (agent.extra?.llm_call_count ?? (isMulti ? 7 : 1)) as number;

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-semibold text-text-primary flex items-center gap-2">
            <Brain size={16} className="text-accent-cyan" />
            AI Narrative Analysis
          </h3>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={isMulti ? 'purple' : 'cyan'}>{isMulti ? 'Multi Agent' : 'Single Agent'}</Badge>
            <span className="flex items-center gap-1 text-xs text-text-secondary">
              <BarChart3 size={12} />
              {isMulti ? '7 nodes' : '1 call'}
            </span>
            <span className="flex items-center gap-1 text-xs text-text-secondary">
              <Zap size={12} className="text-amber-400" />
              {llmCallCount} LLM call{llmCallCount === 1 ? '' : 's'}
            </span>
            {isMulti && <GitBranch size={14} className="text-accent-purple" />}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {agent.narrative ? (
          agent.narrative
            .split(/\n\n+/)
            .filter((p) => p.trim())
            .map((p, i) => (
              <p key={i} className="leading-relaxed text-text-secondary mb-3 last:mb-0">
                {p}
              </p>
            ))
        ) : (
          <p className="text-sm text-text-muted">No narrative was generated for this analysis.</p>
        )}

        {confidencePct !== null && (
          <div className="mt-5 pt-4 border-t border-border-primary">
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-text-muted uppercase tracking-wider">Model confidence</span>
              <div className="h-2 flex-1 rounded-full bg-bg-glass overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${confidenceColor(confidencePct)}`}
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
              <span className="text-sm font-semibold text-text-primary">{confidencePct}%</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}