"use client";
import { useState } from "react";
import ActivityLog from "@/components/ActivityLog";
import ApprovalActions, { type Decision } from "@/components/ApprovalActions";
import SampleDataNotice from "@/components/SampleDataNotice";
import StatusBadge from "@/components/StatusBadge";
import { submitDecision } from "@/lib/decisionService";
import { SAMPLE_DRAFTS, SAMPLE_REVISIONS } from "@/lib/mock/sampleData";
import type { ActivityEvent, ApprovalStatus } from "@/lib/workflowTypes";

const LIVE = process.env.NEXT_PUBLIC_USE_MOCK === "false";

const draft = SAMPLE_DRAFTS[0];
const latest = SAMPLE_REVISIONS[0];
const aiEvents = latest.events.filter((e) => e.actor_type === "ai");

const ACTION_TEXT: Record<Decision, string> = {
  approved: "Approved this draft",
  changes_requested: "Requested changes",
  rejected: "Rejected this draft",
};

export default function ApprovalsPage() {
  const [status, setStatus] = useState<ApprovalStatus>(draft.status);
  const [mockEvents, setMockEvents] = useState<ActivityEvent[]>([]);
  const [role, setRole] = useState<"reviewer" | "editor">("reviewer");

  // Throws on failure, and ApprovalActions shows the error in the dialog.
  async function handleDecide(d: Decision, comment: string) {
    const result = await submitDecision(draft.id, d, comment);
    setStatus(d);
    setMockEvents((prev) => [
      {
        id: `mock-${result.decided_at}`,
        actor_type: "human",
        actor: "Mock reviewer (not a real person)",
        action: `[MOCK] ${ACTION_TEXT[d]}`,
        comment: result.comment || undefined,
        at: result.decided_at,
      },
      ...prev,
    ]);
  }

  function resetMock() {
    setStatus(draft.status);
    setMockEvents([]);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Approval workflow</h1>
        <p className="mt-3 text-sm text-muted">AI recommends. Only a human reviewer decides.</p>
      </div>

      <SampleDataNotice>
        Mock decisions on a sample draft. They aren’t sent to the backend, aren’t saved, and never appear in
        Revision History.
        {LIVE && " The backend decision endpoint isn’t connected to this page yet."}
      </SampleDataNotice>

      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label htmlFor="role" className="block text-sm font-medium">Viewing as (demo only)</label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value as "reviewer" | "editor")}
            className="mt-1 rounded-xl border border-line bg-surface p-2.5 text-sm text-ink"
          >
            <option value="reviewer">Reviewer (can decide)</option>
            <option value="editor">Editor (view only)</option>
          </select>
        </div>
        {mockEvents.length > 0 && (
          <button
            type="button"
            onClick={resetMock}
            className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-surface-2"
          >
            Reset mock decisions
          </button>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section aria-labelledby="draft-heading" className="space-y-4 rounded-2xl border border-line bg-surface p-5">
          <h2 id="draft-heading" className="text-lg font-semibold">{draft.title} (sample)</h2>
          <div className="flex flex-wrap items-center gap-3 text-sm" aria-live="polite">
            <span className="text-muted">Version {latest.number}</span>
            {status === "rejected" ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-maroon-soft bg-maroon px-3 py-0.5 text-xs font-semibold text-white">
                <span aria-hidden="true">✕</span> Rejected
              </span>
            ) : (
              <StatusBadge status={status} />
            )}
            {mockEvents.length > 0 && <span className="text-xs text-muted">(mock status)</span>}
          </div>

          <div>
            <h3 className="text-sm font-semibold">AI recommendation (not a decision)</h3>
            <p className="mt-1 text-sm text-muted">
              Last AI review of version {latest.number}: {draft.open_findings} open finding(s).
            </p>
            <div className="mt-3">
              <ActivityLog events={aiEvents} />
            </div>
          </div>
        </section>

        <section aria-labelledby="human-heading" className="space-y-4 rounded-2xl border border-line bg-surface p-5">
          <h2 id="human-heading" className="text-lg font-semibold">Human reviewer decisions</h2>
          <ApprovalActions canReview={role === "reviewer"} onDecide={handleDecide} isMock />
          {mockEvents.length === 0 ? (
            <p className="text-sm text-muted">No decisions recorded yet.</p>
          ) : (
            <ActivityLog events={mockEvents} />
          )}
        </section>
      </div>
    </div>
  );
}