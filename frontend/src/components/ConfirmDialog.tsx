"use client";
import { useEffect, useId, useRef } from "react";

interface Props {
  open: boolean;
  title: string;
  children: React.ReactNode;
  confirmLabel: string;
  busy?: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmDialog({ open, title, children, confirmLabel, busy, error, onConfirm, onCancel }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  // Native <dialog>: gives focus trapping and Escape for free.
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-md rounded-2xl border border-line bg-surface p-6 text-ink backdrop:bg-black/60"
    >
      <h2 id={titleId} className="text-lg font-semibold">{title}</h2>
      <div className="mt-3 text-sm text-muted">{children}</div>

      {error && (
        <div role="alert" className="mt-4 rounded-xl border border-maroon-soft bg-maroon/25 p-3 text-sm text-ink">
          <strong>Couldn’t record the decision.</strong> {error}
        </div>
      )}

      <div className="mt-5 flex flex-wrap justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-surface-2 disabled:opacity-60"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
          className="rounded-full bg-maroon px-4 py-2 text-sm font-semibold text-white hover:bg-maroon-hover disabled:opacity-60"
        >
          {busy ? "Saving…" : error ? "Try again" : confirmLabel}
        </button>
      </div>
    </dialog>
  );
}