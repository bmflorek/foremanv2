import { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { Tv, Maximize2, Minimize2, RefreshCw, ArrowLeft, Truck, Hexagon, CalendarClock } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { UNIT_STATUSES } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/PageHeader';
import { SelectField } from '@/components/FormControls';

const REFRESH_MS = 15000;

const groupByJob = (units) => {
  const groups = [];
  const index = {};
  units.forEach((u) => {
    if (index[u.job_id] === undefined) {
      index[u.job_id] = groups.length;
      groups.push({ job_id: u.job_id, job_number: u.job_number, job_name: u.job_name, units: [] });
    }
    groups[index[u.job_id]].units.push(u);
  });
  return groups;
};

const daysSince = (iso) => (iso ? Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)) : 0);

const dueUrgency = (dueDate, status) => {
  if (!dueDate || status === 'complete') return null;
  const days = Math.ceil((new Date(`${dueDate}T00:00:00`).getTime() - Date.now()) / 86400000);
  if (days < 0) return { level: 'overdue', days: -days, label: `${-days}d overdue`, card: 'ring-2 ring-red-500/70 shadow-[0_0_24px_rgba(239,68,68,0.35)] animate-[pulse_3s_ease-in-out_infinite]', chip: 'bg-red-500 text-white' };
  if (days <= 7) return { level: 'soon', days, label: days === 0 ? 'Due today' : `Due in ${days}d`, card: 'ring-2 ring-amber-500/60 shadow-[0_0_20px_rgba(245,158,11,0.3)]', chip: 'bg-amber-500 text-slate-950' };
  return null;
};

const UnitCard = ({ unit, tv, meta, draggable, onDragStart, onClick }) => {
  const days = daysSince(unit.status_changed_at);
  const urgency = dueUrgency(unit.due_date, unit.status);
  return (
    <div
      draggable={draggable}
      onDragStart={onDragStart}
      onClick={onClick}
      data-testid={`board-unit-${unit.job_number}-${unit.unit_number}`}
      data-urgency={urgency?.level || 'none'}
      className={cn(
        'group relative rounded-md border-l-4 bg-slate-800 shadow-md transition-[transform,box-shadow,background-color] duration-150',
        meta.column, meta.glow, urgency?.card,
        draggable && 'cursor-grab hover:-translate-y-0.5 hover:bg-slate-700/80 hover:shadow-lg active:cursor-grabbing',
        tv ? 'p-4' : 'p-3'
      )}
    >
      {urgency && (
        <span data-testid={`due-chip-${unit.job_number}-${unit.unit_number}`} className={cn('absolute -top-2 right-2 flex items-center gap-1 rounded-full px-2 py-0.5 font-mono font-bold uppercase tracking-wide', urgency.chip, tv ? 'text-sm' : 'text-[10px]')}>
          <CalendarClock size={tv ? 14 : 11} /> {urgency.label}
        </span>
      )}
      <div className="flex items-start justify-between gap-2">
        <span className={cn('font-mono font-bold leading-none text-slate-50', tv ? 'text-4xl' : 'text-2xl')}>{unit.unit_number}</span>
        <span className={cn('rounded bg-slate-900/70 px-2 py-0.5 font-mono font-semibold text-amber-400', tv ? 'text-xl' : 'text-sm')}>{unit.job_number}</span>
      </div>
      <p className={cn('mt-2 truncate font-medium text-slate-200', tv ? 'text-xl' : 'text-sm')} title={unit.description}>{unit.description || unit.unit_type}</p>
      <div className={cn('mt-1 flex items-center justify-between text-slate-400', tv ? 'text-base' : 'text-xs')}>
        <span className="truncate">{unit.job_name}</span>
        {(unit.width || unit.height) && <span className="ml-2 whitespace-nowrap font-mono">{unit.width || '?'} × {unit.height || '?'}</span>}
      </div>
      <div className={cn('mt-2 flex items-center justify-between', tv ? 'text-base' : 'text-xs')}>
        {unit.current_vendor_name ? (
          <span className="flex items-center gap-1.5 font-semibold text-amber-400"><Truck size={tv ? 18 : 13} />{unit.current_vendor_name}</span>
        ) : (
          <span className="text-slate-500">{unit.qty > 1 ? `Qty ${unit.qty}` : unit.location || ''}</span>
        )}
        <span className="font-mono text-slate-500">{days}d</span>
      </div>
    </div>
  );
};

