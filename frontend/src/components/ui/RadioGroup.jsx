export default function RadioGroup({ label, options, value, onChange, className = '' }) {
  return (
    <div className={`flex flex-col ${className}`}>
      {label && (
        <p className="text-text-primary text-base font-bold leading-normal pb-2">{label}</p>
      )}
      <div className="flex flex-wrap gap-2 sm:gap-3">
        {options.map((opt) => {
          const isSelected = value === opt.value;
          return (
            <label
              key={opt.value}
              className={`text-base font-medium leading-normal flex items-center justify-center rounded-lg border px-4 h-12 text-text-primary relative cursor-pointer transition-all duration-200 ${
                isSelected ? 'border-2 border-primary bg-primary/10' : 'border-border'
              }`}
            >
              {opt.label}
              <input
                className="invisible absolute"
                name={label}
                type="radio"
                value={opt.value}
                checked={isSelected}
                onChange={() => onChange(opt.value)}
              />
            </label>
          );
        })}
      </div>
    </div>
  );
}
