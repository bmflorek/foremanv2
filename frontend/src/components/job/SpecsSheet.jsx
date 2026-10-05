import { SPEC_FIELDS } from '@/lib/constants';

export const SpecsSheet = ({ job }) => {
  const specs = job.specs || {};
  return (
    <div data-testid="specs-sheet" className="rounded-lg border border-slate-700/80 bg-slate-800/50">
      <dl className="grid divide-y divide-slate-700/60 sm:grid-cols-2 sm:divide-y-0 lg:grid-cols-3">
        {SPEC_FIELDS.map((f) => (
          <div key={f.key} className="border-slate-700/60 px-5 py-4 sm:border-b" data-testid={`spec-${f.key}`}>
            <dt className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{f.label}</dt>
            <dd className={`mt-1 text-base ${specs[f.key] ? 'text-slate-50' : 'text-slate-600'}`}>{specs[f.key] || '—'}</dd>
          </div>
        ))}
      </dl>
      <div className="px-5 py-5" data-testid="spec-additional-notes">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-500">Additional / Custom</p>
        <p className={`mt-1 whitespace-pre-wrap text-base ${specs.additional_notes ? 'text-slate-50' : 'text-slate-600'}`}>
          {specs.additional_notes || 'No additional notes.'}
        </p>
      </div>
      {job.notes && (
        <div className="border-t border-slate-700/60 px-5 py-4" data-testid="job-internal-notes">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Internal Notes</p>
          <p className="mt-1 whitespace-pre-wrap text-sm text-slate-300">{job.notes}</p>
        </div>
      )}
    </div>
  );
};
