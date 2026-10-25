"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import EmptyState from "@/components/EmptyState";
import SampleDataNotice from "@/components/SampleDataNotice";
import StatusBadge from "@/components/StatusBadge";
import { fetchReviews, isLive, type ReviewSummary } from "@/lib/api";
import { formatUtc } from "@/lib/format";
import { SAMPLE_DRAFTS } from "@/lib/mock/sampleData";
import type { ReviewStatus } from "@/lib/types";

const statuses: ReviewStatus[] = ["draft", "in_review", "changes_requested", "needs_human_review", "pending_approval", "approved", "rejected"];

export default function DashboardPage() {
  const [reviews, setReviews] = useState<ReviewSummary[] | null>(isLive ? null : []);
  const [error, setError] = useState<string | null>(null);
  const usingSample = !isLive || error !== null;

  useEffect(() => {
    if (!isLive) return;
    fetchReviews()
      .then(setReviews)
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Couldn't load reviews.");
        setReviews([]);
      });
  }, []);

  const sampleRows = SAMPLE_DRAFTS;
  const liveRows = reviews ?? [];
  const rows = usingSample
    ? sampleRows.map((row) => ({ id: row.id, title: row.title, status: row.status, updated_at: row.updated_at }))
    : liveRows.map((row) => ({ id: row.review_id, title: `Review #${row.review_id.slice(-8)}`, status: row.status, updated_at: row.updated_at }));
  const count = (status: ReviewStatus) => rows.filter((row) => row.status === status).length;

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div>
        <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl">
          Welcome <span className="text-maroon-soft">back.</span>
        </h1>
        <p className="mt-3 text-sm text-muted">Workspace: <span className="font-semibold text-ink">Trueline</span></p>
        <Link href="/review" className="mt-5 inline-block rounded-full bg-maroon px-6 py-3 text-sm font-semibold text-white hover:bg-maroon-hover">
          Review new content →
        </Link>
      </div>

      {usingSample && <SampleDataNotice>{isLive ? "Live reviews could not be loaded; showing labelled sample data." : "Counts and drafts below come from a sample list, not from real reviews."}</SampleDataNotice>}
      {error && <p role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm"><strong>Couldn’t load live reviews.</strong> {error}</p>}
      {reviews === null ? (
        <p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">Loading reviews…</p>
      ) : (
        <>
          <section aria-labelledby="counts-heading">
            <h2 id="counts-heading" className="text-lg font-semibold">Review status</h2>
            <ul className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
              {statuses.map((status) => <li key={status} className="rounded-2xl border border-line bg-surface p-4"><StatusBadge status={status} /><p className="mt-3 text-3xl font-bold">{count(status)}</p></li>)}
            </ul>
          </section>
          <section aria-labelledby="recent-heading">
            <h2 id="recent-heading" className="text-lg font-semibold">Recent reviews</h2>
            {rows.length === 0 ? <div className="mt-3"><EmptyState title="No reviews yet" description="Submit your first draft to see it here." /></div> : (
              <ul className="mt-3 space-y-3">{rows.map((row) => <li key={row.id} className="rounded-2xl border border-line bg-surface p-4"><div className="flex flex-wrap items-center gap-3"><p className="font-semibold">{row.title}</p><StatusBadge status={row.status} /></div><p className="mt-2 text-xs text-muted">Updated {formatUtc(row.updated_at)}</p></li>)}</ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}
