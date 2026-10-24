import type { AIStatus } from "@/lib/types";

interface Props {
  aiStatus: AIStatus | null | undefined;
  aiError: string | null | undefined;
}

export default function AiStatusNotice({ aiStatus, aiError }: Props) {
  if (!aiStatus) return null;

  if (aiStatus === "success") {
    return (
      <p className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
        <span className="font-semibold">✓ AI reviewed.</span> AI findings are tied to guideline citations. A human
        still makes the final decision.
      </p>
    );
  }

  if (aiStatus === "skipped") {
    return (
      <p role="status" className="rounded-xl border border-line bg-surface-2 p-3 text-sm text-muted">
        <span className="font-semibold text-ink">Deterministic checks only.</span> No AI review was configured
        for this brand.
      </p>
    );
  }

  return (
    <div role="status" className="rounded-xl border border-line bg-surface-2 p-3 text-sm">
      <p>
        <span className="font-semibold">AI review did not complete.</span> Deterministic checks are shown and
        human review is required.
      </p>
      {aiError && <p className="mt-1 text-xs text-muted">Detail: {aiError}</p>}
    </div>
  );
}