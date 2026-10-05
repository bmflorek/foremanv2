import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Briefcase, CalendarDays, AlertOctagon, CheckCircle2, Mail } from 'lucide-react';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';
import { JOB_STATUSES, UNIT_STATUSES, money, fmtDate } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader, EmptyState } from '@/components/PageHeader';
import { StatusBadge } from '@/components/StatusBadge';
import { BudgetBar } from '@/components/BudgetBar';
import { SelectField } from '@/components/FormControls';
import { JobFormDialog } from '@/components/JobFormDialog';
import { DigestSettingsDialog } from '@/components/DigestSettingsDialog';

const JobCard = ({ job, index }) => (
  <Link
    to={`/dashboard/jobs/${job.id}`}
    data-testid={`job-card-${job.job_number}`}
    style={{ animationDelay: `${index * 40}ms` }}
    className="group animate-rise flex flex-col gap-4 rounded-lg border border-slate-700/80 bg-slate-800/70 p-5 transition-[transform,border-color,box-shadow] duration-200 hover:-translate-y-0.5 hover:border-amber-500/60 hover:shadow-lg hover:shadow-amber-500/5"
  >
    <div className="flex items-start justify-between gap-3">
      <div>
        <p className="font-mono text-3xl font-bold tracking-wider text-amber-400">{job.job_number}</p>
        <p className="mt-1 font-display text-xl font-semibold uppercase leading-tight tracking-wide text-slate-50">{job.name}</p>
        {job.customer && <p className="text-sm text-slate-400">{job.customer}</p>}
      </div>
      <StatusBadge list={JOB_STATUSES} value={job.status} testId={`job-status-${job.job_number}`} />
    </div>
    <BudgetBar budget={job.budget} compact />
    <div className="flex items-center gap-2 text-xs">
      {job.open_issues > 0 && (
        <span className="flex items-center gap-1 rounded bg-red-500/15 px-2 py-0.5 font-mono font-bold text-red-400" data-testid={`job-open-issues-${job.job_number}`}>
          <AlertOctagon size={12} /> {job.open_issues} open issue{job.open_issues === 1 ? '' : 's'}
        </span>
      )}
      <span className={cn('flex items-center gap-1 rounded px-2 py-0.5 font-mono font-semibold', job.approvals_done === job.approvals_total ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-700/70 text-slate-300')} data-testid={`job-approvals-${job.job_number}`}>
        <CheckCircle2 size={12} /> {job.approvals_done}/{job.approvals_total} approved
      </span>
    </div>
    <div className="flex items-center justify-between gap-2 text-xs text-slate-400">
      <div className="flex flex-wrap items-center gap-1.5" data-testid={`job-unit-counts-${job.job_number}`}>
        <span className="rounded bg-slate-700/70 px-2 py-0.5 font-mono font-semibold text-slate-200">{job.unit_counts.total} units</span>
        {UNIT_STATUSES.filter((s) => job.unit_counts[s.value] > 0).map((s) => (
          <span key={s.value} className="flex items-center gap-1 rounded px-1.5 py-0.5 font-mono" title={s.label}>
            <span className={cn('h-1.5 w-1.5 rounded-full', s.dot)} />{job.unit_counts[s.value]}
          </span>
        ))}
      </div>
      {job.due_date && <span className="flex items-center gap-1 whitespace-nowrap"><CalendarDays size={12} />{fmtDate(job.due_date)}</span>}
    </div>
  </Link>
);

const Stat = ({ label, value, testId }) => (
  <div className="rounded-lg border border-slate-700/80 bg-slate-800/50 px-5 py-4" data-testid={testId}>
    <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
    <p className="mt-1 font-mono text-2xl font-bold text-slate-50 tabular">{value}</p>
  </div>
);

export default function JobsPage() {
  const [jobs, setJobs] = useState(null);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('all');
  const [open, setOpen] = useState(false);
  const [digestOpen, setDigestOpen] = useState(false);

  const load = useCallback(() => api.get('/jobs').then((r) => setJobs(r.data)).catch((e) => toast.error(errMsg(e))), []);
  useEffect(() => { load(); }, [load]);

  const list = (jobs || []).filter((j) => {
    const text = `${j.job_number} ${j.name} ${j.customer}`.toLowerCase();
    return (status === 'all' || j.status === status) && text.includes(q.toLowerCase());
  });
  const active = (jobs || []).filter((j) => j.status === 'active');
  const sum = (key) => active.reduce((s, j) => s + (j.unit_counts[key] || 0), 0);

  return (
    <div>
      <PageHeader eyebrow="Projects" title="Jobs" subtitle="Every job, its spec sheet, units and budget.">
        <Button variant="outline" onClick={() => setDigestOpen(true)} data-testid="digest-settings-button">
          <Mail size={16} className="mr-1.5" /> Morning Digest
        </Button>
        <Button onClick={() => setOpen(true)} data-testid="create-job-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
          <Plus size={16} className="mr-1.5" /> New Job
        </Button>
      </PageHeader>

      <div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Active Jobs" value={active.length} testId="stat-active-jobs" />
        <Stat label="Units In Fab" value={sum('in_fab')} testId="stat-units-in-fab" />
        <Stat label="Units Out" value={sum('out_for_process')} testId="stat-units-out" />
        <Stat label="Active Sold Value" value={money(active.reduce((s, j) => s + (j.sold_amount || 0), 0))} testId="stat-sold-value" />
      </div>

      <div className="mb-6 flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <Input data-testid="jobs-search-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search job #, name, customer…" className="pl-9" />
        </div>
        <SelectField testId="jobs-status-filter" value={status} onChange={setStatus} className="sm:w-48" options={[{ value: 'all', label: 'All statuses' }, ...JOB_STATUSES]} />
      </div>

      {jobs && list.length === 0 ? (
        <EmptyState icon={Briefcase} title="No jobs yet" hint="Create your first job to start tracking units, POs and in/out movements." testId="jobs-empty-state" />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4" data-testid="jobs-grid">
          {list.map((j, i) => <JobCard key={j.id} job={j} index={i} />)}
        </div>
      )}

      <JobFormDialog open={open} onOpenChange={setOpen} onSaved={load} />
      <DigestSettingsDialog open={digestOpen} onOpenChange={setDigestOpen} />
    </div>
  );
}
