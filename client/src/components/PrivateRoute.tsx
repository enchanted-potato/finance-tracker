import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function PrivateRoute({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  // CRITICAL: check loading FIRST — Firebase restores auth from IndexedDB asynchronously.
  // Checking user before loading=false would redirect authenticated users on every refresh.
  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}
