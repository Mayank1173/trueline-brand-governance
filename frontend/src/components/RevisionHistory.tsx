import type { Revision } from "@/lib/workflowTypes";
import { formatUtc } from "@/lib/format";
import ActivityLog from "./ActivityLog";
import EmptyState from "./EmptyState";
import StatusBadge from "./StatusBadge";

export default function RevisionHistory({ revisions }: { revisions: Revision[] }) {
  if (revisions.length === 0) {
    return (
      <EmptyState
        title="No revisions yet"
        description="Once a draft is submitted for review, each version will appear here."
      />
    );
  }
  return (
    <ol className="space-y-4">
      {revisions.map((r) => (
        <li key={r.id} className="rounded-2xl border border-line bg-surface p-5">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-base font-semibold">Revision {r.number}</h3>
            <StatusBadge status={r.status} />
            <span className="text-xs text-muted">Submitted {formatUtc(r.submitted_at)}</span>
            <span className="text-xs text-muted">ID: {r.id}</span>
          </div>
          <p className="mt-3 text-sm text-ink">{r.summary}</p>
          <details className="mt-3">
            <summary className="cursor-pointer text-sm font-medium">Reviewer and AI activity ({r.events.length})</summary>
            <div className="mt-3">
              <ActivityLog events={r.events} />
            </div>
          </details>
        </li>
      ))}
    </ol>
  );
}