"use client";
import { useState } from "react";
import ConfirmDialog from "./ConfirmDialog";
import type { Decision } from "@/lib/decisionService";

export type { Decision };

const LABEL: Record<Decision, string> = {
  approved: "Approve",
  rejected: "Reject",
};

interface Props {
  canReview: boolean;
  onDecide: (decision: Decision, comment: string) => Promise<void>;
}

const primary = "rounded-full bg-maroon px-4 py-2 text-sm font-semibold text-white hover:bg-maroon-hover";
const secondary = "rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-surface-2";

export default function ApprovalActions({ canReview, onDecide }: Props) {
  const [comment, setComment] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [pending, setPending] = useState<Decision | null>(null);
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!canReview) {
    return (
      <p className="rounded-xl border border-line bg-surface-2 p-3 text-sm text-muted">
        This review is read-only because a decision has already been recorded.
      </p>
    );
  }

  function ask(d: Decision) {
    if (d !== "approved" && !comment.trim()) {
      setValidationError("Add a comment explaining your decision so the author knows what to do next.");
      return;
    }
    setValidationError(null);
    setSubmitError(null);
    setPending(d);
  }

  async function confirm() {
    if (!pending) return;
    setBusy(true);
    setSubmitError(null);
    try {
      await onDecide(pending, comment.trim());
      setComment("");
      setPending(null);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  function cancel() {
    setPending(null);
    setSubmitError(null);
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="decision-comment" className="block text-sm font-medium">
          Comment <span className="font-normal text-muted">(required when rejecting)</span>
        </label>
        <textarea
          id="decision-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          className="mt-1 w-full rounded-xl border border-line bg-surface p-2.5 text-sm text-ink placeholder:text-muted"
        />
      </div>

      {validationError && (
        <div role="alert" className="rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm">
          {validationError}
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => ask("approved")} className={primary}>Approve</button>
        <button type="button" onClick={() => ask("rejected")} className={secondary}>Reject</button>
      </div>

      <ConfirmDialog
        open={pending !== null}
        title={pending ? `${LABEL[pending]}?` : ""}
        confirmLabel={pending ? `Yes, ${LABEL[pending].toLowerCase()}` : "Confirm"}
        busy={busy}
        error={submitError}
        onConfirm={confirm}
        onCancel={cancel}
      >
        <p>
          You’re about to <strong className="text-ink">{pending ? LABEL[pending].toLowerCase() : ""}</strong> this
          draft as a human reviewer.
        </p>
        {comment.trim() && <p className="mt-2">Your comment: “{comment.trim()}”</p>}
      </ConfirmDialog>
    </div>
  );
}
