"use client";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import EmptyState from "@/components/EmptyState";
import SampleDataNotice from "@/components/SampleDataNotice";
import StatusBadge from "@/components/StatusBadge";
import { fetchReviews, isLive } from "@/lib/api";
import { formatUtc } from "@/lib/format";
import { SAMPLE_DRAFTS } from "@/lib/mock/sampleData";
import type { ReviewStatus } from "@/lib/types";

interface Row {
  id: string;
  title: string;
  status: ReviewStatus;
  meta: string;
}

const SAMPLE_STATUSES: ReviewStatus[] = ["draft", "in_review", "changes_requested", "approved"];
const LIVE_STATUSES: ReviewStatus[] = ["needs_human_review", "changes_requested", "approved"];

const sampleRows: Row[] = SAMPLE_DRAFTS.map((d) => ({
  id: d.id,
  title: d.title,
  status: d.status,
  meta: `Version ${d.version} · Updated ${formatUtc(d.updated_at)} · ${d.open_findings} open finding(s)`,
}));

export default function DashboardPage() {
  const [rows, setRows] = useState<Row[] | null>(isLive ? null : sampleRows);
  const [usingSample, setUsingSample] = useState(!isLive);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLive) return;
    let cancelled = false;
    fetchReviews()
      .then((items) => {
        if (cancelled) return;
        setRows(
          items.map((r) => ({
            id: r.review_id,
            title: r.purpose || "Review",
            status: r.status,
            meta: `${r.finding_count} finding(s), ${r.requires_human_review_count} need human review · Updated ${formatUtc(r.updated_at)} · ${r.review_id}`,
          }))
        );
        setUsingSample(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Couldn't load reviews.");
        setRows(sampleRows);
        setUsingSample(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const statuses = usingSample ? SAMPLE_STATUSES : LIVE_STATUSES;

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="grid items-center gap-6 md:grid-cols-2">
        <div>
          <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl">
            Welcome <span className="text-maroon-soft">back.</span>
          </h1>
          <p className="mt-3 text-sm text-muted">
            Workspace: <span className="font-semibold text-ink">Sample Brand</span>
          </p>
          <Link
            href="/review"
            className="mt-5 inline-block rounded-full bg-maroon px-6 py-3 text-sm font-semibold text-white hover:bg-maroon-hover"
          >
            Review new content →
          </Link>
        </div>
        <Image
          src="/images/hero-review.png"
          alt="Illustration of a magnifying glass examining one of several pricing documents"
          width={1348}
          height={741}
          priority
          className="h-auto w-full rounded-2xl border border-line"
        />
      </div>

      {usingSample && (
        <SampleDataNotice>Counts and drafts below come from a sample list, not from real reviews.</SampleDataNotice>
      )}
      {error && (
        <div role="alert" className="rounded-xl border border-line bg-surface p-3 text-sm">
          <strong>Couldn’t load live reviews.</strong> {error} Showing sample data instead.
        </div>
      )}

      {rows === null ? (
        <p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
          Loading reviews…
        </p>
      ) : (
        <>
          <section aria-labelledby="counts-heading">
            <h2 id="counts-heading" className="text-lg font-semibold">Review status</h2>
            <ul className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
              {statuses.map((s) => (
                <li key={s} className="rounded-2xl border border-line bg-surface p-4">
                  <StatusBadge status={s} />
                  <p className="mt-3 text-3xl font-bold">{rows.filter((r) => r.status === s).length}</p>
                </li>
              ))}
            </ul>
          </section>

          <section aria-labelledby="recent-heading">
            <h2 id="recent-heading" className="text-lg font-semibold">Recent draft reviews</h2>
            {rows.length === 0 ? (
              <div className="mt-3">
                <EmptyState title="No reviews yet" description="Submit your first draft to see it here." />
              </div>
            ) : (
              <ul className="mt-3 space-y-3">
                {rows.map((r) => (
                  <li key={r.id} className="rounded-2xl border border-line bg-surface p-4">
                    <div className="flex flex-wrap items-center gap-3">
                      <p className="font-semibold">{r.title}</p>
                      <StatusBadge status={r.status} />
                    </div>
                    <p className="mt-2 break-all text-xs text-muted">{r.meta}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  );
}