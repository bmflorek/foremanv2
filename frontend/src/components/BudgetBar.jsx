import { cn } from '@/lib/utils';
import { money } from '@/lib/constants';
import { AlertTriangle } from 'lucide-react';

export const BudgetBar = ({ budget, compact = false }) => {
  if (!budget) return null;
  const pct = Math.min(budget.percent_used || 0, 100);
  const tone = budget.over_budget ? 'over' : pct >= 80 ? 'warn' : 'ok';
  const bar = { ok: 'bg-emerald-500', warn: 'bg-amber-500', over: 'bg-red-500' }[tone];
  const text = { ok: 'text-emerald-400', warn: 'text-amber-400', over: 'text-red-400' }[tone];

  return (
    <div data-testid="budget-bar" className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">
          Spent <span className="font-mono text-slate-200 tabular">{money(budget.po_total)}</span>
          <span className="text-slate-500"> / {money(budget.sold_amount)}</span>
        </span>
        <span className={cn('font-mono font-semibold tabular flex items-center gap-1', text)} data-testid="budget-remaining">
          {budget.over_budget && <AlertTriangle size={12} />}
          {budget.over_budget ? `${money(Math.abs(budget.remaining))} over` : `${money(budget.remaining)} left`}
        </span>
      </div>
      <div className={cn('w-full overflow-hidden rounded-full bg-slate-700/60', compact ? 'h-1.5' : 'h-2.5')}>
        <div className={cn('h-full rounded-full transition-[width] duration-700', bar)} style={{ width: `${budget.sold_amount > 0 ? pct : 0}%` }} />
      </div>
    </div>
  );
};
