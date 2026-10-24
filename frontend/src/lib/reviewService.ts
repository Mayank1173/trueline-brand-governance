import type { AIStatus, Finding, ReviewRequest, ReviewResponse } from "./types";
import { MOCK_BRANDS, mockSubmitReview } from "./mock/mockReviewService";
import { errorMessage } from "./api";

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
const TIMEOUT_MS = 30000;

const AI_STATUSES: string[] = [
  "disabled",
  "skipped",
  "not_configured",
  "unavailable",
  "timeout",
  "degraded",
  "success",
];

export const brands = MOCK_BRANDS; // Replace when the brands API is wired in.

function normalizeFinding(raw: unknown, index: number): Finding {
  const f = (typeof raw === "object" && raw !== null ? raw : {}) as Record<string, unknown>;
  return {
    ...(f as unknown as Finding),
    id: typeof f.id === "string" && f.id ? f.id : `finding-${index}`,
    matched_text: typeof f.matched_text === "string" ? f.matched_text : "",
    explanation: typeof f.explanation === "string" ? f.explanation : "",
    citation: (f.citation as Finding["citation"]) ?? null,
    suggested_fix: typeof f.suggested_fix === "string" ? f.suggested_fix : null,
    confidence: typeof f.confidence === "number" ? f.confidence : undefined,
    start: typeof f.start === "number" ? f.start : undefined,
    end: typeof f.end === "number" ? f.end : undefined,
    requires_human_review: f.requires_human_review === true,
  };
}

export async function submitReview(req: ReviewRequest): Promise<ReviewResponse> {
  // Keep using sample data during frontend development.
  if (USE_MOCK) {
    return mockSubmitReview(req);
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");
  if (!apiUrl) {
    throw new Error("The API URL is missing. Check NEXT_PUBLIC_API_URL in .env.local.");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let res: Response;
  try {
    res = await fetch(`${apiUrl}/api/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("The review took too long and was cancelled. Try again.");
    }
    throw new Error("Couldn't reach the review service. Check that the backend is running and try again.");
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // keep the default message if the error response is not JSON
    }
    throw new Error(errorMessage(body, res.status));
  }

  let data: unknown;
  try {
    data = await res.json();
  } catch {
    throw new Error("The review service returned invalid JSON.");
  }

  const d = data as Record<string, unknown> | null;
  if (
    typeof d !== "object" ||
    d === null ||
    typeof d.review_id !== "string" ||
    !["approved", "changes_requested", "needs_human_review"].includes(d.status as string) ||
    !Array.isArray(d.findings)
  ) {
    throw new Error("The review service returned an unexpected response. Check the backend contract.");
  }

  const aiStatus =
    typeof d.ai_status === "string" && AI_STATUSES.includes(d.ai_status) ? (d.ai_status as AIStatus) : null;

  return {
    review_id: d.review_id,
    status: d.status as ReviewResponse["status"],
    findings: d.findings.map(normalizeFinding),
    ai_status: aiStatus,
    ai_error: typeof d.ai_error === "string" ? d.ai_error : null,
  };
}