import type { ReviewRequest, ReviewResponse } from "./types";
import { MOCK_BRANDS, mockSubmitReview } from "./mock/mockReviewService";
import { apiPost, isLive } from "./api";

export const brands = MOCK_BRANDS;

export async function submitReview(req: ReviewRequest): Promise<ReviewResponse> {
  if (!isLive) return mockSubmitReview(req);
  const data = await apiPost<ReviewResponse>("/api/review", req);
  if (!data || !Array.isArray(data.findings) || typeof data.review_id !== "string") {
    throw new Error("The backend returned an unexpected review response.");
  }
  return data;
}
