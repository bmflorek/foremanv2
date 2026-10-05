import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, Factory, Phone, Mail, MapPin, User, Timer, Truck } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { PageHeader, EmptyState } from '@/components/PageHeader';
import { ConfirmDelete } from '@/components/FormControls';
import { VendorFormDialog } from '@/components/VendorFormDialog';

const TurnaroundStats = ({ stats, vendorId }) => {
  const avg = stats?.avg_days_out;
  const tone = avg == null ? 'text-slate-500' : avg >= 7 ? 'text-red-400' : avg >= 3 ? 'text-amber-400' : 'text-emerald-400';
  return (
    <div className="grid grid-cols-3 divide-x divide-slate-700/60 rounded-md border border-slate-700/60 bg-slate-900/50" data-testid={`vendor-stats-${vendorId}`}>
      <div className="px-3 py-2 text-center">
        <p className={cn('flex items-center justify-center gap-1 font-mono text-xl font-bold tabular', tone)} data-testid={`vendor-avg-days-${vendorId}`}>
          <Timer size={14} />{avg == null ? '—' : `${avg}d`}
        </p>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Avg Out</p>
      </div>
      <div className="px-3 py-2 text-center">
        <p className="font-mono text-xl font-bold tabular text-slate-200">{stats?.completed_trips ?? 0}</p>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Trips</p>
      </div>
      <div className="px-3 py-2 text-center">
        <p className={cn('flex items-center justify-center gap-1 font-mono text-xl font-bold tabular', stats?.currently_out ? 'text-amber-400' : 'text-slate-200')}>
          <Truck size={14} />{stats?.currently_out ?? 0}
        </p>
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Out Now</p>
      </div>
    </div>
  );
};

export default function VendorsPage() {
  const [vendors, setVendors] = useState(null);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);
  const [sortSlow, setSortSlow] = useState(false);

  const load = useCallback(() => api.get('/vendors').then((r) => setVendors(r.data)).catch((e) => toast.error(errMsg(e))), []);
  useEffect(() => { load(); }, [load]);

  const list = sortSlow ? [...(vendors || [])].sort((a, b) => (b.stats?.avg_days_out ?? -1) - (a.stats?.avg_days_out ?? -1)) : vendors || [];

  const remove = async (v) => {
    try { await api.delete(`/vendors/${v.id}`); toast.success(`${v.name} deleted`); load(); } catch (e) { toast.error(errMsg(e)); }
  };

  return (
    <div>
      <PageHeader eyebrow="Outside Processes" title="Vendors" subtitle="Welders, painters, glaziers and anodizers your units travel to. Avg Out = average days a unit spends at the vendor (red ≥ 7d).">
        {vendors && vendors.some((v) => v.stats?.avg_days_out != null) && (
          <button onClick={() => setSortSlow((s) => !s)} data-testid="vendors-sort-toggle" className={cn('rounded-md border px-3 py-2 text-sm font-semibold transition-colors', sortSlow ? 'border-amber-500/60 bg-amber-500/10 text-amber-400' : 'border-slate-700 text-slate-400 hover:text-slate-100')}>
            <Timer size={14} className="mr-1.5 inline" /> {sortSlow ? 'Slowest first' : 'Sort by slowest'}
          </button>
        )}
        <Button onClick={() => { setEditing(null); setOpen(true); }} data-testid="create-vendor-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
          <Plus size={16} className="mr-1.5" /> New Vendor
        </Button>
      </PageHeader>

      {vendors && vendors.length === 0 ? (
        <EmptyState icon={Factory} title="No vendors yet" hint="Add the shops you send units to; they populate the check-out dropdown." testId="vendors-empty-state" />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" data-testid="vendors-grid">
          {list.map((v, i) => (
            <div key={v.id} data-testid={`vendor-card-${v.id}`} style={{ animationDelay: `${i * 40}ms` }} className="animate-rise flex flex-col gap-3 rounded-lg border border-slate-700/80 bg-slate-800/70 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-2xl font-bold uppercase leading-tight tracking-wide">{v.name}</h3>
                  {v.service && <span className="mt-1 inline-block rounded bg-amber-500/15 px-2 py-0.5 font-mono text-xs font-semibold uppercase tracking-wider text-amber-400" data-testid={`vendor-service-${v.id}`}>{v.service}</span>}
                </div>
                <div className="flex gap-1">
                  <button onClick={() => { setEditing(v); setOpen(true); }} data-testid={`edit-vendor-${v.id}`} className="rounded p-1.5 text-slate-400 hover:bg-slate-700 hover:text-slate-100"><Pencil size={15} /></button>
                  <ConfirmDelete testId={`delete-vendor-${v.id}`} title={`Delete ${v.name}?`} description="Vendors with units currently checked out cannot be deleted." onConfirm={() => remove(v)}
                    trigger={<button data-testid={`delete-vendor-${v.id}`} className="rounded p-1.5 text-slate-400 hover:bg-red-500/10 hover:text-red-400"><Trash2 size={15} /></button>} />
                </div>
              </div>
              <TurnaroundStats stats={v.stats} vendorId={v.id} />
              <div className="space-y-1 text-sm text-slate-300">
                {v.contact_name && <p className="flex items-center gap-2"><User size={13} className="text-slate-500" />{v.contact_name}</p>}
                {v.phone && <p className="flex items-center gap-2 font-mono"><Phone size={13} className="text-slate-500" />{v.phone}</p>}
                {v.email && <p className="flex items-center gap-2"><Mail size={13} className="text-slate-500" />{v.email}</p>}
                {v.address && <p className="flex items-center gap-2"><MapPin size={13} className="text-slate-500" />{v.address}</p>}
              </div>
              {v.notes && <p className="border-t border-slate-700/60 pt-3 text-sm text-slate-400">{v.notes}</p>}
            </div>
          ))}
        </div>
      )}

      <VendorFormDialog open={open} onOpenChange={setOpen} vendor={editing} onSaved={load} />
    </div>
  );
}
