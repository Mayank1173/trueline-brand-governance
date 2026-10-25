export type ReviewStatus =
  | "draft"
  | "in_review"
  | "changes_requested"
  | "needs_human_review"
  | "pending_approval"
  | "rejected"
  | "approved";

export type Severity = "low" | "medium" | "high";

// Shared category set. Confirm the final list with Mayank/Vandana.
export type FindingCategory =
  | "unsupported_claim"
  | "banned_term"
  | "preferred_terminology"
  | "required_phrase"
  | "product_name"
  | "formatting"
  | "length_limit"
  | "tone";

export interface Citation {
  rule_id: string;
  source: string;
  excerpt: string;
}

export interface Finding {
  id: string;
  matched_text: string; // "" when nothing in the draft matches (e.g. a missing required phrase)
  start?: number; // zero-based offset into the ORIGINAL draft_text
  end?: number; // exclusive
  category: FindingCategory | string; // string fallback so unknown backend values don't crash the UI
  severity: Severity;
  explanation: string;
  citation: Citation | null; // null = no supporting guideline. Never invent one.
  suggested_fix: string | null; // null = no safe fix proposed
  confidence?: number; // 0.0 to 1.0, NOT a calibrated probability
  requires_human_review: boolean;
}

export interface ReviewRequest {
  brand_id: string;
  draft_text: string;
  purpose: string;
}

export interface ReviewResponse {
  review_id: string;
  status: ReviewStatus;
  findings: Finding[];
}

export interface Brand {
  id: string;
  name: string;
}
