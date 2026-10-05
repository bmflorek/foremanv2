import { ArrowUpRight, ArrowDownLeft, History } from 'lucide-react';
import { fmtDateTime } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { EmptyState } from '@/components/PageHeader';

export const MovementLog = ({ movements, showJob = false, testId = 'movement-log' }) => {
  if (!movements) return <p className="text-sm text-slate-500">Loading…</p>;
  if (movements.length === 0) {
    return <EmptyState icon={History} title="No movements yet" hint="Check-outs and check-ins will appear here." testId={`${testId}-empty`} />;
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700/80 bg-slate-800/50">
      <Table data-testid={testId}>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-20">Dir</TableHead>
            {showJob && <TableHead>Job</TableHead>}
            <TableHead>Unit</TableHead><TableHead>Vendor</TableHead><TableHead>Process</TableHead>
            <TableHead>Notes</TableHead><TableHead>By</TableHead><TableHead className="text-right">When</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {movements.map((m) => (
            <TableRow key={m.id} data-testid={`movement-row-${m.id}`}>
              <TableCell>
                <span className={cn('inline-flex items-center gap-1 rounded px-2 py-0.5 font-mono text-[11px] font-bold uppercase', m.direction === 'out' ? 'bg-amber-500/15 text-amber-400' : 'bg-emerald-500/15 text-emerald-400')}>
                  {m.direction === 'out' ? <ArrowUpRight size={12} /> : <ArrowDownLeft size={12} />}{m.direction}
                </span>
              </TableCell>
              {showJob && <TableCell className="font-mono text-slate-300">{m.job_number}</TableCell>}
              <TableCell className="font-mono font-bold text-slate-50">{m.unit_number}</TableCell>
              <TableCell className="text-slate-200">{m.vendor_name || '—'}</TableCell>
              <TableCell className="text-slate-300">{m.process || '—'}</TableCell>
              <TableCell className="max-w-[240px] truncate text-slate-400" title={m.notes}>{m.notes || '—'}</TableCell>
              <TableCell className="text-slate-400">{m.user_name}</TableCell>
              <TableCell className="whitespace-nowrap text-right font-mono text-xs text-slate-400">{fmtDateTime(m.created_at)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};