export default function ShopBoardPage({ tv = false }) {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const jobFilter = params.get('job') || 'all';
  const [board, setBoard] = useState(null);
  const [tick, setTick] = useState(Date.now());
  const [dragging, setDragging] = useState(null);
  const [overCol, setOverCol] = useState(null);
  const [isFull, setIsFull] = useState(false);

  const load = useCallback(() => api.get('/board', { params: jobFilter !== 'all' ? { job_id: jobFilter } : {} }).then((r) => { setBoard(r.data); setTick(Date.now()); }).catch((e) => toast.error(errMsg(e))), [jobFilter]);
  useEffect(() => { load(); const id = setInterval(load, REFRESH_MS); return () => clearInterval(id); }, [load]);
  useEffect(() => {
    const onChange = () => setIsFull(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', onChange);
    return () => document.removeEventListener('fullscreenchange', onChange);
  }, []);

  const toggleFullscreen = () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else document.documentElement.requestFullscreen?.().catch(() => toast.info('Press F11 for fullscreen'));
  };

  const drop = async (status) => {
    setOverCol(null);
    if (!dragging || dragging.status === status) return;
    try {
      await api.patch(`/units/${dragging.id}`, { status });
      load();
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setDragging(null);
    }
  };

  const setJobFilter = (v) => setParams(v === 'all' ? {} : { job: v });
  const jobOptions = [{ value: 'all', label: 'All active jobs' }, ...(board?.jobs || []).map((j) => ({ value: j.id, label: `${j.job_number} · ${j.name}` }))];
  const grouped = jobFilter === 'all';

  const jobFilterSelect = (
    <SelectField testId="board-job-filter" value={jobFilter} onChange={setJobFilter} options={jobOptions} className={cn(tv ? 'h-11 w-72 text-base' : 'w-60')} />
  );

  const legend = (
    <div className={cn('flex items-center gap-4 font-mono uppercase tracking-wider text-slate-500', tv ? 'text-sm' : 'text-[11px]')} data-testid="urgency-legend">
      <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.7)]" /> Due ≤ 7d</span>
      <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.7)]" /> Overdue</span>
    </div>
  );

  const renderCards = (units, meta) => (
    units.map((u) => (
      <UnitCard key={u.id} unit={u} tv={tv} meta={meta} draggable={!tv}
        onDragStart={() => setDragging(u)}
        onClick={() => !tv && navigate(`/dashboard/jobs/${u.job_id}`)} />
    ))
  );

  const columns = (
    <div className={cn('grid gap-4 md:grid-cols-2 xl:grid-cols-4', tv && 'h-full')} data-testid="shop-board">
      {(board?.columns || UNIT_STATUSES.map((s) => ({ status: s.value, label: s.label, units: [] }))).map((col) => {
        const meta = UNIT_STATUSES.find((s) => s.value === col.status);
        return (
          <section
            key={col.status}
            data-testid={`board-column-${col.status}`}
            onDragOver={(e) => { if (!tv) { e.preventDefault(); setOverCol(col.status); } }}
            onDragLeave={() => setOverCol(null)}
            onDrop={() => drop(col.status)}
            className={cn('flex min-h-[60vh] flex-col rounded-lg border bg-slate-900/60 transition-colors', overCol === col.status ? 'border-amber-500 bg-amber-500/5' : 'border-slate-800')}
          >
            <header className={cn('flex items-center justify-between border-b border-slate-800 px-4', tv ? 'py-4' : 'py-3')}>
              <h2 className={cn('flex items-center gap-2 font-display font-bold uppercase tracking-wide', meta.text, tv ? 'text-3xl' : 'text-lg')}>
                <span className={cn('h-2.5 w-2.5 rounded-full', meta.dot)} />{col.label}
              </h2>
              <span className={cn('rounded-full bg-slate-800 px-3 py-0.5 font-mono font-bold text-slate-200', tv ? 'text-2xl' : 'text-sm')} data-testid={`board-count-${col.status}`}>{col.units.length}</span>
            </header>
            <div className={cn('flex flex-1 flex-col gap-3 overflow-y-auto p-3', tv && 'gap-4 p-4')}>
              {grouped
                ? groupByJob(col.units).map((g) => (
                    <div key={g.job_id} className="flex flex-col gap-3" data-testid={`board-group-${col.status}-${g.job_number}`}>
                      <div className={cn('flex items-baseline gap-2 border-b border-slate-700/70 pb-1', tv ? 'text-lg' : 'text-xs')}>
                        <span className="font-mono font-bold text-amber-400">{g.job_number}</span>
                        <span className="truncate font-semibold uppercase tracking-wide text-slate-400">{g.job_name}</span>
                        <span className="ml-auto font-mono text-slate-500">{g.units.length}</span>
                      </div>
                      {renderCards(g.units, meta)}
                    </div>
                  ))
                : renderCards(col.units, meta)}
              {col.units.length === 0 && <p className={cn('mt-6 text-center text-slate-600', tv ? 'text-xl' : 'text-sm')}>Nothing here</p>}
            </div>
          </section>
        );
      })}
    </div>
  );

  if (tv) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-950 p-4 lg:p-6" data-testid="tv-board-page">
        <header className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="grid h-12 w-12 place-items-center rounded-md bg-amber-500 text-slate-950"><Hexagon size={28} strokeWidth={2.5} /></span>
            <div>
              <h1 className="text-4xl font-extrabold uppercase tracking-tight leading-none">Shop Board</h1>
              <p className="font-mono text-sm uppercase tracking-[0.2em] text-slate-500">
                {board ? `${board.total_units} units · ${board.active_jobs} active jobs` : 'Loading…'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {legend}
            {jobFilterSelect}
            <span className="flex items-center gap-2 font-mono text-sm text-slate-500" data-testid="tv-refresh-indicator">
              <RefreshCw size={14} className="animate-[spin_15s_linear_infinite]" /> {new Date(tick).toLocaleTimeString()}
            </span>
            <Button variant="outline" onClick={toggleFullscreen} data-testid="tv-fullscreen-button">{isFull ? <Minimize2 size={16} /> : <Maximize2 size={16} />}</Button>
            <Link to={`/dashboard/board${jobFilter !== 'all' ? `?job=${jobFilter}` : ''}`} data-testid="exit-tv-mode-link" className="flex items-center gap-1.5 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-400 hover:text-slate-100"><ArrowLeft size={15} /> Exit</Link>
          </div>
        </header>
        {columns}
      </div>
    );
  }

  return (
    <div>
      <PageHeader eyebrow="Shop Floor" title="Shop Board" subtitle="Drag units between columns. Checked-out units must be checked in via the tracker.">
        {legend}
        {jobFilterSelect}
        <span className="flex items-center gap-2 font-mono text-xs text-slate-500" data-testid="board-refresh-indicator"><RefreshCw size={12} /> auto · {new Date(tick).toLocaleTimeString()}</span>
        <Button variant="outline" onClick={load} data-testid="board-refresh-button"><RefreshCw size={15} /></Button>
        <Button onClick={() => navigate(`/board${jobFilter !== 'all' ? `?job=${jobFilter}` : ''}`)} data-testid="tv-mode-toggle-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400"><Tv size={16} className="mr-1.5" /> TV Mode</Button>
      </PageHeader>
      {columns}
    </div>
  );
}
