import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';
import { UNIT_STATUSES, UNIT_TYPES, unitTypeFromNumber } from '@/lib/constants';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Field } from '@/components/PageHeader';
import { SelectField } from '@/components/FormControls';

const init = (unit) => ({
  unit_number: unit?.unit_number || '',
  unit_type: unit?.unit_type || 'window',
  description: unit?.description || '',
  width: unit?.width || '',
  height: unit?.height || '',
  qty: unit?.qty ?? 1,
  location: unit?.location || '',
  status: unit?.status || 'not_started',
  notes: unit?.notes || '',
});

const TYPE_OPTIONS = UNIT_TYPES.map((t) => ({ value: t, label: t[0].toUpperCase() + t.slice(1) }));

export const UnitFormDialog = ({ open, onOpenChange, jobId, unit, onSaved }) => {
  const [form, setForm] = useState(init(unit));
  const [typeTouched, setTypeTouched] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) { setForm(init(unit)); setTypeTouched(!!unit); } }, [open, unit]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const setNumber = (e) => {
    const v = e.target.value;
    setForm({ ...form, unit_number: v, unit_type: typeTouched ? form.unit_type : unitTypeFromNumber(v) });
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = { ...form, qty: Number(form.qty) || 1 };
      const { data } = unit ? await api.patch(`/units/${unit.id}`, payload) : await api.post(`/jobs/${jobId}/units`, payload);
      toast.success(`Unit ${data.unit_number} ${unit ? 'updated' : 'added'}`);
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
      <DialogContent className="sm:max-w-xl" data-testid="unit-form-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl uppercase tracking-wide">{unit ? `Edit Unit ${unit.unit_number}` : 'Add Unit'}</DialogTitle>
          <DialogDescription>W = window, D = door, BF = bifold, SL = slider. Add a letter for handing (W1a / W1b).</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Unit #">
              <Input data-testid="unit-number-input" value={form.unit_number} onChange={setNumber} placeholder="W1" required className="font-mono text-lg font-bold uppercase" />
            </Field>
            <Field label="Type">
              <SelectField testId="unit-type-select" value={form.unit_type} onChange={(v) => { setTypeTouched(true); setForm({ ...form, unit_type: v }); }} options={TYPE_OPTIONS} />
            </Field>
            <Field label="Qty">
              <Input data-testid="unit-qty-input" type="number" min="1" value={form.qty} onChange={set('qty')} className="font-mono" />
            </Field>
            <Field label="Description" className="sm:col-span-3">
              <Input data-testid="unit-description-input" value={form.description} onChange={set('description')} placeholder="Casement window, LH" />
            </Field>
            <Field label="Width">
              <Input data-testid="unit-width-input" value={form.width} onChange={set('width')} placeholder={'36"'} className="font-mono" />
            </Field>
            <Field label="Height">
              <Input data-testid="unit-height-input" value={form.height} onChange={set('height')} placeholder={'60"'} className="font-mono" />
            </Field>
            <Field label="Location on Job">
              <Input data-testid="unit-location-input" value={form.location} onChange={set('location')} placeholder="Living Room" />
            </Field>
            {!unit && (
              <Field label="Starting Status" className="sm:col-span-3">
                <SelectField testId="unit-status-select" value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={UNIT_STATUSES.filter((s) => s.value !== 'out_for_process')} />
              </Field>
            )}
          </div>
          <Field label="Notes">
            <Textarea data-testid="unit-notes-input" rows={2} value={form.notes} onChange={set('notes')} />
          </Field>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} data-testid="unit-form-cancel-button">Cancel</Button>
            <Button type="submit" disabled={busy} data-testid="unit-form-submit-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              {busy ? 'Saving…' : unit ? 'Save Changes' : 'Add Unit'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
