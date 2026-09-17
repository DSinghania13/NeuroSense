export default function Button({
  children,
  variant = 'primary',
  icon,
  className = '',
  disabled = false,
  ...props
}) {
  // Base styles: perfectly centers text and icons, adds standardized padding, rounds the corners, and adds a smooth transition
  const baseStyles = "inline-flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-bold rounded-lg transition-all duration-200 focus:outline-none active:scale-[0.98]";

  // Variant styles: handles the colors for 'primary' (blue) and 'outline' (white/gray border)
  const variants = {
    primary: "bg-primary text-white hover:bg-opacity-90 shadow-sm border border-transparent",
    outline: "bg-transparent border-2 border-border text-text-primary hover:border-primary hover:text-primary"
  };

  // Disabled styles: dims the button and changes the cursor so it's obvious it can't be clicked
  const disabledStyles = disabled ? "opacity-50 cursor-not-allowed hover:bg-primary hover:border-border" : "cursor-pointer";

  return (
    <button
      disabled={disabled}
      className={`${baseStyles} ${variants[variant]} ${disabledStyles} ${className}`}
      {...props}
    >
      {icon && (
        <span className="material-symbols-outlined text-[20px]">
          {icon}
        </span>
      )}
      <span>{children}</span>
    </button>
  );
}