export const UNIT_STATUSES = [
  { value: 'not_started', label: 'Not Started', badge: 'bg-slate-700/50 text-slate-300 border-slate-600', dot: 'bg-slate-400', text: 'text-slate-300', column: 'border-slate-500', glow: 'shadow-slate-500/10' },
  { value: 'in_fab', label: 'In Fab', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/30', dot: 'bg-blue-400', text: 'text-blue-400', column: 'border-blue-500', glow: 'shadow-blue-500/10' },
  { value: 'out_for_process', label: 'Out for Process', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30', dot: 'bg-amber-400', text: 'text-amber-400', column: 'border-amber-500', glow: 'shadow-amber-500/10' },
  { value: 'complete', label: 'Complete', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400', text: 'text-emerald-400', column: 'border-emerald-500', glow: 'shadow-emerald-500/10' },
];

export const JOB_STATUSES = [
  { value: 'quoted', label: 'Quoted', badge: 'bg-slate-700/50 text-slate-300 border-slate-600', dot: 'bg-slate-400' },
  { value: 'active', label: 'Active', badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30', dot: 'bg-cyan-400' },
  { value: 'on_hold', label: 'On Hold', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30', dot: 'bg-amber-400' },
  { value: 'complete', label: 'Complete', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400' },
];

export const PO_STATUSES = [
  { value: 'draft', label: 'Draft', badge: 'bg-slate-700/50 text-slate-300 border-slate-600', dot: 'bg-slate-400' },
  { value: 'ordered', label: 'Ordered', badge: 'bg-blue-500/10 text-blue-400 border-blue-500/30', dot: 'bg-blue-400' },
  { value: 'received', label: 'Received', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400' },
  { value: 'cancelled', label: 'Cancelled', badge: 'bg-red-500/10 text-red-400 border-red-500/30', dot: 'bg-red-400' },
];

export const UNIT_TYPES = ['window', 'door', 'bifold', 'slider', 'custom'];

export const ISSUE_SEVERITIES = [
  { value: 'low', label: 'Low', badge: 'bg-slate-700/50 text-slate-300 border-slate-600', dot: 'bg-slate-400' },
  { value: 'medium', label: 'Medium', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30', dot: 'bg-amber-400' },
  { value: 'high', label: 'High', badge: 'bg-red-500/10 text-red-400 border-red-500/30', dot: 'bg-red-400' },
];

export const ISSUE_STATUSES = [
  { value: 'open', label: 'Open', badge: 'bg-red-500/10 text-red-400 border-red-500/30', dot: 'bg-red-400' },
  { value: 'resolved', label: 'Resolved', badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', dot: 'bg-emerald-400' },
];

export const APPROVAL_TYPES = [
  { key: 'drawings', label: 'Drawings', hint: 'Shop drawings signed off by the customer' },
  { key: 'color_sample', label: 'Color Sample', hint: 'Paint / finish sample approved' },
  { key: 'hardware', label: 'Hardware', hint: 'Hardware brand, style and finish confirmed' },
];

export const SPEC_FIELDS = [
  { key: 'paint_type', label: 'Paint Type' },
  { key: 'paint_color', label: 'Color' },
  { key: 'hardware_brand', label: 'Hardware Brand' },
  { key: 'hardware_name', label: 'Hardware Name' },
  { key: 'hinge_type', label: 'Hinge Type' },
  { key: 'hinge_color', label: 'Hinge Color' },
  { key: 'custom_hardware', label: 'Custom Hardware' },
  { key: 'threshold_color', label: 'Threshold Color' },
  { key: 'glazing_bead_type', label: 'Glazing Bead Type' },
  { key: 'sdl_type', label: 'SDL Type' },
  { key: 'glass_type', label: 'Glass Type' },
];

export const EMPTY_SPECS = Object.fromEntries([...SPEC_FIELDS.map((f) => [f.key, '']), ['additional_notes', '']]);

export const statusMeta = (list, value) => list.find((s) => s.value === value) || list[0];

export const money = (n) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n || 0);

export const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '—');

export const fmtDateTime = (iso) =>
  iso ? new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—';

export const unitTypeFromNumber = (num) => {
  const m = /^([A-Za-z]{1,3})\d+/.exec((num || '').trim());
  if (!m) return 'custom';
  return { W: 'window', D: 'door', BF: 'bifold', SL: 'slider' }[m[1].toUpperCase()] || 'custom';
};
