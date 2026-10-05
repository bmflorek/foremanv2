import { useCallback, useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Mail, Plus, X, Send, Clock } from 'lucide-react';
import { api, errMsg } from '@/lib/api';
import { fmtDateTime } from '@/lib/constants';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';

const RecipientsEditor = ({ recipients, busy, onChange }) => {
  const [newEmail, setNewEmail] = useState('');
  const add = (e) => {
    e.preventDefault();
    const v = newEmail.trim().toLowerCase();
    if (!v) return;
    if (recipients.includes(v)) return toast.error('Already on the list');
    onChange([...recipients, v]);
    setNewEmail('');
  };
  return (
    <div>
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recipients ({recipients.length})</p>
      <div className="space-y-2" data-testid="digest-recipients-list">
        {recipients.length === 0 && <p className="text-sm text-slate-500" data-testid="digest-no-recipients">No recipients yet — add an email below.</p>}
        {recipients.map((r) => (
          <div key={r} className="flex items-center justify-between rounded-md bg-slate-800/70 px-3 py-2 text-sm" data-testid={`digest-recipient-${r}`}>
            <span className="font-mono">{r}</span>
            <button disabled={busy} onClick={() => onChange(recipients.filter((x) => x !== r))} data-testid={`digest-remove-${r}`} className="rounded p-1 text-slate-500 hover:bg-red-500/10 hover:text-red-400"><X size={14} /></button>
          </div>
        ))}
      </div>
      <form onSubmit={add} className="mt-3 flex gap-2">
        <Input type="email" value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder="crew@yourshop.com" data-testid="digest-email-input" />
        <Button type="submit" variant="outline" disabled={busy || !newEmail} data-testid="digest-add-recipient-button"><Plus size={15} className="mr-1" /> Add</Button>
      </form>
    </div>
  );
};

const DigestPreview = ({ preview }) => (
  <div className="rounded-lg border border-slate-700/80 bg-slate-800/40 p-4" data-testid="digest-preview">
    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-amber-500">If sent right now</p>
    {!preview ? <p className="text-sm text-slate-500">Loading…</p> : (
      <div className="grid grid-cols-3 gap-3 text-center">
        {[['Overdue jobs', preview.overdue_jobs.length, 'text-red-400'], ['Units out 7+ d', preview.stale_units.length, 'text-amber-400'], ['High issues', preview.open_high_issues, 'text-red-400']].map(([l, v, c]) => (
          <div key={l}>
            <p className={`font-mono text-2xl font-bold ${v ? c : 'text-emerald-400'}`}>{v}</p>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{l}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);

const RecentRuns = ({ runs }) => {
  if (!runs?.length) return null;
  return (
    <div data-testid="digest-recent-runs">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Recent sends</p>
      <ul className="space-y-1 text-xs text-slate-400">
        {runs.slice(0, 5).map((r) => (
          <li key={r.run_id} className="flex justify-between font-mono">
            <span>{r.trigger === 'cron' ? 'Scheduled' : 'Manual'} · {r.sent?.length ?? 0} sent{r.failed?.length ? ` · ${r.failed.length} failed` : ''}</span>
            <span>{fmtDateTime(r.created_at)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export const DigestSettingsDialog = ({ open, onOpenChange }) => {
  const [settings, setSettings] = useState(null);
  const [preview, setPreview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [sending, setSending] = useState(false);

  const load = useCallback(() => {
    api.get('/settings/digest').then((r) => setSettings(r.data)).catch((e) => toast.error(errMsg(e)));
    api.get('/digest/preview').then((r) => setPreview(r.data));
  }, []);
  useEffect(() => { if (open) load(); }, [open, load]);

  const save = async (patch) => {
    setBusy(true);
    try {
      const next = { ...settings, ...patch };
      const { data } = await api.put('/settings/digest', { recipients: next.recipients, enabled: next.enabled });
      setSettings((s) => ({ ...s, ...data }));
      toast.success('Digest settings saved');
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  const sendTest = async () => {
    setSending(true);
    try {
      const { data } = await api.post('/digest/send-test');
      toast.success(`Digest sent to ${data.sent.join(', ')}`);
      load();
    } catch (e) {
      toast.error(errMsg(e));
    } finally {
      setSending(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-xl" data-testid="digest-settings-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 font-display text-2xl uppercase tracking-wide"><Mail className="text-amber-400" size={22} /> Morning Digest</DialogTitle>
          <DialogDescription>Emailed daily at 6:30 AM Eastern: overdue jobs, units out at vendors 7+ days, and open high-severity issues.</DialogDescription>
        </DialogHeader>

        {!settings ? <p className="text-sm text-slate-500">Loading…</p> : (
          <div className="space-y-6">
            <div className="flex items-center justify-between rounded-lg border border-slate-700/80 bg-slate-800/60 px-4 py-3">
              <div>
                <p className="font-semibold">Daily send</p>
                <p className="flex items-center gap-1 text-xs text-slate-400"><Clock size={11} /> {settings.last_sent_at ? `Last sent ${fmtDateTime(settings.last_sent_at)}` : 'Never sent yet'}</p>
              </div>
              <Switch checked={settings.enabled} disabled={busy} onCheckedChange={(v) => save({ enabled: v })} data-testid="digest-enabled-switch" />
            </div>
            <RecipientsEditor recipients={settings.recipients} busy={busy} onChange={(recipients) => save({ recipients })} />
            <DigestPreview preview={preview} />
            <RecentRuns runs={settings.recent_runs} />
          </div>
        )}

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} data-testid="digest-close-button">Close</Button>
          <Button onClick={sendTest} disabled={sending || !settings?.recipients?.length} data-testid="digest-send-test-button" className="bg-amber-500 font-semibold text-slate-950 hover:bg-amber-400">
            <Send size={15} className="mr-1.5" /> {sending ? 'Sending…' : 'Send test digest now'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
