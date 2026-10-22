"use client";
import { useState } from "react";

export type Decision = "approved" | "changes_requested" | "rejected";

interface Props {
  canReview: boolean;
  onDecide: (decision: Decision, comment: string) => void;
}

const primary = "rounded-full bg-maroon px-4 py-2 text-sm font-semibold text-white hover:bg-maroon-hover";
const secondary = "rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-surface-2";

export default function ApprovalActions({ canReview, onDecide }: Props) {
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (!canReview) {
    return (
      <p className="rounded-xl border border-line bg-surface-2 p-3 text-sm text-muted">
        Your role can view this review but can’t record decisions. Ask a reviewer.
      </p>
    );
  }

  function decide(d: Decision) {
    if (d !== "approved" && !comment.trim()) {
      setError("Add a comment explaining your decision so the author knows what to do next.");
      return;
    }
    setError(null);
    onDecide(d, comment.trim());
    setComment("");
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="decision-comment" className="block text-sm font-medium">
          Comment <span className="font-normal text-muted">(required to request changes or reject)</span>
        </label>
        <textarea
          id="decision-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          className="mt-1 w-full rounded-xl border border-line bg-surface p-2.5 text-sm text-ink placeholder:text-muted"
        />
      </div>
      {error && (
        <div role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm">
          {error}
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => decide("approved")} className={primary}>Approve</button>
        <button type="button" onClick={() => decide("changes_requested")} className={secondary}>Request changes</button>
        <button type="button" onClick={() => decide("rejected")} className={secondary}>Reject</button>
      </div>
    </div>
  );
}