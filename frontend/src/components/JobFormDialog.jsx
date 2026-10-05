import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';
import { JOB_STATUSES, SPEC_FIELDS, EMPTY_SPECS } from '@/lib/constants';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Field } from '@/components/PageHeader';
import { SelectField } from '@/components/FormControls';

const init = (job) => ({
  job_number: job?.job_number || '',
  name: job?.name || '',
  customer: job?.customer || '',
  address: job?.address || '',
  sold_amount: job?.sold_amount ?? '',
  status: job?.status || 'active',
  due_date: job?.due_date || '',
  notes: job?.notes || '',
  specs: { ...EMPTY_SPECS, ...(job?.specs || {}) },
});

export const JobFormDialog = ({ open, onOpenChange, job, onSaved }) => {
  const [form, setForm] = useState(init(job));
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) setForm(init(job)); }, [open, job]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const setSpec = (k) => (e) => setForm({ ...form, specs: { ...form.specs, [k]: e.target.value } });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = { ...form, sold_amount: Number(form.sold_amount) || 0, due_date: form.due_date || null };
      const { data } = job ? await api.put(`/jobs/${job.id}`, payload) : await api.post('/jobs', payload);
      toast.success(job ? `Job ${data.job_number} updated` : `Job ${data.job_number} created`);
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
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-3xl" data-testid="job-form-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl uppercase tracking-wide">{job ? `Edit Job ${job.job_number}` : 'New Job'}</DialogTitle>
          <DialogDescription>Job number is 2-digit year + 3-digit sequence (e.g. 26207).</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Job #">
              <Input data-testid="job-number-input" value={form.job_number} onChange={set('job_number')} placeholder="26207" required pattern="\d{5}" maxLength={5} className="font-mono text-lg font-bold tracking-widest" />
            </Field>
            <Field label="Job Name" className="sm:col-span-2">
              <Input data-testid="job-name-input" value={form.name} onChange={set('name')} placeholder="Hillcrest Residence" required />
            </Field>
            <Field label="Customer">
              <Input data-testid="job-customer-input" value={form.customer} onChange={set('customer')} />
            </Field>
            <Field label="Address" className="sm:col-span-2">
              <Input data-testid="job-address-input" value={form.address} onChange={set('address')} />
            </Field>
            <Field label="Sold Amount ($)">
              <Input data-testid="job-sold-amount-input" type="number" min="0" step="0.01" value={form.sold_amount} onChange={set('sold_amount')} className="font-mono" />
            </Field>
            <Field label="Status">
              <SelectField testId="job-status-select" value={form.status} onChange={(v) => setForm({ ...form, status: v })} options={JOB_STATUSES} />
            </Field>
            <Field label="Due Date">
              <Input data-testid="job-due-date-input" type="date" value={form.due_date} onChange={set('due_date')} />
            </Field>
          </div>

          <div>
            <p className="mb-3 font-mono text-xs uppercase tracking-[0.2em] text-amber-500">Spec Sheet</p>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {SPEC_FIELDS.map((f) => (
                <Field key={f.key} label={f.label}>
                  <Input data-testid={`spec-${f.key}-input`} value={form.specs[f.key]} onChange={setSpec(f.key)} />
                </Field>
              ))}
            </div>
            <Field label="Additional (custom / one-off notes)" className="mt-4">
              <Textarea data-testid="spec-additional-notes-input" rows={3} value={form.specs.additional_notes} onChange={setSpec('additional_notes')} />
            </Field>
          </div>

          <Field label="Internal Notes">
            <Textarea data-testid="job-notes-input" rows={2} value={form.notes} onChange={set('notes')} />
          </Field>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} data-testid="job-form-cancel-button">Cancel</Button>
            <Button type="submit" disabled={busy} data-testid="job-form-submit-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              {busy ? 'Saving…' : job ? 'Save Changes' : 'Create Job'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
