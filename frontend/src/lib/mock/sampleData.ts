// ⚠️ SAMPLE DATA ONLY. These are not real drafts, reviews, people or audit records.
// Replace with API calls once Kushal's endpoints exist.
import type { BrandGuidelines, DraftSummary, Revision } from "../workflowTypes";

export const SAMPLE_DRAFTS: DraftSummary[] = [
  { id: "draft_001", title: "Spring sale Instagram post", status: "changes_requested", version: 3, updated_at: "2026-10-21T16:40:00Z", open_findings: 2 },
  { id: "draft_002", title: "Product launch email", status: "pending_approval", version: 1, updated_at: "2026-10-21T09:10:00Z", open_findings: 0 },
  { id: "draft_003", title: "Newsletter intro", status: "approved", version: 2, updated_at: "2026-10-18T14:00:00Z", open_findings: 0 },
  { id: "draft_004", title: "Homepage banner copy", status: "pending_approval", version: 1, updated_at: "2026-10-17T12:30:00Z", open_findings: 0 },
];

// Newest first. Revisions of draft_001.
export const SAMPLE_REVISIONS: Revision[] = [
  {
    id: "rev_003",
    number: 3,
    submitted_at: "2026-10-21T16:40:00Z",
    status: "changes_requested",
    summary: "Replaced “cheapest” with “great value” and added the disclaimer. Guarantee claim still present.",
    events: [
      { id: "e5", actor_type: "human", actor: "Sample Reviewer", action: "Requested changes", comment: "Remove the guarantee claim or link an approved fact.", at: "2026-10-21T17:05:00Z" },
      { id: "e4", actor_type: "ai", actor: "Review AI (sample)", action: "Recommended changes: 2 open findings, 1 needs human review.", at: "2026-10-21T16:41:00Z" },
    ],
  },
  {
    id: "rev_002",
    number: 2,
    submitted_at: "2026-10-20T11:15:00Z",
    status: "changes_requested",
    summary: "Removed “revolutionary”. Price and guarantee claims still present.",
    events: [
      { id: "e3", actor_type: "ai", actor: "Review AI (sample)", action: "Recommended changes: 3 open findings.", at: "2026-10-20T11:16:00Z" },
    ],
  },
  {
    id: "rev_001",
    number: 1,
    submitted_at: "2026-10-19T09:30:00Z",
    status: "changes_requested",
    summary: "Initial submission.",
    events: [
      { id: "e2", actor_type: "ai", actor: "Review AI (sample)", action: "Recommended changes: 4 open findings.", at: "2026-10-19T09:31:00Z" },
    ],
  },
];

export const SAMPLE_GUIDELINES: BrandGuidelines = {
  brand_id: "brand_001",
  name: "Sample Brand (mock)",
  voice: [
    { rule_id: "VOICE-001", text: "Confident and factual. Short sentences." },
    { rule_id: "VOICE-003", text: "Avoid exaggerated hype words such as “revolutionary”." },
  ],
  preferred_terms: [{ rule_id: "TERM-020", use: "customers", instead_of: "users" }],
  banned_terms: [
    { rule_id: "TERM-014", term: "cheapest", reason: "Unverifiable price superlative." },
    { rule_id: "CLAIM-001", term: "guaranteed", reason: "Promises an outcome without an approved fact." },
  ],
  required_phrases: [{ rule_id: "LEGAL-002", phrase: "Terms apply.", when: "All promotional content" }],
  facts: [
    { rule_id: "FACT-001", text: "Free shipping on orders over $50.", source: "Pricing policy v4 (sample)", expires: "2026-12-31" },
    { rule_id: "FACT-002", text: "Battery lasts up to 10 hours.", source: "Lab test report (sample)", expires: null },
  ],
};