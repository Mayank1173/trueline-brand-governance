
import type { ReviewRequest, ReviewResponse } from "./types";
import { MOCK_BRANDS, mockSubmitReview } from "./mock/mockReviewService";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

export const brands = MOCK_BRANDS; // Replace when the brands API is available.

export async function submitReview(
  req: ReviewRequest
): Promise<ReviewResponse> {
  // Keep using sample data during frontend development.
  if (USE_MOCK) {
    return mockSubmitReview(req);
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");

  if (!apiUrl) {
    throw new Error(
      "The API URL is missing. Check NEXT_PUBLIC_API_URL in .env.local."
    );
  }

  let res: Response;

  try {
    res = await fetch(`${apiUrl}/api/review`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(req),
    });
  } catch {
    throw new Error(
      "Couldn't reach the review service. Check that the backend is running and try again."
    );
  }

  if (!res.ok) {
    let message = `The review service returned an error (${res.status}).`;

    try {
      const errorData = await res.json();

      if (typeof errorData.detail === "string") {
        message = errorData.detail;
      } else if (typeof errorData.message === "string") {
        message = errorData.message;
      }
    } catch {
      // Keep the default message if the error response is not JSON.
    }

    throw new Error(message);
  }

  let data: unknown;

  try {
    data = await res.json();
  } catch {
    throw new Error("The review service returned invalid JSON.");
  }

  if (
    typeof data !== "object" ||
    data === null ||
    !("review_id" in data) ||
    typeof data.review_id !== "string" ||
    !("status" in data) ||
    !["approved", "changes_requested", "needs_human_review"].includes(
      data.status as string
    ) ||
    !("findings" in data) ||
    !Array.isArray(data.findings)
  ) {
    throw new Error(
      "The review service returned an unexpected response. Check the backend contract."
    );
  }

  return data as ReviewResponse;
}
