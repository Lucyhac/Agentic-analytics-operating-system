import { FormEvent, useState } from 'react';
import { Bot, Loader2, Send, Sparkles, WandSparkles, Wrench } from 'lucide-react';
import { motion } from 'framer-motion';

import type { AgentResponse } from '../types/dataset';

interface AgentConsoleProps {
  disabled: boolean;
  isRunning: boolean;
  lastResponse: AgentResponse | null;
  onSubmit: (message: string) => Promise<void>;
}

const examples = [
  'Remove duplicate records',
  'Replace missing values with average',
  'Show top 10 by revenue',
  'Create revenue by city bar chart',
  'Find correlations between columns',
];

export function AgentConsole({ disabled, isRunning, lastResponse, onSubmit }: AgentConsoleProps) {
  const [message, setMessage] = useState('');
  const [activeExample, setActiveExample] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || disabled || isRunning) return;
    setMessage('');
    await onSubmit(trimmed);
  };

  const handleExample = async (example: string) => {
    if (disabled || isRunning) return;
    setActiveExample(example);
    setMessage(example);
    try {
      await onSubmit(example);
      setMessage('');
    } finally {
      setActiveExample(null);
    }
  };

  return (
    <section className="glass aurora-panel rounded-lg p-5">
      <div className="relative">
      <div className="mb-5 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-lg bg-mint/15 text-mint shadow-glow">
            <Bot size={22} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Autonomous Data Agent</h2>
            <p className="text-sm text-slate-400">Classifies intent, plans tools, executes safely, refreshes dashboard state.</p>
          </div>
        </div>
        {lastResponse && (
          <span className="rounded-lg border border-cyan/25 bg-cyan/10 px-3 py-2 text-xs uppercase tracking-wide text-cyan">
            {lastResponse.intent}
          </span>
        )}
      </div>

      <form className="flex flex-col gap-3 md:flex-row" onSubmit={handleSubmit}>
        <input
          className="min-h-12 flex-1 rounded-lg border border-line bg-ink/80 px-4 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan focus:shadow-glow"
          disabled={disabled || isRunning}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask the agent to clean, analyze, modify, or visualize your dataset..."
          value={message}
        />
        <button
          className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-mint px-5 text-sm font-semibold text-ink shadow-glow transition hover:bg-mint/90 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled || isRunning || !message.trim()}
          type="submit"
        >
          {isRunning ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
          Run Agent
        </button>
      </form>

      <div className="mt-4 flex flex-wrap gap-2">
        {examples.map((example) => (
          <button
            className="inline-flex items-center gap-2 rounded-lg border border-line bg-white/[0.05] px-3 py-2 text-xs text-slate-300 transition hover:border-cyan/50 hover:bg-cyan/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            disabled={disabled || isRunning}
            key={example}
            onClick={() => handleExample(example)}
            type="button"
          >
            {activeExample === example ? <Loader2 className="animate-spin" size={13} /> : <WandSparkles size={13} />}
            {example}
          </button>
        ))}
      </div>

      {lastResponse && (
        <motion.div animate={{ opacity: 1, y: 0 }} className="mt-5 space-y-4" initial={{ opacity: 0, y: 10 }}>
          <div className="rounded-lg border border-line bg-white/[0.03] p-4">
            <div className="mb-2 flex items-center gap-2 text-mint">
              <Sparkles size={16} />
              <span className="text-sm font-medium">Agent response</span>
            </div>
            <p className="text-sm leading-6 text-slate-200">{lastResponse.response}</p>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            {lastResponse.actions.map((action, index) => (
              <div className="rounded-lg border border-line bg-ink/50 p-3" key={`${action.action}-${index}`}>
                <div className="mb-2 flex items-center gap-2 text-cyan">
                  <Wrench size={15} />
                  <span className="text-xs font-medium uppercase tracking-wide">{action.action}</span>
                </div>
                <p className="text-xs leading-5 text-slate-400">
                  {[action.column, action.group_by, action.operation, action.chart_type].filter(Boolean).join(' | ') ||
                    'Safe structured tool action'}
                </p>
              </div>
            ))}
          </div>
        </motion.div>
      )}
      </div>
    </section>
  );
}
