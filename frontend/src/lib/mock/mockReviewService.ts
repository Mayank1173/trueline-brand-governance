// ⚠️ MOCK DATA ONLY. Not a real AI review. Replace via src/lib/reviewService.ts.
import type { Brand, Citation, Finding, ReviewRequest, ReviewResponse, Severity } from "../types";

export const MOCK_BRANDS: Brand[] = [{ id: "brand_001", name: "Sample Brand (mock)" }];

interface Rule {
  term: string;
  category: string;
  severity: Severity;
  explanation: string;
  suggested_fix: string | null;
  citation: Citation | null;
  confidence: number;
  requires_human_review: boolean;
}

const RULES: Rule[] = [
  {
    term: "guaranteed",
    category: "unsupported_claim",
    severity: "high",
    explanation: "Absolute guarantees cannot be supported by an approved, current fact.",
    suggested_fix: "designed to help",
    citation: {
      rule_id: "CLAIM-001",
      source: "Sample Brand Guidelines §4.2 (sample)",
      excerpt: "Do not promise guaranteed outcomes unless an approved, current fact supports it.",
    },
    confidence: 0.93,
    requires_human_review: true,
  },
  {
    term: "cheapest",
    category: "banned_term",
    severity: "medium",
    explanation: "Comparative price claims are discouraged in brand copy.",
    suggested_fix: "great value",
    citation: {
      rule_id: "TERM-014",
      source: "Sample Brand Guidelines §2.3 (sample)",
      excerpt: "Avoid 'cheapest' and other unverifiable price superlatives.",
    },
    confidence: 0.88,
    requires_human_review: false,
  },
  {
    term: "revolutionary",
    category: "tone",
    severity: "low",
    explanation: "Hype language conflicts with the calm, credible brand voice.",
    suggested_fix: "innovative",
    citation: {
      rule_id: "VOICE-003",
      source: "Sample Brand Guidelines §1.1 (sample)",
      excerpt: "Voice is confident and factual. Avoid exaggerated hype words.",
    },
    confidence: 0.74,
    requires_human_review: false,
  },
  {
    // Tests the "no safe fix" path (suggested_fix = null)
    term: "!!!",
    category: "formatting",
    severity: "low",
    explanation: "Multiple exclamation marks are not allowed in brand copy.",
    suggested_fix: null,
    citation: {
      rule_id: "FMT-002",
      source: "Sample Brand Guidelines §3.4 (sample)",
      excerpt: "Use at most one exclamation mark per post.",
    },
    confidence: 0.99,
    requires_human_review: false,
  },
  {
    // Tests the "no citation" path (citation = null)
    term: "world-class",
    category: "unsupported_claim",
    severity: "medium",
    explanation: "Possible unsupported superlative. No matching guideline was found, so a human should check.",
    suggested_fix: null,
    citation: null,
    confidence: 0.55,
    requires_human_review: true,
  },
];

export async function mockSubmitReview(req: ReviewRequest): Promise<ReviewResponse> {
  await new Promise((r) => setTimeout(r, 900));

  if (req.draft_text.includes("__error__")) {
    throw new Error("Mock server error (500). Try again in a moment.");
  }

  const lower = req.draft_text.toLowerCase();
  const findings: Finding[] = [];

  RULES.forEach((rule, i) => {
    const idx = lower.indexOf(rule.term.toLowerCase());
    if (idx >= 0) {
      findings.push({
        id: `finding_${String(i + 1).padStart(3, "0")}`,
        matched_text: req.draft_text.slice(idx, idx + rule.term.length),
        start: idx,
        end: idx + rule.term.length, // exclusive
        category: rule.category,
        severity: rule.severity,
        explanation: rule.explanation,
        citation: rule.citation ? { ...rule.citation } : null,
        suggested_fix: rule.suggested_fix,
        confidence: rule.confidence,
        requires_human_review: rule.requires_human_review,
      });
    }
  });

  if (!lower.includes("terms apply")) {
    findings.push({
      id: "finding_disclaimer",
      matched_text: "",
      category: "required_phrase",
      severity: "medium",
      explanation: "Promotional copy must end with the required disclaimer.",
      citation: {
        rule_id: "LEGAL-002",
        source: "Sample Brand Guidelines §6.1 (sample)",
        excerpt: "All promotional content must include 'Terms apply.'",
      },
      suggested_fix: "Terms apply.",
      confidence: 0.97,
      requires_human_review: false,
    });
  }

  const status = findings.some((f) => f.requires_human_review)
    ? "needs_human_review"
    : findings.length > 0
      ? "changes_requested"
      : "approved";

  return { review_id: `review_mock_${Date.now()}`, status, findings };
}