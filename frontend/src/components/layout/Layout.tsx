import { Outlet, Navigate } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import AIChat from '../chat/AIChat';
import { useDatasetStore } from '../../store/datasetStore';

export default function Layout() {
  const { profile } = useDatasetStore();

  if (!profile) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
      <AIChat />
    </div>
  );
}
