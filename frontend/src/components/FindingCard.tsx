import type { Finding } from "@/lib/types";
import SeverityBadge from "./SeverityBadge";
import CitationPanel from "./CitationPanel";

export type FindingState = "open" | "fix_applied" | "dismissed";

const CATEGORY: Record<Finding["category"], string> = {
  banned_term: "Banned / discouraged term",
  tone: "Tone & voice",
  missing_disclaimer: "Missing disclaimer",
  unsupported_claim: "Unsupported claim",
};

interface Props {
  finding: Finding;
  state: FindingState;
  onApply: () => void;
  onDismiss: () => void;
  onReopen: () => void;
}

const primary = "rounded-full bg-maroon px-4 py-1.5 text-sm font-semibold text-white hover:bg-maroon-hover";
const secondary = "rounded-full border border-line px-4 py-1.5 text-sm font-medium text-ink hover:bg-surface-2";

export default function FindingCard({ finding, state, onApply, onDismiss, onReopen }: Props) {
  const titleId = `finding-${finding.id}-title`;
  return (
    <article
      aria-labelledby={titleId}
      className={`rounded-2xl border border-line bg-surface p-5 ${state === "dismissed" ? "opacity-60" : ""}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <h3 id={titleId} className="text-sm font-semibold text-ink">
          {CATEGORY[finding.category]}
        </h3>
        <SeverityBadge severity={finding.severity} />
        {finding.requires_human_review && (
          <span className="rounded-full border border-ink/50 px-2.5 py-0.5 text-xs font-semibold text-ink">
            ● Human review required
          </span>
        )}
        {finding.confidence !== undefined && (
          <span className="text-xs text-muted">AI confidence: {Math.round(finding.confidence * 100)}%</span>
        )}
      </div>

      {finding.matched_text && (
        <p className="mt-3 text-sm text-muted">
          Flagged text:{" "}
          <mark className="rounded bg-maroon px-1.5 py-0.5 text-white">{finding.matched_text}</mark>
        </p>
      )}

      <p className="mt-2 text-sm text-ink">{finding.explanation}</p>

      <div className="mt-3">
        <CitationPanel citation={finding.citation} />
      </div>

      <div className="mt-3 rounded-xl border border-line bg-surface-2 p-3 text-sm">
        <span className="font-medium text-maroon-soft">Suggested fix (AI): </span>
        <span className="text-ink">
          {finding.matched_text ? `replace with “${finding.suggested_fix}”` : `add “${finding.suggested_fix}”`}
        </span>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {state === "open" && (
          <>
            <button onClick={onApply} className={primary}>Accept fix</button>
            <button onClick={onDismiss} className={secondary}>Dismiss</button>
          </>
        )}
        {state === "fix_applied" && (
          <p className="text-sm font-medium text-maroon-soft">
            ◷ Fix applied to the draft. Not verified until you re-run the review.
          </p>
        )}
        {state === "dismissed" && (
          <>
            <p className="text-sm text-muted">Dismissed. This issue is still in the draft.</p>
            <button onClick={onReopen} className={secondary}>Reopen</button>
          </>
        )}
      </div>
    </article>
  );
}