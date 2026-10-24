import StatusBadge from "@/components/StatusBadge";
import type { ReviewStatus } from "@/lib/types";

// A clean automated review is pending until a human records approval.
export default function DisplayStatus({ status, findingCount }: { status: ReviewStatus; findingCount: number }) {
  if (status === "pending_approval") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-line bg-surface-2 px-2.5 py-0.5 text-xs font-semibold text-ink">
        ◷ Awaiting Human Approval
      </span>
    );
  }
  return <StatusBadge status={status} />;
}
