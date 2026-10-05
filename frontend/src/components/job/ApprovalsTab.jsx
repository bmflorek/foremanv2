import { useState } from 'react';
import { toast } from 'sonner';
import { CheckCircle2, Circle, Undo2 } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { APPROVAL_TYPES, fmtDate } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Field } from '@/components/PageHeader';

const ApprovalCard = ({ type, approval, onSave, index }) => {
  const [form, setForm] = useState({ approved_by: approval.approved_by || '', approved_at: approval.approved_at || new Date().toISOString().slice(0, 10), notes: approval.notes || '' });
  const [busy, setBusy] = useState(false);
  const done = approval.approved;

  const save = async (approved) => {
    setBusy(true);
    try { await onSave(type.key, { ...form, approved }); } finally { setBusy(false); }
  };

  return (
    <div data-testid={`approval-card-${type.key}`} style={{ animationDelay: `${index * 50}ms` }}
      className={cn('animate-rise flex flex-col gap-4 rounded-lg border p-5', done ? 'border-emerald-500/50 bg-emerald-500/5' : 'border-slate-700/80 bg-slate-800/60')}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-2xl font-bold uppercase tracking-wide">{type.label}</h3>
          <p className="text-sm text-slate-400">{type.hint}</p>
        </div>
        {done ? <CheckCircle2 className="shrink-0 text-emerald-400" size={28} data-testid={`approval-check-${type.key}`} /> : <Circle className="shrink-0 text-slate-600" size={28} />}
      </div>

      {done ? (
        <div className="space-y-1 text-sm" data-testid={`approval-signed-${type.key}`}>
          <p className="text-emerald-300">Approved by <span className="font-semibold">{approval.approved_by}</span> on <span className="font-mono">{fmtDate(approval.approved_at)}</span></p>
          {approval.notes && <p className="text-slate-300">{approval.notes}</p>}
          <Button size="sm" variant="ghost" disabled={busy} onClick={() => save(false)} data-testid={`revoke-approval-${type.key}`} className="mt-2 text-slate-400 hover:text-red-400">
            <Undo2 size={14} className="mr-1" /> Revoke
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Approved by">
              <Input data-testid={`approval-by-input-${type.key}`} value={form.approved_by} onChange={(e) => setForm({ ...form, approved_by: e.target.value })} placeholder="Customer name" />
            </Field>
            <Field label="Date">
              <Input data-testid={`approval-date-input-${type.key}`} type="date" value={form.approved_at} onChange={(e) => setForm({ ...form, approved_at: e.target.value })} />
            </Field>
          </div>
          <Field label="Notes">
            <Textarea data-testid={`approval-notes-input-${type.key}`} rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Rev C drawings, emailed 6/12" />
          </Field>
          <Button disabled={busy || !form.approved_by} onClick={() => save(true)} data-testid={`approve-button-${type.key}`} className="w-full bg-emerald-600 font-semibold text-white hover:bg-emerald-500">
            <CheckCircle2 size={16} className="mr-1.5" /> Mark Approved
          </Button>
        </div>
      )}
    </div>
  );
};

export const ApprovalsTab = ({ job, onChanged }) => {
  const save = async (key, body) => {
    try {
      await api.put(`/jobs/${job.id}/approvals/${key}`, body);
      toast.success(body.approved ? `${APPROVAL_TYPES.find((t) => t.key === key).label} approved` : 'Approval revoked');
      onChanged?.();
    } catch (e) {
      toast.error(errMsg(e));
    }
  };
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400" data-testid="approvals-progress">
        <span className="font-mono text-lg font-bold text-slate-50">{job.approvals_done}/{job.approvals_total}</span> customer sign-offs collected
      </p>
      <div className="grid gap-4 lg:grid-cols-3">
        {APPROVAL_TYPES.map((t, i) => <ApprovalCard key={`${t.key}-${job.approvals[t.key]?.approved}`} type={t} approval={job.approvals[t.key] || {}} onSave={save} index={i} />)}
      </div>
    </div>
  );
};
