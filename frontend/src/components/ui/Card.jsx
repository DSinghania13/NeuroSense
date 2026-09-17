export default function Card({ children, className = '', noPadding = false }) {
  return (
    <div
      className={`rounded-lg border border-border bg-card shadow-sm ${
        noPadding ? '' : 'p-6 md:p-8'
      } ${className}`}
    >
      {children}
    </div>
  );
}
