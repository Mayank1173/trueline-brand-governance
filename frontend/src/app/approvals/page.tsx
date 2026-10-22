"use client";
import { useState } from "react";
import ActivityLog from "@/components/ActivityLog";
import ApprovalActions, { type Decision } from "@/components/ApprovalActions";
import SampleDataNotice from "@/components/SampleDataNotice";
import StatusBadge from "@/components/StatusBadge";
import { SAMPLE_DRAFTS, SAMPLE_REVISIONS } from "@/lib/mock/sampleData";
import type { ActivityEvent, ApprovalStatus } from "@/lib/workflowTypes";

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
  const [humanEvents, setHumanEvents] = useState<ActivityEvent[]>(
    latest.events.filter((e) => e.actor_type === "human")
  );
  const [role, setRole] = useState<"reviewer" | "editor">("reviewer");

  function handleDecide(d: Decision, comment: string) {
    setStatus(d);
    setHumanEvents((prev) => [
      {
        id: `local-${Date.now()}`,
        actor_type: "human",
        actor: "You (this browser session)",
        action: ACTION_TEXT[d],
        comment: comment || undefined,
        at: new Date().toISOString(),
      },
      ...prev,
    ]);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight md:text-5xl">Approval workflow</h1>
        <p className="mt-3 text-sm text-muted">AI recommends. Only a human reviewer decides.</p>
      </div>

      <SampleDataNotice>
        Decisions you record here live only in this browser tab and aren’t saved anywhere.
      </SampleDataNotice>

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

      <div className="grid gap-6 lg:grid-cols-2">
        <section aria-labelledby="draft-heading" className="space-y-4 rounded-2xl border border-line bg-surface p-5">
          <h2 id="draft-heading" className="text-lg font-semibold">{draft.title}</h2>
          <div className="flex flex-wrap items-center gap-3 text-sm" aria-live="polite">
            <span className="text-muted">Version {latest.number}</span>
            {status === "rejected" ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-maroon-soft bg-maroon px-3 py-0.5 text-xs font-semibold text-white">
                <span aria-hidden="true">✕</span> Rejected
              </span>
            ) : (
              <StatusBadge status={status} />
            )}
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
          <ApprovalActions canReview={role === "reviewer"} onDecide={handleDecide} />
          <ActivityLog events={humanEvents} />
        </section>
      </div>
    </div>
  );
}