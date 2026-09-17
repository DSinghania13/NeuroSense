import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../constants/routes';

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Wait for AuthContext to finish scanning localStorage before making decisions
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <span className="material-symbols-outlined text-4xl text-primary animate-spin">
          autorenew
        </span>
      </div>
    );
  }

  // If no user object exists in MongoDB or state, boot them back to the login screen
  if (!user) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  // If authenticated, render the children layout smoothly
  return <Outlet />;
}