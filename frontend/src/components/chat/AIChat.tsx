import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Copy, Trash2, Sparkles, Bot } from 'lucide-react';
import { useDatasetStore } from '../../store/datasetStore';
import { useDataset } from '../../hooks/useDataset';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const SUGGESTED_PROMPTS = [
  'Which columns have missing values?',
  'Which features are most correlated?',
  'Are there any outliers?',
  'Which column could be my target?',
  'Is this dataset ready for machine learning?',
  'Should I remove the outliers?',
];

function generateDemoResponse(message: string, eda: ReturnType<typeof useDataset>['edaResult']): string {
  if (!eda) return 'No dataset loaded. Please upload a dataset first.';

  const lower = message.toLowerCase();

  if (lower.includes('missing')) {
    const summary = eda.missingness?.summary;
    if (summary && summary.total_missing_cells > 0) {
      const cols = Object.entries<{ missing_count: number; missing_percentage: number }>(eda.missingness.columns)
        .filter(([, v]) => v.missing_count > 0)
        .map(([k, v]) => `${k} (${v.missing_percentage}%)`)
        .join(', ');
      return `Found ${summary.total_missing_cells} missing cells across ${summary.columns_with_missing} column(s): ${cols}. Consider imputation strategies based on the missingness pattern.`;
    }
    return 'Great news! This dataset has no missing values detected.';
  }

  if (lower.includes('correlat')) {
    const pairs = eda.correlation_analysis?.highly_correlated_pairs || [];
    if (pairs.length > 0) {
      const top = pairs.slice(0, 3).map((p: { column_a: string; column_b: string; correlation: number }) => `${p.column_a} ↔ ${p.column_b} (${p.correlation})`).join('\n');
      return `Found ${pairs.length} highly correlated pair(s):\n${top}\n\nConsider removing redundant features or using dimensionality reduction.`;
    }
    return 'No highly correlated feature pairs were detected in this dataset.';
  }

  if (lower.includes('outlier')) {
    const outlierCols = Object.entries<{ count: number; percentage: number }>(eda.outliers || {}).filter(([, v]) => v.count > 0);
    if (outlierCols.length > 0) {
      const list = outlierCols.slice(0, 5).map(([k, v]) => `${k}: ${v.count} outliers (${v.percentage}%)`).join('\n');
      return `Outliers detected in ${outlierCols.length} column(s):\n${list}\n\nUse IQR or Z-score methods to decide whether to cap, transform, or remove these.`;
    }
    return 'No statistical outliers were detected in the numeric columns.';
  }

  if (lower.includes('target')) {
    const task = eda.ml_task;
    if (task?.target) {
      return `Based on analysis, "${task.target}" appears to be a suitable target variable.\nTask type: ${task.task_type}\nConfidence: ${(task.confidence * 100).toFixed(0)}%`;
    }
    return 'No target column has been specified yet. You can set a target column when uploading your dataset.';
  }

  if (lower.includes('machine learning') || lower.includes('ml') || lower.includes('ready')) {
    const score = eda.quality_score;
    return `ML Readiness Assessment:\nQuality Score: ${score.score}/100 (${score.grade})\n\nRecommendations:\n${score.recommendations.map((r: string) => `• ${r}`).join('\n')}`;
  }

  if (lower.includes('outlier') && lower.includes('remove')) {
    return 'Whether to remove outliers depends on context:\n• If they represent data errors, remove them\n• If they represent rare but valid cases, keep them\n• Consider transformations (log, sqrt) as alternatives\n• Use domain knowledge to guide decisions';
  }

  const insights = eda.insights?.insights || [];
  if (insights.length > 0) {
    return `Here are some key insights about your dataset:\n\n${insights.slice(0, 4).map((insight: string) => `• ${insight}`).join('\n')}`;
  }

  return `I can help you analyze your dataset. Try asking about:\n• Missing values\n• Correlations\n• Outliers\n• Target variables\n• ML readiness`;
}

export default function AIChat() {
  const { isChatOpen, setChatOpen, chatMessages, addChatMessage, clearChat } = useDatasetStore();
  const { edaResult, fileName } = useDataset();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  useEffect(() => {
    if (isChatOpen) inputRef.current?.focus();
  }, [isChatOpen]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim()) return;

      const userMsg: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: text.trim(),
        timestamp: Date.now(),
      };
      addChatMessage(userMsg);
      setInput('');
      setIsTyping(true);

      setTimeout(() => {
        const response = generateDemoResponse(text, edaResult);
        const assistantMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response,
          timestamp: Date.now(),
        };
        addChatMessage(assistantMsg);
        setIsTyping(false);
      }, 800 + Math.random() * 600);
    },
    [addChatMessage, edaResult],
  );

  const copyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content);
  }, []);

  return (
    <>
      {/* Floating button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        onClick={() => setChatOpen(!isChatOpen)}
        className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-gradient-to-r from-accent-cyan to-accent-blue text-white shadow-lg hover:opacity-90 transition-opacity"
        aria-label="Toggle AI Chat"
      >
        {isChatOpen ? <X size={22} /> : <MessageCircle size={22} />}
      </motion.button>

      {/* Chat panel */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-24 right-6 z-50 w-[380px] max-w-[calc(100vw-3rem)] h-[500px] max-h-[calc(100vh-8rem)] rounded-2xl border border-border-primary bg-bg-secondary shadow-2xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-border-primary bg-bg-card/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-accent-cyan/10">
                  <Sparkles size={16} className="text-accent-cyan" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">DataSense AI</h3>
                  {fileName && <p className="text-xs text-text-muted">{fileName}</p>}
                </div>
              </div>
              <button
                onClick={clearChat}
                className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-glass transition-colors"
                title="Clear chat"
              >
                <Trash2 size={14} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.length === 0 && (
                <div className="text-center py-8">
                  <div className="p-3 rounded-xl bg-bg-glass w-fit mx-auto mb-3">
                    <Bot size={24} className="text-accent-cyan" />
                  </div>
                  <p className="text-sm text-text-secondary mb-4">Ask me anything about your dataset</p>
                  <div className="space-y-2">
                    {SUGGESTED_PROMPTS.map((prompt) => (
                      <button
                        key={prompt}
                        onClick={() => sendMessage(prompt)}
                        className="block w-full text-left p-2.5 rounded-lg border border-border-primary bg-bg-glass text-xs text-text-secondary hover:text-text-primary hover:border-border-secondary transition-colors"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {chatMessages.map((msg: ChatMessage) => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm ${
                      msg.role === 'user'
                        ? 'bg-accent-cyan/10 text-text-primary border border-accent-cyan/20'
                        : 'bg-bg-glass text-text-secondary border border-border-primary'
                    }`}
                  >
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    {msg.role === 'assistant' && (
                      <button
                        onClick={() => copyMessage(msg.content)}
                        className="mt-2 flex items-center gap-1 text-xs text-text-muted hover:text-text-secondary transition-colors"
                      >
                        <Copy size={12} />
                        Copy
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="rounded-xl px-4 py-3 bg-bg-glass border border-border-primary">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 rounded-full bg-accent-cyan animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 rounded-full bg-accent-cyan animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 rounded-full bg-accent-cyan animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 border-t border-border-primary bg-bg-card/50">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage(input);
                }}
                className="flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask about your dataset..."
                  className="flex-1 px-3 py-2 rounded-lg bg-bg-glass border border-border-primary text-sm text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                />
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="p-2 rounded-lg bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 hover:bg-accent-cyan/20 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
