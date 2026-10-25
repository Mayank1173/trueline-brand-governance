import { apiPost } from "./api";
import type { ReviewResponse, ReviewStatus } from "./types";

export type Decision = "approved" | "rejected";

export interface DecisionResult {
  review_id: string;
  status: ReviewStatus;
  findings: ReviewResponse["findings"];
  ai_status?: ReviewResponse["ai_status"];
  ai_error?: ReviewResponse["ai_error"];
  decision_event: {
    id: string;
    event_type: "human_approval" | "human_rejection";
    actor_type: "human";
    actor: string;
    action: string;
    comment: string | null;
    previous_status: ReviewStatus | null;
    new_status: ReviewStatus | null;
    decision: Decision;
    reviewer: string | null;
    at: string;
  };
}

export async function submitDecision(
  reviewId: string,
  decision: Decision,
  comment: string,
  reviewer: string
): Promise<DecisionResult> {
  const data = await apiPost<unknown>(`/api/reviews/${encodeURIComponent(reviewId)}/decision`, {
    decision,
    reviewer,
    comment,
  });
  const result = data as Partial<DecisionResult> | null;
  if (
    typeof result !== "object" ||
    result === null ||
    typeof result.review_id !== "string" ||
    typeof result.status !== "string" ||
    typeof result.decision_event !== "object" ||
    result.decision_event === null
  ) {
    throw new Error("The backend returned an unexpected decision response.");
  }
  return result as DecisionResult;
}
