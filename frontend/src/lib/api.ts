import type { AIStatus, ReviewStatus } from "./types";

export const isLive = process.env.NEXT_PUBLIC_USE_MOCK === "false";
const TIMEOUT_MS = 15000;

export function errorMessage(body: unknown, status: number): string {
  const fallback = `The review service returned an error (${status}).`;
  if (typeof body !== "object" || body === null) return fallback;
  const b = body as Record<string, unknown>;

  const err = b.error;
  if (typeof err === "object" && err !== null) {
    const e = err as { message?: unknown; details?: unknown };
    let msg = typeof e.message === "string" ? e.message : "";
    if (Array.isArray(e.details)) {
      const parts = e.details
        .map((d) => (typeof d === "object" && d !== null && typeof (d as { msg?: unknown }).msg === "string" ? (d as { msg: string }).msg : null))
        .filter((m): m is string => m !== null);
      if (parts.length > 0) msg = `${msg} ${parts.join("; ")}`.trim();
    }
    if (msg) return msg;
  }
  if (typeof b.detail === "string") return b.detail;
  if (typeof b.message === "string") return b.message;
  return fallback;
}

export async function apiGet<T>(path: string): Promise<T> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");
  if (!apiUrl) throw new Error("The API URL is missing. Check NEXT_PUBLIC_API_URL in .env.local.");

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${apiUrl}${path}`, { signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("The request took too long and was cancelled.");
    }
    throw new Error("Couldn't reach the backend. Check that it is running.");
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // not JSON
    }
    throw new Error(errorMessage(body, res.status));
  }

  try {
    return (await res.json()) as T;
  } catch {
    throw new Error("The backend returned invalid JSON.");
  }
}

export interface ReviewSummary {
  review_id: string;
  brand_id: string;
  purpose: string | null;
  status: ReviewStatus;
  finding_count: number;
  requires_human_review_count: number;
  created_at: string;
  updated_at: string;
  ai_status: AIStatus | null;
  ai_error: string | null;
}

export async function fetchReviews(limit = 50): Promise<ReviewSummary[]> {
  const data = await apiGet<{ items?: unknown }>(`/api/reviews?limit=${limit}`);
  if (!Array.isArray(data.items)) throw new Error("The backend returned an unexpected review list.");
  return data.items as ReviewSummary[];
}