// ⚠️ MOCK ONLY until the backend decision endpoint exists.
// When Mayank shares the contract, replace the body of submitDecision() with a real
// POST (e.g. /api/reviews/{id}/decision) and set is_mock: false. Nothing else changes.

export type Decision = "approved" | "changes_requested" | "rejected";

export interface DecisionResult {
  review_id: string;
  decision: Decision;
  comment: string;
  decided_at: string; // ISO 8601, UTC
  is_mock: boolean;
}

export async function submitDecision(
  reviewId: string,
  decision: Decision,
  comment: string
): Promise<DecisionResult> {
  await new Promise((r) => setTimeout(r, 800)); // fake network delay

  // Type __error__ in the comment to test the error state.
  if (comment.includes("__error__")) {
    throw new Error("Mock server error (500). Your decision was not saved. Try again.");
  }

  return {
    review_id: reviewId,
    decision,
    comment,
    decided_at: new Date().toISOString(),
    is_mock: true,
  };
}