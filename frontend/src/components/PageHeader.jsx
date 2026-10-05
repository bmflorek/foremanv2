export const PageHeader = ({ eyebrow, title, subtitle, children }) => (
  <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
    <div>
      {eyebrow && <p className="mb-1 font-mono text-xs uppercase tracking-[0.2em] text-amber-500">{eyebrow}</p>}
      <h1 className="text-3xl font-extrabold uppercase tracking-tight text-slate-50 sm:text-4xl">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-400 md:text-base">{subtitle}</p>}
    </div>
    {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
  </div>
);

export const EmptyState = ({ icon: Icon, title, hint, testId }) => (
  <div data-testid={testId} className="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-6 py-14 text-center">
    {Icon && <Icon className="mb-3 text-slate-600" size={36} />}
    <p className="font-display text-xl font-semibold uppercase tracking-wide text-slate-300">{title}</p>
    {hint && <p className="mt-1 max-w-sm text-sm text-slate-500">{hint}</p>}
  </div>
);

export const Field = ({ label, children, className = '' }) => (
  <label className={`flex flex-col gap-1.5 ${className}`}>
    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{label}</span>
    {children}
  </label>
);
