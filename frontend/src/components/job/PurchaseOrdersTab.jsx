import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, Receipt, AlertTriangle } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { PO_STATUSES, money, fmtDate } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { EmptyState } from '@/components/PageHeader';
import { SelectField, ConfirmDelete } from '@/components/FormControls';
import { POFormDialog } from '@/components/POFormDialog';

const Tile = ({ label, value, tone = 'text-slate-50', testId }) => (
  <div className="rounded-lg border border-slate-700/80 bg-slate-800/50 px-5 py-4" data-testid={testId}>
    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
    <p className={cn('mt-1 font-mono text-2xl font-bold tabular', tone)}>{value}</p>
  </div>
);

export const PurchaseOrdersTab = ({ job, vendors, onChanged }) => {
  const [data, setData] = useState(null);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);

  const load = useCallback(() => api.get(`/jobs/${job.id}/purchase-orders`).then((r) => setData(r.data)).catch((e) => toast.error(errMsg(e))), [job.id]);
  useEffect(() => { load(); }, [load]);
  const refresh = () => { load(); onChanged?.(); };

  const changeStatus = async (po, status) => {
    try { await api.put(`/purchase-orders/${po.id}`, { status }); refresh(); } catch (e) { toast.error(errMsg(e)); }
  };
  const remove = async (po) => {
    try { await api.delete(`/purchase-orders/${po.id}`); toast.success(`${po.po_number} deleted`); refresh(); } catch (e) { toast.error(errMsg(e)); }
  };

  const budget = data?.budget;
  const pos = data?.purchase_orders || [];

  return (
    <div className="space-y-5">
      {budget && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Tile label="Sold Amount" value={money(budget.sold_amount)} testId="budget-sold" />
          <Tile label={`PO Spend (${budget.po_count})`} value={money(budget.po_total)} tone="text-blue-400" testId="budget-spent" />
          <Tile label={budget.over_budget ? 'Over Budget' : 'Remaining Budget'} value={money(Math.abs(budget.remaining))} tone={budget.over_budget ? 'text-red-400' : budget.percent_used >= 80 ? 'text-amber-400' : 'text-emerald-400'} testId="budget-remaining-tile" />
        </div>
      )}
      {budget?.over_budget && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/50 bg-red-500/10 px-4 py-3 text-sm text-red-300" data-testid="over-budget-alert">
          <AlertTriangle size={18} /> Purchase orders exceed the sold amount by <span className="font-mono font-bold">{money(Math.abs(budget.remaining))}</span>.
        </div>
      )}

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">PO numbers auto-generate as <span className="font-mono text-slate-300">{job.job_number}-PO-NN</span></p>
        <Button size="sm" onClick={() => { setEditing(null); setOpen(true); }} data-testid="create-po-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
          <Plus size={15} className="mr-1" /> New PO
        </Button>
      </div>

      {data && pos.length === 0 ? (
        <EmptyState icon={Receipt} title="No purchase orders" hint="Create a PO for supplies; its total deducts from the sold amount." testId="po-empty-state" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-700/80 bg-slate-800/50">
          <Table data-testid="po-table">
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>PO #</TableHead><TableHead>Date</TableHead><TableHead>Vendor</TableHead>
                <TableHead>Items</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Total</TableHead><TableHead className="w-24" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {pos.map((po) => (
                <TableRow key={po.id} data-testid={`po-row-${po.po_number}`} className={po.status === 'cancelled' ? 'opacity-50' : ''}>
                  <TableCell className="font-mono font-bold text-amber-400">{po.po_number}</TableCell>
                  <TableCell className="text-slate-300">{fmtDate(po.date)}</TableCell>
                  <TableCell className="text-slate-200">{po.vendor_name || <span className="text-slate-600">—</span>}</TableCell>
                  <TableCell className="max-w-[280px] truncate text-slate-400" title={po.line_items.map((l) => l.description).join(', ')}>
                    {po.line_items.length} · {po.line_items.map((l) => l.description).filter(Boolean).join(', ') || '—'}
                  </TableCell>
                  <TableCell><SelectField testId={`po-status-${po.po_number}`} value={po.status} onChange={(v) => changeStatus(po, v)} options={PO_STATUSES} className="h-8 w-36 text-xs" /></TableCell>
                  <TableCell className="text-right font-mono text-base font-semibold tabular">{money(po.total)}</TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <button onClick={() => { setEditing(po); setOpen(true); }} data-testid={`edit-po-${po.po_number}`} className="rounded p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-100"><Pencil size={14} /></button>
                      <ConfirmDelete testId={`delete-po-${po.po_number}`} title={`Delete ${po.po_number}?`} description="Its total will be returned to the remaining budget." onConfirm={() => remove(po)}
                        trigger={<button data-testid={`delete-po-${po.po_number}`} className="rounded p-1.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400"><Trash2 size={14} /></button>} />
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <POFormDialog open={open} onOpenChange={setOpen} jobId={job.id} po={editing} vendors={vendors} onSaved={refresh} />
    </div>
  );
};
