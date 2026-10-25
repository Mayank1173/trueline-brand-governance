import type { ReviewStatus } from "./types";

export const REVIEW_STATUSES: ReviewStatus[] = [
  "pending_approval",
  "changes_requested",
  "needs_human_review",
  "approved",
  "rejected",
];

export const DECISION_ELIGIBLE_STATUSES: ReviewStatus[] = [
  "pending_approval",
  "changes_requested",
  "needs_human_review",
];

export function canRecordDecision(status: ReviewStatus): boolean {
  return DECISION_ELIGIBLE_STATUSES.includes(status);
}

export function countReviewStatuses(
  reviews: Array<{ status: ReviewStatus }>
): Record<ReviewStatus, number> {
  const counts = Object.fromEntries(
    ["draft", "in_review", ...REVIEW_STATUSES].map((status) => [status, 0])
  ) as Record<ReviewStatus, number>;
  for (const review of reviews) counts[review.status] += 1;
  return counts;
}
