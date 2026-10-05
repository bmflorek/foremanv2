import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { ArrowUpRight, ArrowDownLeft, Truck, PackageOpen } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { fmtDateTime } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { PageHeader, Field, EmptyState } from '@/components/PageHeader';
import { SelectField } from '@/components/FormControls';
import { MovementLog } from '@/components/job/MovementLog';

export default function TrackerPage() {
  const [jobs, setJobs] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [units, setUnits] = useState([]);
  const [out, setOut] = useState(null);
  const [movements, setMovements] = useState(null);
  const [form, setForm] = useState({ job_id: '', unit_id: '', vendor_id: '', notes: '' });
  const [busy, setBusy] = useState(false);

  const loadLists = useCallback(() => {
    api.get('/movements/out').then((r) => setOut(r.data));
    api.get('/movements', { params: { limit: 50 } }).then((r) => setMovements(r.data));
  }, []);

  useEffect(() => {
    api.get('/jobs').then((r) => setJobs(r.data.filter((j) => j.status !== 'complete')));
    api.get('/vendors').then((r) => setVendors(r.data));
    loadLists();
  }, [loadLists]);

  useEffect(() => {
    if (!form.job_id) return setUnits([]);
    api.get(`/jobs/${form.job_id}/units`).then((r) => setUnits(r.data.filter((u) => !u.current_vendor_id && u.status !== 'complete')));
  }, [form.job_id, out]);

  const checkOut = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post('/movements', { unit_id: form.unit_id, direction: 'out', vendor_id: form.vendor_id, notes: form.notes });
      toast.success(`${data.unit_number} checked out to ${data.vendor_name}`);
      setForm({ ...form, unit_id: '', notes: '' });
      loadLists();
    } catch (err) {
      toast.error(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  const checkIn = async (u) => {
    try {
      const { data } = await api.post('/movements', { unit_id: u.id, direction: 'in' });
      toast.success(`${data.unit_number} checked back in from ${data.vendor_name}`);
      loadLists();
    } catch (err) {
      toast.error(errMsg(err));
    }
  };

  const jobOptions = jobs.map((j) => ({ value: j.id, label: `${j.job_number} · ${j.name}` }));
  const unitOptions = units.map((u) => ({ value: u.id, label: `${u.unit_number}${u.description ? ` · ${u.description}` : ''}` }));
  const vendorOptions = vendors.map((v) => ({ value: v.id, label: `${v.name}${v.service ? ` · ${v.service}` : ''}` }));

  return (
    <div>
      <PageHeader eyebrow="Logistics" title="In / Out Tracker" subtitle="Check units out to vendors for welding, paint, glazing and back in when they return." />

      <div className="grid gap-6 xl:grid-cols-[400px_1fr]">
        <form onSubmit={checkOut} className="h-fit rounded-lg border border-amber-500/30 bg-slate-800/60 p-5" data-testid="checkout-form">
          <h2 className="mb-4 flex items-center gap-2 text-2xl font-bold uppercase tracking-wide text-amber-400"><ArrowUpRight size={22} /> Check Out</h2>
          <div className="space-y-4">
            <Field label="Job">
              <SelectField testId="checkout-job-select" value={form.job_id} onChange={(v) => setForm({ ...form, job_id: v, unit_id: '' })} options={jobOptions} placeholder="Select job…" />
            </Field>
            <Field label="Unit">
              <SelectField testId="checkout-unit-select" value={form.unit_id} onChange={(v) => setForm({ ...form, unit_id: v })} options={unitOptions} placeholder={form.job_id ? (unitOptions.length ? 'Select unit…' : 'No units available') : 'Pick a job first'} disabled={!form.job_id || !unitOptions.length} />
            </Field>
            <Field label="Vendor / Location">
              <SelectField testId="checkout-vendor-select" value={form.vendor_id} onChange={(v) => setForm({ ...form, vendor_id: v })} options={vendorOptions} placeholder={vendors.length ? 'Select vendor…' : 'Add vendors first'} disabled={!vendors.length} />
            </Field>
            <Field label="Notes">
              <Textarea data-testid="checkout-notes-input" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} placeholder="Weld corners, grind flush…" />
            </Field>
            <Button type="submit" disabled={busy || !form.unit_id || !form.vendor_id} data-testid="checkout-unit-submit-button" className="h-11 w-full bg-amber-500 font-display text-base font-bold uppercase tracking-wider text-slate-950 hover:bg-amber-400">
              {busy ? 'Working…' : 'Check Out Unit'}
            </Button>
          </div>
        </form>

        <div className="space-y-4">
          <h2 className="flex items-center gap-2 text-2xl font-bold uppercase tracking-wide"><Truck size={22} className="text-amber-400" /> Currently Out <span className="ml-1 rounded-full bg-slate-800 px-3 py-0.5 font-mono text-base" data-testid="out-count">{out?.length ?? '…'}</span></h2>
          {out && out.length === 0 ? (
            <EmptyState icon={PackageOpen} title="Everything is in the shop" hint="Check a unit out when it leaves for an outside process." testId="out-empty-state" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3" data-testid="out-list">
              {(out || []).map((u, i) => (
                <div key={u.id} data-testid={`out-unit-${u.job_number}-${u.unit_number}`} style={{ animationDelay: `${i * 40}ms` }} className="animate-rise flex flex-col gap-3 rounded-lg border-l-4 border-amber-500 bg-slate-800/80 p-4 shadow-md">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-mono text-3xl font-bold leading-none">{u.unit_number}</p>
                      <p className="mt-1 text-sm text-slate-400">{u.description || u.unit_type}</p>
                    </div>
                    <span className={cn('rounded px-2 py-1 font-mono text-sm font-bold', u.days_out >= 7 ? 'bg-red-500/15 text-red-400' : u.days_out >= 3 ? 'bg-amber-500/15 text-amber-400' : 'bg-slate-700 text-slate-200')} data-testid={`days-out-${u.unit_number}`}>
                      {u.days_out}d out
                    </span>
                  </div>
                  <div className="text-sm">
                    <p className="text-slate-200"><span className="font-mono text-amber-400">{u.job_number}</span> · {u.job_name}</p>
                    <p className="flex items-center gap-1.5 text-slate-300"><Truck size={13} className="text-amber-400" /> {u.vendor_name}{u.vendor_service ? <span className="text-slate-500"> · {u.vendor_service}</span> : null}</p>
                    <p className="font-mono text-xs text-slate-500">since {fmtDateTime(u.out_since)}</p>
                  </div>
                  <Button size="sm" variant="outline" onClick={() => checkIn(u)} data-testid={`checkin-button-${u.unit_number}`} className="border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 hover:text-emerald-300">
                    <ArrowDownLeft size={15} className="mr-1" /> Check In
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-10">
        <h2 className="mb-4 text-2xl font-bold uppercase tracking-wide">Recent Movements</h2>
        <MovementLog movements={movements} showJob testId="tracker-movement-log" />
      </div>
    </div>
  );
}
