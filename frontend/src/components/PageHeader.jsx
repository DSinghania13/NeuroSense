export default function PageHeader({ title, description, actions }) {
  return (
    <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border bg-card px-8 lg:px-10 py-6 shadow-sm">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-black leading-tight tracking-tight text-text-primary">
          {title}
        </h1>
        {description && (
          <p className="text-base font-normal text-text-secondary leading-snug max-w-2xl">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  );
}
