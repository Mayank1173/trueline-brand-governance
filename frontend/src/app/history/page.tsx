"use client";
import { useEffect, useState } from "react";
import ActivityLog from "@/components/ActivityLog";
import RevisionHistory from "@/components/RevisionHistory";
import SampleDataNotice from "@/components/SampleDataNotice";
import DisplayStatus from "@/components/DisplayStatus";
import { apiGet, fetchReviews, isLive, type ReviewSummary } from "@/lib/api";
import { formatUtc } from "@/lib/format";
import { SAMPLE_DRAFTS, SAMPLE_REVISIONS } from "@/lib/mock/sampleData";
import type { ActivityEvent, ActorType } from "@/lib/workflowTypes";

interface Loaded {
  id: string;
  events: ActivityEvent[];
  error: string | null;
}

function toActor(v: unknown): ActorType {
  return v === "ai" || v === "system" ? v : "human";
}

function toEvents(raw: unknown): ActivityEvent[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((r, i) => {
    const e = (typeof r === "object" && r !== null ? r : {}) as Record<string, unknown>;
    return {
      id: typeof e.id === "string" ? e.id : `event-${i}`,
      actor_type: toActor(e.actor_type),
      actor: typeof e.actor === "string" ? e.actor : "Unknown",
      action: typeof e.action === "string" ? e.action : "",
      comment: typeof e.comment === "string" ? e.comment : undefined,
      at: typeof e.at === "string" ? e.at : "",
    };
  });
}

function LiveHistory() {
  const [reviews, setReviews] = useState<ReviewSummary[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [chosen, setChosen] = useState<string | null>(null);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [attempt, setAttempt] = useState(0);

  const selected = chosen ?? reviews?.[0]?.review_id ?? null;
  const current = reviews?.find((r) => r.review_id === selected) ?? null;
  const loading = selected !== null && loaded?.id !== selected;

  useEffect(() => {
    let cancelled = false;
    fetchReviews()
      .then((items) => {
        if (!cancelled) setReviews(items);
      })
      .catch((err) => {
        if (!cancelled) setListError(err instanceof Error ? err.message : "Couldn't load reviews.");
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    apiGet<{ events?: unknown }>(`/api/reviews/${selected}/history`)
      .then((d) => {
        if (!cancelled) setLoaded({ id: selected, events: toEvents(d.events), error: null });
      })
      .catch((err) => {
        if (!cancelled)
          setLoaded({ id: selected, events: [], error: err instanceof Error ? err.message : "Couldn't load history." });
      });
    return () => {
      cancelled = true;
    };
  }, [selected, attempt]);

  function retry() {
    setListError(null);
    setLoaded(null);
    setAttempt((a) => a + 1);
  }

  if (listError) {
    return (
      <div role="alert" className="rounded-xl border border-line bg-surface p-3 text-sm">
        <strong>Couldn’t load reviews.</strong> {listError}
        <div className="mt-2">
          <button
            type="button"
            onClick={retry}
            className="rounded-full border border-line px-4 py-1.5 text-sm font-medium hover:bg-surface-2"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (reviews === null) {
    return (
      <p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
        Loading reviews…
      </p>
    );
  }

  if (reviews.length === 0) {
    return (
      <p className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
        No reviews yet. Submit a draft on Draft Review and its audit trail will appear here.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="review-pick" className="block text-sm font-medium">Review</label>
        <select
          id="review-pick"
          value={selected ?? ""}
          onChange={(e) => setChosen(e.target.value)}
          className="mt-1 w-full rounded-xl border border-line bg-surface p-2.5 text-sm text-ink"
        >
          {reviews.map((r) => (
            <option key={r.review_id} value={r.review_id}>
              {formatUtc(r.created_at)} · {r.status} · {r.review_id}
            </option>
          ))}
        </select>
      </div>

      {current && (
        <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-surface p-4 text-sm">
          <DisplayStatus status={current.status} findingCount={current.finding_count} />
          <span>
            {current.finding_count} finding(s), {current.requires_human_review_count} need human review
          </span>
        </div>
      )}

      {loading && (
        <p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
          Loading audit events…
        </p>
      )}

      {!loading && loaded?.error && (
        <div role="alert" className="rounded-xl border border-line bg-surface p-3 text-sm">
          <strong>Couldn’t load the audit trail.</strong> {loaded.error}
          <div className="mt-2">
            <button
              type="button"
              onClick={retry}
              className="rounded-full border border-line px-4 py-1.5 text-sm font-medium hover:bg-surface-2"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {!loading && loaded && !loaded.error && <ActivityLog events={loaded.events} />}
    </div>
  );
}

export default function HistoryPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Revision history</h1>
        {!isLive && (
          <p className="mt-3 text-sm text-muted">
            Draft: <span className="font-semibold text-ink">{SAMPLE_DRAFTS[0].title}</span>
          </p>
        )}
      </div>

      {isLive ? (
        <LiveHistory />
      ) : (
        <>
          <SampleDataNotice>These are sample records, not a real audit trail.</SampleDataNotice>
          <RevisionHistory revisions={SAMPLE_REVISIONS} />
        </>
      )}
    </div>
  );
}