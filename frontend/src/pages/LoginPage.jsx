import { Hexagon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Field } from '@/components/PageHeader';
import { useAuthForm } from '@/hooks/useAuthForm';

const HERO = 'https://images.unsplash.com/photo-1549492761-123cdcb927aa?crop=entropy&cs=srgb&fm=jpg&q=85&w=1400';

const HeroPanel = () => (
  <div className="relative hidden overflow-hidden lg:block">
    <img src={HERO} alt="Architectural glass and door facade" className="absolute inset-0 h-full w-full object-cover" />
    <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/60 to-slate-950/20" />
    <div className="relative flex h-full flex-col justify-end p-14">
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-amber-400">Jobs · Units · In/Out · Budget</p>
      <h1 className="mt-3 max-w-xl text-5xl font-extrabold uppercase leading-[0.95] tracking-tight text-slate-50 lg:text-6xl">
        Every unit, every job, on the board.
      </h1>
      <p className="mt-4 max-w-md text-slate-300">Custom window & door fabrication tracking from quote to install.</p>
    </div>
  </div>
);

const Brand = () => (
  <div className="flex items-center gap-3">
    <span className="grid h-11 w-11 place-items-center rounded-md bg-amber-500 text-slate-950">
      <Hexagon size={24} strokeWidth={2.5} />
    </span>
    <div className="leading-none">
      <p className="font-display text-2xl font-extrabold uppercase tracking-wide">ShopTrack</p>
      <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">Fabrication Ops</p>
    </div>
  </div>
);

const ModeLinks = ({ mode, switchMode }) => (
  <div className="flex items-center justify-between text-sm text-slate-400">
    {mode === 'login' ? (
      <>
        <button type="button" data-testid="auth-switch-register" onClick={() => switchMode('register')} className="hover:text-amber-400">Create an account</button>
        <button type="button" data-testid="auth-switch-reset" onClick={() => switchMode('reset')} className="hover:text-amber-400">Forgot password?</button>
      </>
    ) : (
      <button type="button" data-testid="auth-switch-login" onClick={() => switchMode('login')} className="hover:text-amber-400">← Back to sign in</button>
    )}
  </div>
);

export default function LoginPage({ setUser }) {
  const { mode, form, otpSent, busy, set, switchMode, submit, title, submitLabel } = useAuthForm(setUser);

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <HeroPanel />
      <div className="flex items-center justify-center px-6 py-12">
        <form onSubmit={submit} className="w-full max-w-sm space-y-6 animate-rise" data-testid="auth-form">
          <Brand />
          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight">{title}</h2>
            <p className="text-sm text-slate-400">
              {mode === 'reset' && otpSent ? 'Enter the 6-digit code from your email.' : 'Shop floor access for your crew.'}
            </p>
          </div>

          {mode === 'register' && (
            <Field label="Name">
              <Input data-testid="auth-name-input" value={form.name} onChange={set('name')} required placeholder="Jane Fabricator" />
            </Field>
          )}
          <Field label="Email">
            <Input data-testid="auth-email-input" type="email" value={form.email} onChange={set('email')} required placeholder="you@shop.com" disabled={mode === 'reset' && otpSent} />
          </Field>
          {mode !== 'reset' && (
            <Field label="Password">
              <Input data-testid="auth-password-input" type="password" value={form.password} onChange={set('password')} required minLength={6} placeholder="••••••••" />
            </Field>
          )}
          {mode === 'reset' && otpSent && (
            <>
              <Field label="Reset code">
                <Input data-testid="auth-otp-input" value={form.otp} onChange={set('otp')} required className="font-mono tracking-[0.4em]" maxLength={6} />
              </Field>
              <Field label="New password">
                <Input data-testid="auth-new-password-input" type="password" value={form.new_password} onChange={set('new_password')} required minLength={6} />
              </Field>
            </>
          )}

          <Button type="submit" disabled={busy} data-testid="auth-submit-button" className="h-11 w-full bg-amber-500 font-display text-base font-bold uppercase tracking-wider text-slate-950 hover:bg-amber-400">
            {submitLabel}
          </Button>
          <ModeLinks mode={mode} switchMode={switchMode} />
        </form>
      </div>
    </div>
  );
}
