import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import SampleDataNotice from "@/components/SampleDataNotice";
import StatusBadge from "@/components/StatusBadge";
import { formatUtc } from "@/lib/format";
import { SAMPLE_DRAFTS } from "@/lib/mock/sampleData";
import type { ReviewStatus } from "@/lib/types";

const STATUSES: ReviewStatus[] = ["draft", "in_review", "changes_requested", "approved"];

export default function DashboardPage() {
  const drafts = SAMPLE_DRAFTS;
  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl">
          Welcome <span className="text-maroon-soft">back.</span>
        </h1>
        <p className="mt-3 text-sm text-muted">
          Workspace: <span className="font-semibold text-ink">Sample Brand (mock)</span>
        </p>
        <Link
          href="/review"
          className="mt-5 inline-block rounded-full bg-maroon px-6 py-3 text-sm font-semibold text-white hover:bg-maroon-hover"
        >
          Review new content →
        </Link>
      </div>

      <SampleDataNotice>Counts and drafts below come from a sample list, not from real reviews.</SampleDataNotice>

      <section aria-labelledby="counts-heading">
        <h2 id="counts-heading" className="text-lg font-semibold">Review status</h2>
        <ul className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
          {STATUSES.map((s) => (
            <li key={s} className="rounded-2xl border border-line bg-surface p-4">
              <StatusBadge status={s} />
              <p className="mt-3 text-3xl font-bold">{drafts.filter((d) => d.status === s).length}</p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="recent-heading">
        <h2 id="recent-heading" className="text-lg font-semibold">Recent draft reviews</h2>
        {drafts.length === 0 ? (
          <div className="mt-3">
            <EmptyState title="No reviews yet" description="Submit your first draft to see it here." />
          </div>
        ) : (
          <ul className="mt-3 space-y-3">
            {drafts.map((d) => (
              <li key={d.id} className="rounded-2xl border border-line bg-surface p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <p className="font-semibold">{d.title}</p>
                  <StatusBadge status={d.status} />
                </div>
                <p className="mt-2 text-xs text-muted">
                  Version {d.version} · Updated {formatUtc(d.updated_at)} · {d.open_findings} open finding(s)
                </p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}