import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, Boxes, Truck } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { UNIT_STATUSES } from '@/lib/constants';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { EmptyState } from '@/components/PageHeader';
import { SelectField, ConfirmDelete } from '@/components/FormControls';
import { UnitFormDialog } from '@/components/UnitFormDialog';

const Dash = () => <span className="text-slate-600">—</span>;

const UnitRow = ({ unit: u, onStatus, onEdit, onDelete }) => (
  <TableRow data-testid={`unit-row-${u.unit_number}`}>
    <TableCell className="font-mono text-lg font-bold text-amber-400">{u.unit_number}</TableCell>
    <TableCell className="capitalize text-slate-300">{u.unit_type}</TableCell>
    <TableCell className="max-w-[260px] truncate text-slate-200" title={u.description}>{u.description || <Dash />}</TableCell>
    <TableCell className="font-mono text-slate-300">{u.width || u.height ? `${u.width || '?'} × ${u.height || '?'}` : <Dash />}</TableCell>
    <TableCell className="text-right font-mono">{u.qty}</TableCell>
    <TableCell className="text-slate-300">{u.location || <Dash />}</TableCell>
    <TableCell>
      <div className="flex flex-col gap-1">
        <SelectField testId={`unit-status-${u.unit_number}`} value={u.status} onChange={onStatus} options={UNIT_STATUSES} className="h-8 w-44 text-xs" disabled={!!u.current_vendor_id} />
        {u.current_vendor_id && (
          <span className="flex items-center gap-1 text-[11px] text-amber-400" data-testid={`unit-vendor-${u.unit_number}`}><Truck size={11} /> at {u.current_vendor_name}</span>
        )}
      </div>
    </TableCell>
    <TableCell>
      <div className="flex justify-end gap-1">
        <button onClick={onEdit} data-testid={`edit-unit-${u.unit_number}`} className="rounded p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-100"><Pencil size={14} /></button>
        <ConfirmDelete testId={`delete-unit-${u.unit_number}`} title={`Delete unit ${u.unit_number}?`} description="This removes the unit and its movement history." onConfirm={onDelete}
          trigger={<button data-testid={`delete-unit-${u.unit_number}`} className="rounded p-1.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400"><Trash2 size={14} /></button>} />
      </div>
    </TableCell>
  </TableRow>
);

export const UnitsTab = ({ job, onChanged }) => {
  const [units, setUnits] = useState(null);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);

  const load = useCallback(() => api.get(`/jobs/${job.id}/units`).then((r) => setUnits(r.data)).catch((e) => toast.error(errMsg(e))), [job.id]);
  useEffect(() => { load(); }, [load]);
  const refresh = () => { load(); onChanged?.(); };

  const run = async (fn, successMsg) => {
    try { await fn(); if (successMsg) toast.success(successMsg); refresh(); } catch (e) { toast.error(errMsg(e)); }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400" data-testid="units-count">{units ? `${units.length} unit${units.length === 1 ? '' : 's'}` : 'Loading…'}</p>
        <Button size="sm" onClick={() => { setEditing(null); setOpen(true); }} data-testid="add-unit-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
          <Plus size={15} className="mr-1" /> Add Unit
        </Button>
      </div>

      {units && units.length === 0 ? (
        <EmptyState icon={Boxes} title="No units on this job" hint="Add windows (W1), doors (D1), bifolds (BF1) and sliders (SL1)." testId="units-empty-state" />
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-700/80 bg-slate-800/50">
          <Table data-testid="units-table">
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Unit</TableHead><TableHead>Type</TableHead><TableHead>Description</TableHead>
                <TableHead>W × H</TableHead><TableHead className="text-right">Qty</TableHead><TableHead>Location</TableHead>
                <TableHead>Status</TableHead><TableHead className="w-24" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(units || []).map((u) => (
                <UnitRow key={u.id} unit={u}
                  onStatus={(status) => run(() => api.patch(`/units/${u.id}`, { status }))}
                  onEdit={() => { setEditing(u); setOpen(true); }}
                  onDelete={() => run(() => api.delete(`/units/${u.id}`), `Unit ${u.unit_number} deleted`)} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <UnitFormDialog open={open} onOpenChange={setOpen} jobId={job.id} unit={editing} onSaved={refresh} />
    </div>
  );
};
