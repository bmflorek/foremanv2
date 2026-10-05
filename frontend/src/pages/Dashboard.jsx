import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Briefcase, LayoutGrid, ArrowLeftRight, Factory, LogOut, Hexagon } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

const NAV = [
  { to: '/dashboard/jobs', label: 'Jobs', icon: Briefcase, testId: 'nav-jobs-link' },
  { to: '/dashboard/board', label: 'Shop Board', icon: LayoutGrid, testId: 'nav-shop-board-link' },
  { to: '/dashboard/tracker', label: 'In/Out Tracker', icon: ArrowLeftRight, testId: 'nav-in-out-link' },
  { to: '/dashboard/vendors', label: 'Vendors', icon: Factory, testId: 'nav-vendors-link' },
];

export default function Dashboard({ user, setUser }) {
  const navigate = useNavigate();

  const logout = async () => {
    try { await api.post('/auth/logout'); } catch (err) { console.error('Logout request failed', err); }
    localStorage.removeItem('session_token');
    setUser(null);
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen flex-col" data-testid="dashboard">
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-900/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1700px] items-center gap-6 px-4 py-3 sm:px-6">
          <NavLink to="/dashboard/jobs" className="flex items-center gap-2.5" data-testid="brand-link">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-amber-500 text-slate-950">
              <Hexagon size={20} strokeWidth={2.5} />
            </span>
            <span className="hidden flex-col leading-none sm:flex">
              <span className="font-display text-xl font-extrabold uppercase tracking-wide text-slate-50">ShopTrack</span>
              <span className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">Fabrication Ops</span>
            </span>
          </NavLink>

          <nav className="flex flex-1 items-center gap-1 overflow-x-auto" aria-label="Primary">
            {NAV.map(({ to, label, icon: Icon, testId }) => (
              <NavLink
                key={to}
                to={to}
                data-testid={testId}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold transition-colors',
                    isActive ? 'bg-amber-500/15 text-amber-400' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                  )
                }
              >
                <Icon size={16} />
                <span className="hidden md:inline">{label}</span>
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 lg:flex" data-testid="user-profile">
              <img src={user.picture} alt="" className="h-8 w-8 rounded-full border border-slate-700" />
              <span className="text-sm font-medium text-slate-300">{user.name}</span>
            </div>
            <button
              onClick={logout}
              data-testid="logout-button"
              className="flex items-center gap-1.5 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-400 transition-colors hover:border-red-500/50 hover:text-red-400"
            >
              <LogOut size={15} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1700px] flex-1 px-4 py-8 sm:px-6 lg:py-10">
        <Outlet />
      </main>
    </div>
  );
}
