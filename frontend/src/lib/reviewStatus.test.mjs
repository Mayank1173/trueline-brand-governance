import assert from "node:assert/strict";
import { canRecordDecision, countReviewStatuses, REVIEW_STATUSES } from "./reviewStatus.ts";
import { SAMPLE_DRAFTS } from "./mock/sampleData.ts";

// Only the five statuses the backend can actually assign are shown.
assert.deepEqual(REVIEW_STATUSES, [
  "pending_approval",
  "changes_requested",
  "needs_human_review",
  "approved",
  "rejected",
]);

assert.equal(canRecordDecision("pending_approval"), true);
assert.equal(canRecordDecision("changes_requested"), true);
assert.equal(canRecordDecision("needs_human_review"), true);
assert.equal(canRecordDecision("approved"), false);
assert.equal(canRecordDecision("rejected"), false);

const counts = countReviewStatuses([
  { status: "approved" },
  { status: "approved" },
  { status: "rejected" },
  { status: "pending_approval" },
]);
assert.equal(counts.approved, 2);
assert.equal(counts.rejected, 1);
assert.equal(counts.pending_approval, 1);
assert.equal(counts.changes_requested, 0);
assert.equal(counts.needs_human_review, 0);
assert.equal(counts.draft, 0);
assert.equal(counts.in_review, 0);

// Sample rows must stay inside the same reachable status set.
for (const draft of SAMPLE_DRAFTS) {
  assert.ok(
    REVIEW_STATUSES.includes(draft.status),
    `sample draft ${draft.id} uses unreachable status ${draft.status}`,
  );
}

console.log("review status regression: PASS");
