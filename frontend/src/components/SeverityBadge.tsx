import type { Severity } from "@/lib/types";

const MAP: Record<Severity, { label: string; icon: string; cls: string }> = {
  low: { label: "Low severity", icon: "▽", cls: "border-line bg-surface-2 text-muted" },
  medium: { label: "Medium severity", icon: "◆", cls: "border-ink/60 text-ink" },
  high: { label: "High severity", icon: "▲", cls: "border-maroon-soft bg-maroon text-white" },
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  const s = MAP[severity];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${s.cls}`}>
      <span aria-hidden="true">{s.icon}</span>
      {s.label}
    </span>
  );
}