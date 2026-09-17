import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ROUTES } from '../constants/routes';

// 1. The Loading Screen (Checking server connection)
function LoadingScreen({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)] text-center p-8">
      <span className="material-symbols-outlined text-6xl text-text-secondary animate-spin mb-4">
        autorenew
      </span>
      <h2 className="text-2xl font-bold text-text-primary">{message}</h2>
    </div>
  );
}

// 2. The Locked Screen (Server is actively loading models)
function LockedScreen({ message }) {
  return (
    <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)] text-center p-8">
      <span className="material-symbols-outlined text-6xl text-primary animate-pulse mb-4">
        psychology
      </span>
      <h2 className="text-2xl font-bold text-text-primary">{message}</h2>
      <p className="text-text-secondary mt-2">The AI models are currently loading into memory. This usually takes 5-10 seconds.</p>
    </div>
  );
}

// 3. The Main Guard Component
export default function SystemGuard({ children }) {
  const navigate = useNavigate();
  const location = useLocation();

  // -- STATE: Health Polling --
  const [isReady, setIsReady] = useState(false);
  const [checking, setChecking] = useState(true);

  // ==========================================
  // EFFECT 1: HEALTH POLLING
  // ==========================================
  useEffect(() => {
    const checkHealth = () => {
      fetch('/api/health')
        .then(res => {
          if (!res.ok) throw new Error("Backend not responding");
          return res.json();
        })
        .then(data => {
          if (data.ready) {
            setIsReady(true);
            setChecking(false);
          } else {
            // Models are still loading. Check again in 2 seconds!
            setChecking(false);
            setTimeout(checkHealth, 2000);
          }
        })
        .catch(err => {
          console.error("Health check failed. Retrying...", err);
          // If the server isn't even up yet, keep trying
          setTimeout(checkHealth, 2000);
        });
    };

    // Start the first check
    checkHealth();
  }, []);

  // ==========================================
  // EFFECT 2: BROWSER LOCK (PREVENT ACCIDENTAL BACK/REFRESH)
  // ==========================================
  useEffect(() => {
    // 1. Prevent accidental page reloads (F5) or closing the tab
    const handleBeforeUnload = (e) => {
      e.preventDefault();
      e.returnValue = "You are in the middle of a diagnostic session. Progress will be lost if you leave.";
    };
    window.addEventListener('beforeunload', handleBeforeUnload);

    // 2. Trap the Browser Back Button
    // Push a dummy state so the first "Back" click just eats this state and triggers our trap
    window.history.pushState(null, null, window.location.pathname);

    const handlePopState = () => {
      const confirmLeave = window.confirm(
        "⚠️ WARNING: Navigating back will abort the current diagnostic sequence. Are you sure you want to leave? Data may be lost."
      );

      if (!confirmLeave) {
        // They clicked Cancel -> Push the dummy state again to reset the trap!
        window.history.pushState(null, null, window.location.pathname);
      } else {
        // They clicked OK -> Boot them to the Dashboard safely
        navigate(ROUTES.DASHBOARD, { replace: true });
      }
    };

    window.addEventListener('popstate', handlePopState);

    // Cleanup when the test naturally finishes and moves to the next one
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };
  }, [navigate, location.pathname]);

  // ==========================================
  // RENDER LOGIC
  // ==========================================
  if (checking) return <LoadingScreen message="Connecting to NeuroSense AI..." />;
  if (!isReady) return <LockedScreen message="System is initializing models" />;

  // If we make it here, the backend is ready and the browser is locked! Render the actual test page.
  return children;
}