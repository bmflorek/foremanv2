import { cn } from '@/lib/utils';
import { statusMeta } from '@/lib/constants';

export const StatusBadge = ({ list, value, className, testId, size = 'sm' }) => {
  const meta = statusMeta(list, value);
  return (
    <span
      data-testid={testId || `status-badge-${value}`}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-semibold uppercase tracking-wider whitespace-nowrap',
        size === 'sm' ? 'px-2.5 py-0.5 text-[11px]' : 'px-3 py-1 text-sm',
        meta.badge,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', meta.dot)} />
      {meta.label}
    </span>
  );
};
