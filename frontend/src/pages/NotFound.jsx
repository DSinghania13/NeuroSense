import { Link } from 'react-router-dom';
import { ROUTES } from '../constants/routes';
import Button from '../components/ui/Button';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-center px-4">
      <h1 className="text-9xl font-black text-primary/20">404</h1>
      <h2 className="text-2xl font-bold text-text-primary mt-4 mb-2">Page Not Found</h2>
      <p className="text-text-secondary mb-8 max-w-md">
        The page you are looking for might have been removed, had its name changed, or is
        temporarily unavailable.
      </p>
      <Link to={ROUTES.DASHBOARD} className="no-underline">
        <Button icon="home" className="h-12 px-6">
          Return to Dashboard
        </Button>
      </Link>
    </div>
  );
}
