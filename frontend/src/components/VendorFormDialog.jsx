import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Field } from '@/components/PageHeader';

const FIELDS = [
  ['name', 'Vendor Name', 'Precision Weld Co.'],
  ['service', 'Process / Service', 'Welding, Painting, Powder Coat…'],
  ['contact_name', 'Contact Person', ''],
  ['phone', 'Phone', ''],
  ['email', 'Email', ''],
  ['address', 'Address', ''],
];
const init = (v) => Object.fromEntries([...FIELDS.map(([k]) => [k, v?.[k] || '']), ['notes', v?.notes || '']]);

export const VendorFormDialog = ({ open, onOpenChange, vendor, onSaved }) => {
  const [form, setForm] = useState(init(vendor));
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) setForm(init(vendor)); }, [open, vendor]);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = vendor ? await api.put(`/vendors/${vendor.id}`, form) : await api.post('/vendors', form);
      toast.success(`${data.name} ${vendor ? 'updated' : 'added'}`);
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
      <DialogContent className="sm:max-w-lg" data-testid="vendor-form-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl uppercase tracking-wide">{vendor ? 'Edit Vendor' : 'New Vendor'}</DialogTitle>
          <DialogDescription>Vendors populate the location dropdown when checking units out.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            {FIELDS.map(([k, label, ph]) => (
              <Field key={k} label={label} className={k === 'address' || k === 'name' ? 'sm:col-span-2' : ''}>
                <Input data-testid={`vendor-${k}-input`} value={form[k]} onChange={set(k)} placeholder={ph} required={k === 'name'} />
              </Field>
            ))}
          </div>
          <Field label="Notes">
            <Textarea data-testid="vendor-notes-input" rows={2} value={form.notes} onChange={set('notes')} />
          </Field>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} data-testid="vendor-form-cancel-button">Cancel</Button>
            <Button type="submit" disabled={busy} data-testid="vendor-form-submit-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              {busy ? 'Saving…' : vendor ? 'Save Changes' : 'Add Vendor'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
