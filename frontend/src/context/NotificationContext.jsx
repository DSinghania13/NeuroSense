import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const NotificationContext = createContext();

export function NotificationProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const [browserEnabled, setBrowserEnabled] = useState(
    localStorage.getItem('notify_browser') === 'true'
  );

  const notify = useCallback((title, message, type = 'info') => {
    const id = Date.now() + Math.random(); // Ensure unique IDs
    setToasts(prev => [...prev, { id, title, message, type }]);

    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);

    if (browserEnabled && 'Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: '/favicon.ico'
      });
    }
  }, [browserEnabled]);

  // ==========================================
  // NEW: GLOBAL ERROR INTERCEPTORS
  // ==========================================
  useEffect(() => {
    // 1. Catch Standard JavaScript Runtime Errors
    const handleGlobalError = (event) => {
      if (event.message === "Script error.") return; // Ignore useless cross-origin browser extension errors
      notify("System Error", event.message || "An unexpected JavaScript error occurred.", "error");
    };

    // 2. Catch Async/API Promise Failures
    const handleUnhandledRejection = (event) => {
      const message = event.reason?.message || event.reason || "A background process or API call failed.";
      notify("Background Error", message, "error");
    };

    // 3. Catch React UI Render Crashes (Dispatched from ErrorBoundary)
    const handleReactError = (event) => {
      notify("UI Crash Prevented", event.detail || "A component failed to render on the screen.", "error");
    };

    // Attach listeners to the browser window
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('react-render-error', handleReactError);

    // Cleanup
    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('react-render-error', handleReactError);
    };
  }, [notify]);

  return (
    <NotificationContext.Provider value={{ notify, browserEnabled, setBrowserEnabled }}>
      {children}

      {/* GLOBAL TOAST CONTAINER */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`pointer-events-auto p-4 rounded-xl shadow-2xl border flex items-start gap-3 w-80 transform transition-all duration-300 bg-white ${
              toast.type === 'success' ? 'border-green-500 shadow-green-500/20' : 
              toast.type === 'error' ? 'border-red-500 shadow-red-500/20' : 
              'border-primary shadow-primary/20'
            }`}
          >
            <span className={`material-symbols-outlined mt-0.5 ${
              toast.type === 'success' ? 'text-green-500' : 
              toast.type === 'error' ? 'text-red-500' : 
              'text-primary'
            }`}>
              {toast.type === 'success' ? 'check_circle' : toast.type === 'error' ? 'error' : 'info'}
            </span>
            <div>
              <h4 className="text-sm font-bold text-gray-900">{toast.title}</h4>
              <p className="text-xs text-gray-600 mt-1 leading-relaxed break-words">{toast.message}</p>
            </div>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}

export const useNotification = () => useContext(NotificationContext);