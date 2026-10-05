import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, AlertOctagon, CheckCircle2, RotateCcw } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { ISSUE_SEVERITIES, ISSUE_STATUSES, fmtDateTime } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { EmptyState } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { ConfirmDelete } from '@/components/FormControls';
import { IssueFormDialog } from '@/components/IssueFormDialog';

const IssueCard = ({ issue, onEdit, onDelete, onToggle, index }) => {
  const [resolution, setResolution] = useState('');
  const open = issue.status === 'open';
  return (
    <div data-testid={`issue-card-${issue.id}`} style={{ animationDelay: `${index * 30}ms` }}
      className={cn('animate-rise rounded-lg border-l-4 bg-slate-800/70 p-4', open ? (issue.severity === 'high' ? 'border-red-500' : 'border-amber-500') : 'border-emerald-500 opacity-80')}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className={cn('text-xl font-bold uppercase tracking-wide', !open && 'line-through text-slate-400')} data-testid={`issue-title-${issue.id}`}>{issue.title}</h3>
            <StatusBadge list={ISSUE_SEVERITIES} value={issue.severity} testId={`issue-severity-${issue.id}`} />
            <StatusBadge list={ISSUE_STATUSES} value={issue.status} testId={`issue-status-${issue.id}`} />
            {issue.unit_number && <span className="rounded bg-slate-900/70 px-2 py-0.5 font-mono text-xs font-bold text-amber-400">{issue.unit_number}</span>}
          </div>
          {issue.description && <p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{issue.description}</p>}
          <p className="mt-2 font-mono text-xs text-slate-500">
            Logged by {issue.created_by_name} · {fmtDateTime(issue.created_at)}
            {!open && ` · Resolved by ${issue.resolved_by_name} · ${fmtDateTime(issue.resolved_at)}`}
          </p>
          {!open && issue.resolution && <p className="mt-1 text-sm text-emerald-300/90"><span className="font-semibold">Fix:</span> {issue.resolution}</p>}
        </div>
        <div className="flex gap-1">
          <button onClick={onEdit} data-testid={`edit-issue-${issue.id}`} className="rounded p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-100"><Pencil size={14} /></button>
          <ConfirmDelete testId={`delete-issue-${issue.id}`} title="Delete this issue?" description="This cannot be undone." onConfirm={onDelete}
            trigger={<button data-testid={`delete-issue-${issue.id}`} className="rounded p-1.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400"><Trash2 size={14} /></button>} />
        </div>
      </div>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
        {open && <Input data-testid={`issue-resolution-input-${issue.id}`} value={resolution} onChange={(e) => setResolution(e.target.value)} placeholder="How was it fixed? (optional)" className="h-9 sm:max-w-md" />}
        <Button size="sm" variant="outline" onClick={() => onToggle(open ? { status: 'resolved', resolution } : { status: 'open' })} data-testid={`toggle-issue-${issue.id}`}
          className={open ? 'border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300' : 'text-slate-300'}>
          {open ? <><CheckCircle2 size={15} className="mr-1" /> Mark Resolved</> : <><RotateCcw size={15} className="mr-1" /> Reopen</>}
        </Button>
      </div>
    </div>
  );
};

export const IssuesTab = ({ job, onChanged }) => {
  const [issues, setIssues] = useState(null);
  const [units, setUnits] = useState([]);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState('open');

  const load = useCallback(() => api.get(`/jobs/${job.id}/issues`).then((r) => setIssues(r.data)).catch((e) => toast.error(errMsg(e))), [job.id]);
  useEffect(() => { load(); api.get(`/jobs/${job.id}/units`).then((r) => setUnits(r.data)); }, [load, job.id]);
  const refresh = () => { load(); onChanged?.(); };

  const toggle = async (issue, body) => {
    try { await api.patch(`/issues/${issue.id}`, body); toast.success(body.status === 'resolved' ? 'Issue resolved' : 'Issue reopened'); refresh(); } catch (e) { toast.error(errMsg(e)); }
  };
  const remove = async (issue) => {
    try { await api.delete(`/issues/${issue.id}`); toast.success('Issue deleted'); refresh(); } catch (e) { toast.error(errMsg(e)); }
  };

  const list = (issues || []).filter((i) => filter === 'all' || i.status === filter);
  const openCount = (issues || []).filter((i) => i.status === 'open').length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-1 rounded-md bg-slate-800/60 p-1" data-testid="issues-filter">
          {[['open', `Open (${openCount})`], ['resolved', `Resolved (${(issues || []).length - openCount})`], ['all', 'All']].map(([v, l]) => (
            <button key={v} onClick={() => setFilter(v)} data-testid={`issues-filter-${v}`} className={cn('rounded px-3 py-1.5 text-sm font-semibold transition-colors', filter === v ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-slate-100')}>{l}</button>
          ))}
        </div>
        <Button size="sm" onClick={() => { setEditing(null); setOpen(true); }} data-testid="add-issue-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
          <Plus size={15} className="mr-1" /> Log Issue
        </Button>
      </div>

      {issues && list.length === 0 ? (
        <EmptyState icon={AlertOctagon} title={filter === 'open' ? 'No open issues' : 'No issues'} hint="Log problems the crew hits so nothing gets lost." testId="issues-empty-state" />
      ) : (
        <div className="space-y-3" data-testid="issues-list">
          {list.map((i, idx) => <IssueCard key={i.id} issue={i} index={idx} onEdit={() => { setEditing(i); setOpen(true); }} onDelete={() => remove(i)} onToggle={(body) => toggle(i, body)} />)}
        </div>
      )}

      <IssueFormDialog open={open} onOpenChange={setOpen} jobId={job.id} issue={editing} units={units} onSaved={refresh} />
    </div>
  );
};
