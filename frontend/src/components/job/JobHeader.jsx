import { Link } from 'react-router-dom';
import { ArrowLeft, Pencil, Trash2, MapPin, CalendarDays, User } from 'lucide-react';
import { JOB_STATUSES, UNIT_STATUSES, money, fmtDate } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/StatusBadge';
import { BudgetBar } from '@/components/BudgetBar';
import { ConfirmDelete } from '@/components/FormControls';

export const JobHeader = ({ job, onEdit, onDelete }) => (
  <>
    <Link to="/dashboard/jobs" className="mb-5 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-amber-400" data-testid="back-to-jobs-link">
      <ArrowLeft size={15} /> All jobs
    </Link>
    <div className="mb-6 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-4xl font-bold tracking-wider text-amber-400 sm:text-5xl" data-testid="job-number">{job.job_number}</span>
          <StatusBadge list={JOB_STATUSES} value={job.status} size="md" testId="job-status-badge" />
        </div>
        <h1 className="mt-1 text-3xl font-extrabold uppercase tracking-tight sm:text-4xl" data-testid="job-name">{job.name}</h1>
        <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-400">
          {job.customer && <span className="flex items-center gap-1.5"><User size={14} />{job.customer}</span>}
          {job.address && <span className="flex items-center gap-1.5"><MapPin size={14} />{job.address}</span>}
          {job.due_date && <span className="flex items-center gap-1.5"><CalendarDays size={14} />Due {fmtDate(job.due_date)}</span>}
        </div>
      </div>
      <div className="flex gap-2">
        <Button variant="outline" onClick={onEdit} data-testid="edit-job-button"><Pencil size={15} className="mr-1.5" /> Edit Job</Button>
        <ConfirmDelete testId="delete-job" title={`Delete job ${job.job_number}?`} description="All units, purchase orders, issues and movement history for this job will be removed." onConfirm={onDelete}
          trigger={<Button variant="outline" data-testid="delete-job-button" className="border-red-500/40 text-red-400 hover:bg-red-500/10 hover:text-red-300"><Trash2 size={15} /></Button>} />
      </div>
    </div>
  </>
);

export const JobSummary = ({ job }) => (
  <div className="mb-8 grid gap-4 lg:grid-cols-[1fr_auto]">
    <div className="rounded-lg border border-slate-700/80 bg-slate-800/50 p-5">
      <div className="mb-3 flex items-baseline justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Budget</p>
        <p className="font-mono text-sm text-slate-300">Sold <span className="text-lg font-bold text-slate-50" data-testid="job-sold-amount">{money(job.sold_amount)}</span></p>
      </div>
      <BudgetBar budget={job.budget} />
    </div>
    <div className="flex items-center gap-2 rounded-lg border border-slate-700/80 bg-slate-800/50 px-5 py-4" data-testid="job-unit-summary">
      <div className="mr-3 text-center">
        <p className="font-mono text-3xl font-bold">{job.unit_counts.total}</p>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Units</p>
      </div>
      {UNIT_STATUSES.map((s) => (
        <div key={s.value} className="min-w-[64px] rounded border border-slate-700/60 px-2 py-1.5 text-center" title={s.label}>
          <p className="font-mono text-lg font-bold">{job.unit_counts[s.value] || 0}</p>
          <p className="flex items-center justify-center gap-1 text-[9px] font-semibold uppercase tracking-wider text-slate-400"><span className={cn('h-1.5 w-1.5 rounded-full', s.dot)} />{s.label}</p>
        </div>
      ))}
    </div>
  </div>
);
