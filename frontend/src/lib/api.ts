import type { Brand, ReviewStatus } from "./types";

// Mock mode is opt-in. NEXT_PUBLIC_* values are inlined during `next build`.
export const isLive = process.env.NEXT_PUBLIC_USE_MOCK !== "true";
const TIMEOUT_MS = 15000;

function baseUrl(): string {
  const value = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "");
  if (!value) throw new Error("The API URL is missing. Check NEXT_PUBLIC_API_URL.");
  return value;
}

function errorMessage(body: unknown, status: number): string {
  if (typeof body === "object" && body !== null) {
    const value = body as { detail?: unknown; message?: unknown; error?: { message?: unknown } };
    if (typeof value.error?.message === "string") return value.error.message;
    if (typeof value.detail === "string") return value.detail;
    if (typeof value.message === "string") return value.message;
  }
  return `The backend returned an error (${status}).`;
}

export async function apiGet<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, { cache: "no-store", signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The backend request timed out.");
    }
    throw new Error("Couldn't reach the backend. Check that it is running.");
  } finally {
    clearTimeout(timer);
  }
  let body: unknown = null;
  try { body = await response.json(); } catch { /* handled below */ }
  if (!response.ok) throw new Error(errorMessage(body, response.status));
  return body as T;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}${path}`, {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("The backend request timed out.");
    }
    throw new Error("Couldn't reach the backend. Check that it is running.");
  } finally {
    clearTimeout(timer);
  }
  let responseBody: unknown = null;
  try { responseBody = await response.json(); } catch { /* handled below */ }
  if (!response.ok) throw new Error(errorMessage(responseBody, response.status));
  return responseBody as T;
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
}

export async function fetchReviews(limit = 50): Promise<ReviewSummary[]> {
  const data = await apiGet<{ items?: unknown }>(`/api/reviews?limit=${limit}`);
  if (!Array.isArray(data.items)) throw new Error("The backend returned an unexpected review list.");
  return data.items as ReviewSummary[];
}

export async function fetchBrands(): Promise<Brand[]> {
  const data = await apiGet<unknown>("/api/brands");
  if (!Array.isArray(data)) throw new Error("The backend returned an unexpected brand list.");
  const brands = data.filter(
    (brand): brand is Brand =>
      typeof brand === "object" && brand !== null &&
      typeof (brand as { id?: unknown }).id === "string" &&
      typeof (brand as { name?: unknown }).name === "string",
  );
  if (brands.length !== data.length) throw new Error("The backend returned an unexpected brand list.");
  if (brands.length === 0) throw new Error("No brands are configured in the backend.");
  return brands;
}
