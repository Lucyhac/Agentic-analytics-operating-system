import type { LucideIcon } from 'lucide-react';

import { formatCompactNumber } from '../utils/format';

interface MetricCardProps {
  label: string;
  value: unknown;
  icon: LucideIcon;
  tone?: 'cyan' | 'mint' | 'amber' | 'coral';
}

const toneClass = {
  cyan: 'bg-cyan/15 text-cyan',
  mint: 'bg-mint/15 text-mint',
  amber: 'bg-amber/15 text-amber',
  coral: 'bg-coral/15 text-coral',
};

export function MetricCard({ label, value, icon: Icon, tone = 'cyan' }: MetricCardProps) {
  return (
    <div className="glass rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
          <p className="mt-2 break-words text-2xl font-semibold text-white">{formatCompactNumber(value)}</p>
        </div>
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${toneClass[tone]}`}>
          <Icon size={20} />
        </div>
      </div>
    </div>
  );
}
