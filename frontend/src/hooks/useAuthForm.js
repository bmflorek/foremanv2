import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { api, errMsg } from '@/lib/api';

const EMPTY = { email: '', password: '', name: '', otp: '', new_password: '' };

export const useAuthForm = (setUser) => {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState(EMPTY);
  const [otpSent, setOtpSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const switchMode = (next) => { setMode(next); setOtpSent(false); };

  const handleReset = async () => {
    if (!otpSent) {
      await api.post('/auth/request-password-reset', { email: form.email });
      setOtpSent(true);
      toast.success('If that email exists, a reset code was sent');
      return;
    }
    await api.post('/auth/verify-reset-otp', { email: form.email, otp: form.otp, new_password: form.new_password });
    toast.success('Password reset. Please sign in.');
    switchMode('login');
  };

  const handleCredentials = async () => {
    const body = mode === 'login' ? { email: form.email, password: form.password } : { email: form.email, password: form.password, name: form.name };
    const { data } = await api.post(`/auth/${mode}`, body);
    localStorage.setItem('session_token', data.session_token);
    setUser(data.user);
    navigate('/dashboard/jobs');
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await (mode === 'reset' ? handleReset() : handleCredentials());
    } catch (err) {
      toast.error(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  const title = { login: 'Sign in', register: 'Create account', reset: 'Reset password' }[mode];
  const submitLabel = busy ? 'Working…' : mode === 'reset' ? (otpSent ? 'Set new password' : 'Send reset code') : title;

  return { mode, form, otpSent, busy, set, switchMode, submit, title, submitLabel };
};
