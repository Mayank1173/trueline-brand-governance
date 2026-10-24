import type { ReviewStatus } from "./types";

export type ActorType = "ai" | "human" | "system";
export type ApprovalStatus = ReviewStatus | "rejected";

export interface DraftSummary {
  id: string;
  title: string;
  status: ReviewStatus;
  version: number;
  updated_at: string; // ISO 8601, UTC
  open_findings: number;
}

export interface ActivityEvent {
  id: string;
  actor_type: ActorType;
  actor: string;
  action: string;
  comment?: string;
  at: string; // ISO 8601, UTC
}

export interface Revision {
  id: string;
  number: number;
  submitted_at: string;
  status: ReviewStatus;
  summary: string;
  events: ActivityEvent[];
}

export interface BrandGuidelines {
  brand_id: string;
  name: string;
  voice: { rule_id: string; text: string }[];
  preferred_terms: { rule_id: string; use: string; instead_of: string }[];
  banned_terms: { rule_id: string; term: string; reason: string }[];
  required_phrases: { rule_id: string; phrase: string; when: string }[];
  facts: { rule_id: string; text: string; source: string; expires: string | null }[];
}