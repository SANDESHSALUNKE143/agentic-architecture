import { useEffect, useId, useRef, useState } from "react";

export type Option = { value: string; label: string };

type TextProps = {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  autoComplete?: string;
  autoFocus?: boolean;
  className?: string;
  name?: string;
  disabled?: boolean;
  type?: string;
  "aria-label"?: string;
};

export function TextField({ label, value, onChange, placeholder, autoComplete, autoFocus, className, name, disabled, type = "text", "aria-label": ariaLabel }: TextProps) {
  const input = (
    <input
      className={className}
      type={type}
      name={name}
      value={value}
      placeholder={placeholder}
      autoComplete={autoComplete}
      autoFocus={autoFocus}
      disabled={disabled}
      aria-label={label ? undefined : ariaLabel}
      onChange={(event) => onChange(event.target.value)}
    />
  );
  if (!label) return input;
  return (
    <label className="ui-field">
      <span>{label}</span>
      {input}
    </label>
  );
}

export function TextArea({
  label,
  value,
  onChange,
  placeholder,
  className,
  "aria-label": ariaLabel,
}: {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
}) {
  const area = (
    <textarea
      className={className}
      value={value}
      placeholder={placeholder}
      aria-label={label ? undefined : ariaLabel}
      onChange={(event) => onChange(event.target.value)}
    />
  );
  if (!label) return area;
  return (
    <label className="ui-field">
      <span>{label}</span>
      {area}
    </label>
  );
}

export function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="ui-field ui-number">
      <span>{label}</span>
      <input type="number" value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

export function Checkbox({ label, checked, onChange, disabled }: { label: string; checked: boolean; onChange?: (checked: boolean) => void; disabled?: boolean }) {
  return (
    <label className="ui-check">
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange?.(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

export function RadioGroup({ name, value, options, onChange }: { name: string; value: string; options: Option[]; onChange: (value: string) => void }) {
  return (
    <div className="ui-radios" role="radiogroup">
      {options.map((option) => (
        <label key={option.value} className="ui-check">
          <input type="radio" name={name} checked={value === option.value} onChange={() => onChange(option.value)} />
          <span>{option.label}</span>
        </label>
      ))}
    </div>
  );
}

export function Select({ label, value, onChange, options, placeholder = "Choose", hint }: { label?: string; value: string; onChange: (value: string) => void; options: Option[]; placeholder?: string; hint?: string }) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const labelId = useId();
  const current = options.find((option) => option.value === value);

  useEffect(() => {
    if (!open) return;
    function outside(event: MouseEvent) {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", outside);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", outside);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const control = (
    <div className="ui-select" ref={root}>
      <button type="button" className="ui-select-trigger" aria-haspopup="listbox" aria-expanded={open} aria-labelledby={label ? labelId : undefined} onClick={() => setOpen((currentOpen: boolean) => !currentOpen)}>
        <span>{current?.label || placeholder}</span>
        <svg className="ui-chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" /></svg>
      </button>
      {open ? (
        <div className="ui-menu" role="listbox" aria-labelledby={label ? labelId : undefined}>
          {options.map((option) => (
            <button key={option.value} type="button" role="option" aria-selected={option.value === value} className="ui-option" onClick={() => { onChange(option.value); setOpen(false); }}>
              <span>{option.label}</span>
              <span className="ui-mark" aria-hidden="true" />
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );

  return (
    <div className="ui-field">
      {label ? <span id={labelId}>{label}</span> : null}
      {control}
      {hint ? <span className="muted">{hint}</span> : null}
    </div>
  );
}
