import type { ReviewStatus } from "@/lib/types";

const MAP: Record<ReviewStatus, { label: string; icon: string; cls: string }> = {
  draft: { label: "Draft", icon: "✎", cls: "border-line bg-surface-2 text-ink" },
  in_review: { label: "In Review", icon: "◷", cls: "border-ink/50 bg-surface-2 text-ink" },
  changes_requested: { label: "Changes Requested", icon: "!", cls: "border-maroon-soft bg-maroon/30 text-maroon-soft" },
  approved: { label: "Approved", icon: "✓", cls: "border-cream bg-cream text-black" },
};

export default function StatusBadge({ status }: { status: ReviewStatus }) {
  const s = MAP[status];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-0.5 text-xs font-semibold ${s.cls}`}>
      <span aria-hidden="true">{s.icon}</span>
      {s.label}
    </span>
  );
}