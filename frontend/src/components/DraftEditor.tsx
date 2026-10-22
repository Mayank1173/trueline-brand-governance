interface Props {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}

export default function DraftEditor({ value, onChange, disabled }: Props) {
  return (
    <div>
      <label htmlFor="draft" className="block text-sm font-medium text-ink">
        Draft text
      </label>
      <textarea
        id="draft"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        rows={10}
        placeholder="Paste your marketing draft here…"
        className="mt-1 w-full rounded-xl border border-line bg-surface p-3 text-sm text-ink placeholder:text-muted disabled:opacity-60"
      />
    </div>
  );
}