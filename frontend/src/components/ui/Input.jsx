export default function Input({ id, label, icon, type = "text", wrapperClassName = "", className = "", ...props }) {
  return (
    <div className={`flex flex-col gap-1.5 ${wrapperClassName}`}>
      {label && (
        <label htmlFor={id} className="text-sm font-bold text-text-primary">
          {label}
        </label>
      )}

      {/* The relative wrapper MUST have flex and items-center if you use absolute icons */}
      <div className="relative flex items-center">

        {/* The Icon */}
        {icon && (
          <span className="material-symbols-outlined absolute left-3 text-text-secondary pointer-events-none">
            {icon}
          </span>
        )}

        {/* The Input Field */}
        <input
          id={id}
          type={type}
          // Notice: py-3 (even vertical padding) prevents the cursor from sitting too low
          className={`w-full rounded-lg border border-border bg-background py-3 text-text-primary focus:ring-2 focus:ring-primary outline-none transition-all ${
            icon ? 'pl-10' : 'pl-3'
          } pr-3 ${className}`}
          {...props}
        />
      </div>
    </div>
  );
}