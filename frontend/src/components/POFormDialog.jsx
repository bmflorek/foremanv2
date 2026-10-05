import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Plus, Trash2 } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { PO_STATUSES, money } from '@/lib/constants';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Field } from '@/components/PageHeader';
import { SelectField } from '@/components/FormControls';

let lineSeq = 0;
const blankLine = () => ({ key: `line-${++lineSeq}`, description: '', qty: 1, unit_cost: '' });
const withKeys = (items) => (items?.length ? items.map((li) => ({ ...li, key: `line-${++lineSeq}` })) : [blankLine()]);

const init = (po) => ({
  vendor_id: po?.vendor_id || 'none',
  date: po?.date || new Date().toISOString().slice(0, 10),
  status: po?.status || 'ordered',
  notes: po?.notes || '',
  line_items: withKeys(po?.line_items),
});

const lineTotal = (items) => items.reduce((s, li) => s + (Number(li.qty) || 0) * (Number(li.unit_cost) || 0), 0);

const toPayload = (form) => ({
  vendor_id: form.vendor_id === 'none' ? null : form.vendor_id,
  date: form.date,
  status: form.status,
  notes: form.notes,
  line_items: form.line_items
    .filter((li) => li.description || li.unit_cost)
    .map((li) => ({ description: li.description, qty: Number(li.qty) || 0, unit_cost: Number(li.unit_cost) || 0 })),
});

const LineItemsEditor = ({ items, onChange }) => {
  const setLine = (key, field, value) => onChange(items.map((li) => (li.key === key ? { ...li, [field]: value } : li)));
  const removeLine = (key) => onChange(items.filter((li) => li.key !== key));
  return (
    <div>
      <div className="mb-2 grid grid-cols-[1fr_70px_110px_32px] gap-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        <span>Description</span><span>Qty</span><span>Unit Cost</span><span />
      </div>
      <div className="space-y-2">
        {items.map((li, i) => (
          <div key={li.key} className="grid grid-cols-[1fr_70px_110px_32px] gap-2" data-testid={`po-line-item-${i}`}>
            <Input data-testid={`po-line-description-${i}`} value={li.description} onChange={(e) => setLine(li.key, 'description', e.target.value)} placeholder="Aluminum extrusion 6063" />
            <Input data-testid={`po-line-qty-${i}`} type="number" min="0" step="any" value={li.qty} onChange={(e) => setLine(li.key, 'qty', e.target.value)} className="font-mono" />
            <Input data-testid={`po-line-cost-${i}`} type="number" min="0" step="0.01" value={li.unit_cost} onChange={(e) => setLine(li.key, 'unit_cost', e.target.value)} className="font-mono" placeholder="0.00" />
            <button type="button" onClick={() => removeLine(li.key)} data-testid={`po-line-remove-${i}`} className="grid place-items-center rounded text-slate-500 hover:bg-red-500/10 hover:text-red-400" disabled={items.length === 1}>
              <Trash2 size={15} />
            </button>
          </div>
        ))}
      </div>
      <div className="mt-3 flex items-center justify-between">
        <Button type="button" size="sm" variant="outline" onClick={() => onChange([...items, blankLine()])} data-testid="po-add-line-item-button">
          <Plus size={14} className="mr-1" /> Add line
        </Button>
        <p className="text-sm text-slate-400">
          Total <span className="ml-2 font-mono text-xl font-bold text-slate-50 tabular" data-testid="po-form-total">{money(lineTotal(items))}</span>
        </p>
      </div>
    </div>
  );
};

export const POFormDialog = ({ open, onOpenChange, jobId, po, vendors, onSaved }) => {
  const [form, setForm] = useState(init(po));
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) setForm(init(po)); }, [open, po]);

  const vendorOptions = [{ value: 'none', label: 'No vendor / misc supplier' }, ...vendors.map((v) => ({ value: v.id, label: `${v.name}${v.service ? ` · ${v.service}` : ''}` }))];

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = toPayload(form);
      const { data } = po ? await api.put(`/purchase-orders/${po.id}`, payload) : await api.post(`/jobs/${jobId}/purchase-orders`, payload);
      toast.success(`${data.po_number} ${po ? 'updated' : 'created'} · ${money(data.total)}`);
      if (data.budget?.over_budget) toast.warning(`Job is now ${money(Math.abs(data.budget.remaining))} over budget`);
      onSaved?.(data);
      onOpenChange(false);
    } catch (err) {
      toast.error(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl" data-testid="po-form-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl uppercase tracking-wide">{po ? `Edit ${po.po_number}` : 'New Purchase Order'}</DialogTitle>
          <DialogDescription>PO number is auto-generated. Totals deduct from the job's sold amount.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Vendor / Supplier" className="sm:col-span-2">
              <SelectField testId="po-vendor-select" value={form.vendor_id} onChange={(v) => setForm({ ...form, vendor_id: v })} options={vendorOptions} />
            </Field>
            <Field label="Date">
              <Input data-testid="po-date-input" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            </Field>
          </div>

          <LineItemsEditor items={form.line_items} onChange={(line_items) => setForm({ ...form, line_items })} />

          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Status">
              <SelectField testId="po-status-select" value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={PO_STATUSES} />
            </Field>
            <Field label="Notes" className="sm:col-span-2">
              <Textarea data-testid="po-notes-input" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </Field>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} data-testid="po-form-cancel-button">Cancel</Button>
            <Button type="submit" disabled={busy} data-testid="po-form-submit-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              {busy ? 'Saving…' : po ? 'Save Changes' : 'Create PO'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
