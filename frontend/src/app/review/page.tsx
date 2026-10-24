"use client";
import { useState } from "react";
import AiStatusNotice from "@/components/AiStatusNotice";
import DisplayStatus from "@/components/DisplayStatus";
import DraftEditor from "@/components/DraftEditor";
import FindingCard, { type FindingState } from "@/components/FindingCard";
import { brands, submitReview } from "@/lib/reviewService";
import type { Finding, ReviewResponse } from "@/lib/types";
import { applySuggestedFix } from "@/lib/applyFix";

const field = "mt-1 w-full rounded-xl border border-line bg-surface p-2.5 text-sm text-ink placeholder:text-muted";

export default function ReviewPage() {
  const [brandId, setBrandId] = useState(brands[0].id);
  const [purpose, setPurpose] = useState("");
  const [draft, setDraft] = useState("");
  const [originalDraft, setOriginalDraft] = useState<string | null>(null);
  const [reviewedText, setReviewedText] = useState<string | null>(null);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [states, setStates] = useState<Record<string, FindingState>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const stale = result !== null && reviewedText !== draft;
  const openCount = result ? result.findings.filter((f) => states[f.id] === "open").length : 0;

  async function runReview() {
    if (!draft.trim()) {
      setError("Paste or type a draft before submitting.");
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const res = await submitReview({ brand_id: brandId, draft_text: draft, purpose });
      setResult(res);
      setStates(Object.fromEntries(res.findings.map((f) => [f.id, "open" as FindingState])));
      setReviewedText(draft);
      if (originalDraft === null) setOriginalDraft(draft);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    void runReview();
  }

  function applyFix(f: Finding) {
    const next = applySuggestedFix(draft, f);
    if (next === null) {
      setNotice(
        typeof f.suggested_fix !== "string"
          ? "No automatic fix is available for this finding. Edit the draft manually."
          : `Couldn't find “${f.matched_text}” in the current draft. Edit it manually.`
      );
      return;
    }
    setDraft(next);
    setStates((s) => ({ ...s, [f.id]: "fix_applied" }));
    setNotice(null);
  }

  const setState = (id: string, st: FindingState) => setStates((s) => ({ ...s, [id]: st }));

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl">
          Review before <span className="text-maroon-soft">you publish.</span>
        </h1>
        <p className="mt-3 max-w-2xl text-sm text-muted">
          Check content against brand rules. Every flag shows its source. AI suggests, humans decide.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section aria-labelledby="draft-heading" className="rounded-2xl border border-line bg-surface p-5">
          <h2 id="draft-heading" className="text-lg font-semibold">Your draft</h2>

          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div>
              <label htmlFor="brand" className="block text-sm font-medium">Brand</label>
              <select id="brand" value={brandId} onChange={(e) => setBrandId(e.target.value)} className={field}>
                {brands.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="purpose" className="block text-sm font-medium">
                Intended purpose <span className="font-normal text-muted">(optional)</span>
              </label>
              <input
                id="purpose"
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                placeholder="e.g. Instagram promo for the spring sale"
                className={field}
              />
            </div>

            <DraftEditor value={draft} onChange={setDraft} disabled={loading} />

            {error && (
              <div role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm text-ink">
                <strong>Review failed.</strong> {error}
                <div className="mt-2">
                  <button
                    type="button"
                    onClick={() => void runReview()}
                    disabled={loading}
                    className="rounded-full border border-line px-4 py-1.5 text-sm font-medium text-ink hover:bg-surface-2 disabled:opacity-60"
                  >
                    Try again
                  </button>
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="rounded-full bg-maroon px-6 py-2.5 text-sm font-semibold text-white hover:bg-maroon-hover disabled:opacity-60"
            >
              {loading ? "Reviewing…" : result ? "Re-run review" : "Submit for review"}
            </button>
          </form>

          {originalDraft !== null && originalDraft !== draft && (
            <details className="mt-6 rounded-xl border border-line bg-surface-2 p-3">
              <summary className="cursor-pointer text-sm font-medium">Compare original vs current draft</summary>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <div>
                  <h3 className="text-xs font-semibold uppercase text-muted">Original</h3>
                  <pre className="mt-1 whitespace-pre-wrap rounded-lg bg-bg p-2 text-sm">{originalDraft}</pre>
                </div>
                <div>
                  <h3 className="text-xs font-semibold uppercase text-muted">Current</h3>
                  <pre className="mt-1 whitespace-pre-wrap rounded-lg bg-bg p-2 text-sm">{draft}</pre>
                </div>
              </div>
            </details>
          )}
        </section>

        <section aria-labelledby="findings-heading" aria-live="polite">
          <h2 id="findings-heading" className="text-lg font-semibold">Findings</h2>

          {loading && (
            <p role="status" className="mt-4 rounded-2xl border border-line bg-surface p-5 text-sm text-muted">
              Reviewing your draft against brand rules…
            </p>
          )}

          {!loading && !result && (
            <div className="mt-4 rounded-2xl border border-dashed border-line bg-surface p-6 text-sm text-muted">
              No review yet. Paste a draft and submit it. Findings with citations will appear here.
            </div>
          )}

          {!loading && result && (
            <div className="mt-4 space-y-4">
              <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-line bg-surface p-4 text-sm">
                <DisplayStatus status={result.status} findingCount={result.findings.length} />
                <span>{result.findings.length} finding(s), {openCount} still open</span>
                <span className="text-xs text-muted">Review ID: {result.review_id}</span>
              </div>

              <AiStatusNotice aiStatus={result.ai_status} aiError={result.ai_error} />

              <p className="text-xs text-muted">
                Trueline recommends fixes. A human reviewer makes the final decision.
              </p>

              {stale && (
                <div role="status" className="rounded-xl border border-ink/40 bg-surface-2 p-3 text-sm">
                  The draft changed since the last review. Re-run the review to verify these results.
                </div>
              )}
              {notice && (
                <div role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm">
                  {notice}
                </div>
              )}

              {result.findings.length === 0 ? (
                <div className="rounded-2xl border border-line bg-surface p-5 text-sm">
                  <p className="font-semibold">◷ Awaiting Human Approval</p>
                  <p className="mt-1 text-muted">
                    The automated check found no issues. That is not an approval. A human reviewer must approve
                    this draft before it is published.
                  </p>
                </div>
              ) : (
                result.findings.map((f) => (
                  <FindingCard
                    key={f.id}
                    finding={f}
                    state={states[f.id] ?? "open"}
                    onApply={() => applyFix(f)}
                    onDismiss={() => setState(f.id, "dismissed")}
                    onReopen={() => setState(f.id, "open")}
                  />
                ))
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}