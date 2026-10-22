import type { ActivityEvent } from "@/lib/workflowTypes";
import { formatUtc } from "@/lib/format";

export default function ActivityLog({ events }: { events: ActivityEvent[] }) {
  if (events.length === 0) {
    return <p className="text-sm text-muted">No activity recorded yet.</p>;
  }
  return (
    <ul className="space-y-3">
      {events.map((e) => (
        <li key={e.id} className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                e.actor_type === "ai" ? "border-line text-muted" : "border-maroon-soft bg-maroon text-white"
              }`}
            >
              {e.actor_type === "ai" ? "◇ AI recommendation" : "● Human decision"}
            </span>
            <span className="font-medium text-ink">{e.actor}</span>
            <span className="text-xs text-muted">{formatUtc(e.at)}</span>
          </div>
          <p className="mt-2 text-ink">{e.action}</p>
          {e.comment && <p className="mt-1 text-muted">“{e.comment}”</p>}
        </li>
      ))}
    </ul>
  );
}