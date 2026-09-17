import React from 'react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render shows the fallback UI.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Dispatch a custom event to the window so the NotificationContext can pick it up!
    const errorMessage = error?.message || "Unknown rendering error.";
    window.dispatchEvent(new CustomEvent('react-render-error', { detail: errorMessage }));

    // Log to console for debugging purposes
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI to show instead of the White Screen of Death
      return (
        <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 p-10 h-full w-full min-h-[400px]">
          <span className="material-symbols-outlined text-6xl text-red-500 mb-4 animate-pulse">warning</span>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Display Error Prevented</h2>
          <p className="text-gray-600 mb-6 max-w-md text-center">
            A part of the user interface crashed. We intercepted the error to prevent the whole app from freezing.
            The details have been logged in the notification panel.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 transition-colors shadow-md"
          >
            Reload Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}