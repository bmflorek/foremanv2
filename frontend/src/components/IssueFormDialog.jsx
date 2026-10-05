import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';
import { ISSUE_SEVERITIES } from '@/lib/constants';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Field } from '@/components/PageHeader';
import { SelectField } from '@/components/FormControls';

const init = (issue) => ({
  title: issue?.title || '',
  description: issue?.description || '',
  severity: issue?.severity || 'medium',
  unit_id: issue?.unit_id || 'none',
});

export const IssueFormDialog = ({ open, onOpenChange, jobId, issue, units, onSaved }) => {
  const [form, setForm] = useState(init(issue));
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) setForm(init(issue)); }, [open, issue]);

  const unitOptions = [{ value: 'none', label: 'Whole job / not unit-specific' }, ...units.map((u) => ({ value: u.id, label: `${u.unit_number}${u.description ? ` · ${u.description}` : ''}` }))];

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = { ...form, unit_id: form.unit_id === 'none' ? null : form.unit_id };
      const { data } = issue ? await api.patch(`/issues/${issue.id}`, payload) : await api.post(`/jobs/${jobId}/issues`, payload);
      toast.success(issue ? 'Issue updated' : 'Issue logged');
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
      <DialogContent className="sm:max-w-lg" data-testid="issue-form-dialog">
        <DialogHeader>
          <DialogTitle className="font-display text-2xl uppercase tracking-wide">{issue ? 'Edit Issue' : 'Log Issue'}</DialogTitle>
          <DialogDescription>Record a problem the crew ran into on this job.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <Field label="Title">
            <Input data-testid="issue-title-input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Glass arrived cracked" required />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Severity">
              <SelectField testId="issue-severity-select" value={form.severity} onChange={(v) => setForm({ ...form, severity: v })} options={ISSUE_SEVERITIES} />
            </Field>
            <Field label="Related Unit">
              <SelectField testId="issue-unit-select" value={form.unit_id} onChange={(v) => setForm({ ...form, unit_id: v })} options={unitOptions} />
            </Field>
          </div>
          <Field label="Details">
            <Textarea data-testid="issue-description-input" rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </Field>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)} data-testid="issue-form-cancel-button">Cancel</Button>
            <Button type="submit" disabled={busy} data-testid="issue-form-submit-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
              {busy ? 'Saving…' : issue ? 'Save Changes' : 'Log Issue'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
