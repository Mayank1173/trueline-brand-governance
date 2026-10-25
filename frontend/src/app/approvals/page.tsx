"use client";

import { useEffect, useState } from "react";
import ActivityLog from "@/components/ActivityLog";
import ApprovalActions, { type Decision } from "@/components/ApprovalActions";
import DisplayStatus from "@/components/DisplayStatus";
import { apiGet, fetchReviews, isLive, type ReviewSummary } from "@/lib/api";
import { submitDecision } from "@/lib/decisionService";
import { formatUtc } from "@/lib/format";
import { canRecordDecision } from "@/lib/reviewStatus";
import type { ActivityEvent, ActorType } from "@/lib/workflowTypes";

function toActorType(value: unknown): ActorType {
  return value === "ai" || value === "system" ? value : "human";
}

function toEvents(raw: unknown): ActivityEvent[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item, index) => {
    const value = (typeof item === "object" && item !== null ? item : {}) as Record<string, unknown>;
    return {
      id: typeof value.id === "string" ? value.id : `event-${index}`,
      actor_type: toActorType(value.actor_type),
      actor: typeof value.actor === "string" ? value.actor : "Unknown",
      action: typeof value.action === "string" ? value.action : "",
      comment: typeof value.comment === "string" ? value.comment : undefined,
      at: typeof value.at === "string" ? value.at : "",
    };
  });
}

export default function ApprovalsPage() {
  const [reviews, setReviews] = useState<ReviewSummary[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [reviewer, setReviewer] = useState("Frontend reviewer");
  const [loading, setLoading] = useState(isLive);
  const [listError, setListError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const selected = reviews?.find((review) => review.review_id === selectedId) ?? null;

  async function loadReviews() {
    const items = await fetchReviews();
    setReviews(items);
    setListError(null);
    setSelectedId((current) => current && items.some((item) => item.review_id === current)
      ? current
      : items[0]?.review_id ?? null);
  }

  async function loadHistory(reviewId: string) {
    const data = await apiGet<{ events?: unknown }>(`/api/reviews/${encodeURIComponent(reviewId)}/history`);
    setEvents(toEvents(data.events));
  }

  useEffect(() => {
    if (!isLive) return;
    let cancelled = false;
    void Promise.resolve().then(() => loadReviews())
      .catch((error) => {
        if (!cancelled) setListError(error instanceof Error ? error.message : "Couldn’t load reviews.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!isLive || !selectedId) return;
    let cancelled = false;
    void Promise.resolve().then(() => loadHistory(selectedId)).catch((error) => {
      if (!cancelled) {
        setEvents([]);
        setHistoryError(error instanceof Error ? error.message : "Couldn’t load review history.");
      }
    });
    return () => { cancelled = true; };
  }, [selectedId]);

  async function handleDecide(decision: Decision, comment: string) {
    if (!selected || !reviewer.trim()) {
      throw new Error("Enter a reviewer name before recording a decision.");
    }
    const result = await submitDecision(selected.review_id, decision, comment, reviewer.trim());
    setReviews((current) => current?.map((item) => item.review_id === selected.review_id
      ? { ...item, status: result.status, updated_at: result.decision_event.at }
      : item) ?? null);
    setHistoryError(null);
    try {
      await loadHistory(selected.review_id);
    } catch (error) {
      setHistoryError(error instanceof Error ? error.message : "Decision saved, but history could not be refreshed.");
    }
    try {
      await loadReviews();
    } catch (error) {
      setListError(error instanceof Error ? error.message : "Decision saved, but the review list could not be refreshed.");
    }
  }

  const systemEvents = events.filter((event) => event.actor_type !== "human");
  const humanEvents = events.filter((event) => event.actor_type === "human");

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Approval workflow</h1>
        <p className="mt-3 text-sm text-muted">AI recommends. Only a human reviewer decides.</p>
      </div>

      <p className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
        Reviewer identity is caller-supplied. The backend does not currently authenticate or authorize reviewers.
      </p>
      {listError && <p role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm">{listError}</p>}
      {!isLive && (
        <p className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
          Approvals require the live backend. Mock mode does not record decisions.
        </p>
      )}
      {loading && <p role="status" className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">Loading persisted reviews…</p>}

      {!loading && isLive && reviews?.length === 0 && (
        <p className="rounded-2xl border border-line bg-surface p-5 text-sm text-muted">No persisted reviews are available.</p>
      )}

      {!loading && selected && (
        <>
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="space-y-4 rounded-2xl border border-line bg-surface p-5" aria-labelledby="review-heading">
              <h2 id="review-heading" className="text-lg font-semibold">Persisted review</h2>
              <label htmlFor="review-pick" className="block text-sm font-medium">Review</label>
              <select id="review-pick" value={selectedId ?? ""} onChange={(event) => {
                setSelectedId(event.target.value);
                setEvents([]);
                setHistoryError(null);
              }} className="w-full rounded-xl border border-line bg-surface p-2.5 text-sm text-ink">
                {reviews?.map((review) => (
                  <option key={review.review_id} value={review.review_id}>
                    {formatUtc(review.created_at)} · {review.status} · {review.review_id}
                  </option>
                ))}
              </select>
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <DisplayStatus status={selected.status} findingCount={selected.finding_count} />
                <span>{selected.finding_count} finding(s)</span>
              </div>
              <p className="break-all text-xs text-muted">Review ID: {selected.review_id}</p>
              <p className="text-xs text-muted">Purpose: {selected.purpose || "general"}</p>
            </section>

            <section className="space-y-4 rounded-2xl border border-line bg-surface p-5" aria-labelledby="decision-heading">
              <h2 id="decision-heading" className="text-lg font-semibold">Human decision</h2>
              <div>
                <label htmlFor="reviewer" className="block text-sm font-medium">Reviewer label</label>
                <input id="reviewer" value={reviewer} onChange={(event) => setReviewer(event.target.value)} className="mt-1 w-full rounded-xl border border-line bg-surface p-2.5 text-sm text-ink" />
              </div>
              <ApprovalActions canReview={canRecordDecision(selected.status)} onDecide={handleDecide} />
            </section>
          </div>

          <section className="rounded-2xl border border-line bg-surface p-5" aria-labelledby="history-heading">
            <h2 id="history-heading" className="text-lg font-semibold">Persisted review history</h2>
            {historyError && <p role="alert" className="mt-3 rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm">{historyError}</p>}
            <div className="mt-4 grid gap-6 lg:grid-cols-2">
              <div><h3 className="text-sm font-semibold">System events</h3><div className="mt-3"><ActivityLog events={systemEvents} /></div></div>
              <div><h3 className="text-sm font-semibold">Reviewer decisions</h3><div className="mt-3"><ActivityLog events={humanEvents} /></div></div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
