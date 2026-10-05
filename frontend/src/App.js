import { useEffect, useState } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { api } from '@/lib/api';
import LoginPage from '@/pages/LoginPage';
import Dashboard from '@/pages/Dashboard';
import JobsPage from '@/pages/JobsPage';
import JobDetailPage from '@/pages/JobDetailPage';
import ShopBoardPage from '@/pages/ShopBoardPage';
import TrackerPage from '@/pages/TrackerPage';
import VendorsPage from '@/pages/VendorsPage';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('session_token');
    if (!token) return setLoading(false);
    api.get('/auth/me')
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem('session_token'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
      </div>
    );
  }

  const guard = (el) => (user ? el : <Navigate to="/login" replace />);

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={user ? <Navigate to="/dashboard/jobs" replace /> : <LoginPage setUser={setUser} />} />
          <Route path="/board" element={guard(<ShopBoardPage tv />)} />
          <Route path="/dashboard" element={guard(<Dashboard user={user} setUser={setUser} />)}>
            <Route index element={<Navigate to="/dashboard/jobs" replace />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route path="jobs/:jobId" element={<JobDetailPage />} />
            <Route path="board" element={<ShopBoardPage />} />
            <Route path="tracker" element={<TrackerPage />} />
            <Route path="vendors" element={<VendorsPage />} />
          </Route>
          <Route path="*" element={<Navigate to={user ? '/dashboard/jobs' : '/login'} replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="top-right" richColors />
    </div>
  );
}

export default App;
