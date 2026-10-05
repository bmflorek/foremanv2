import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { JobFormDialog } from '@/components/JobFormDialog';
import { JobHeader, JobSummary } from '@/components/job/JobHeader';
import { SpecsSheet } from '@/components/job/SpecsSheet';
import { UnitsTab } from '@/components/job/UnitsTab';
import { PurchaseOrdersTab } from '@/components/job/PurchaseOrdersTab';
import { MovementLog } from '@/components/job/MovementLog';
import { IssuesTab } from '@/components/job/IssuesTab';
import { ApprovalsTab } from '@/components/job/ApprovalsTab';

const tabList = (job) => [
  ['specs', 'Spec Sheet'],
  ['units', 'Units'],
  ['pos', 'Purchase Orders'],
  ['issues', 'Issues', job.open_issues],
  ['approvals', 'Approvals', `${job.approvals_done}/${job.approvals_total}`],
  ['movements', 'Movement Log'],
];

export default function JobDetailPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [movements, setMovements] = useState(null);
  const [edit, setEdit] = useState(false);
  const [tab, setTab] = useState('specs');

  const load = useCallback(() => api.get(`/jobs/${jobId}`).then((r) => setJob(r.data)).catch(() => { toast.error('Job not found'); navigate('/dashboard/jobs'); }), [jobId, navigate]);
  const loadMovements = useCallback(() => api.get('/movements', { params: { job_id: jobId } }).then((r) => setMovements(r.data)), [jobId]);

  useEffect(() => { load(); api.get('/vendors').then((r) => setVendors(r.data)); }, [load]);
  useEffect(() => { if (tab === 'movements') loadMovements(); }, [tab, loadMovements]);

  const remove = async () => {
    try { await api.delete(`/jobs/${jobId}`); toast.success(`Job ${job.job_number} deleted`); navigate('/dashboard/jobs'); } catch (e) { toast.error(errMsg(e)); }
  };

  if (!job) return <div className="loading-screen !min-h-[50vh]"><div className="spinner" /></div>;

  return (
    <div data-testid="job-detail-page">
      <JobHeader job={job} onEdit={() => setEdit(true)} onDelete={remove} />
      <JobSummary job={job} />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-5 h-auto flex-wrap justify-start gap-1 bg-slate-800/60 p-1">
          {tabList(job).map(([v, l, badge]) => (
            <TabsTrigger key={v} value={v} data-testid={`tab-${v}`} className="font-display text-base uppercase tracking-wide data-[state=active]:bg-amber-500 data-[state=active]:text-slate-950">
              {l}
              {badge !== undefined && badge !== 0 && (
                <span data-testid={`tab-${v}-badge`} className={cn('ml-2 rounded-full px-2 py-0.5 font-mono text-[11px] font-bold', v === 'issues' ? 'bg-red-500 text-white' : 'bg-slate-700 text-slate-200')}>{badge}</span>
              )}
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value="specs"><SpecsSheet job={job} /></TabsContent>
        <TabsContent value="units"><UnitsTab job={job} onChanged={load} /></TabsContent>
        <TabsContent value="pos"><PurchaseOrdersTab job={job} vendors={vendors} onChanged={load} /></TabsContent>
        <TabsContent value="issues"><IssuesTab job={job} onChanged={load} /></TabsContent>
        <TabsContent value="approvals"><ApprovalsTab job={job} onChanged={load} /></TabsContent>
        <TabsContent value="movements"><MovementLog movements={movements} /></TabsContent>
      </Tabs>

      <JobFormDialog open={edit} onOpenChange={setEdit} job={job} onSaved={load} />
    </div>
  );
}
