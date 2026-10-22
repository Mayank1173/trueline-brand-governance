import type { ReviewRequest, ReviewResponse } from "./types";
import { MOCK_BRANDS, mockSubmitReview } from "./mock/mockReviewService";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

export const brands = MOCK_BRANDS; // TODO: replace with GET /api/brands once agreed

export async function submitReview(req: ReviewRequest): Promise<ReviewResponse> {
  if (USE_MOCK) return mockSubmitReview(req);

  let res: Response;
  try {
    res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  } catch {
    throw new Error("Couldn't reach the review service. Check your connection and try again.");
  }
  if (!res.ok) {
    throw new Error(`The review service returned an error (${res.status}). Try again shortly.`);
  }
  const data = await res.json();
  if (!data || !Array.isArray(data.findings)) {
    throw new Error("The review service sent an unexpected response. Tell the backend team.");
  }
  return data as ReviewResponse;
}