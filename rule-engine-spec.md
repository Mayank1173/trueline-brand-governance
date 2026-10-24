# Rule Engine Specification — Trueline

> **Status note:** The finding schema in this document is a **proposed design**. Field names, severity levels, and rule IDs must be confirmed with **Mayank and Kushal** before this spec is treated as final. Nothing in this document has been implemented or tested yet. All examples are illustrative only.
>
> **Dataset note:** Brand rules and approved facts referenced here are placeholders. They must be replaced with **Apurwa's** fictional brand guidelines and sample drafts when available. Do not treat any example rule text below as an actual Trueline brand rule.

---

## 1. Purpose and scope

This document specifies the **deterministic rule engine** for Trueline: the set of checks that can run **without an AI model**. The goal is to make these checks predictable, testable, and explainable.

A deterministic check must satisfy three properties:

1. **Same input → same output.** No randomness, no model sampling.
2. **The result can be traced to a rule.** Every finding cites the rule that produced it.
3. **The failure mode is known.** We can state clearly what the check cannot detect.

Checks that require judgment (e.g., "is this claim misleading?") are **out of scope** for the deterministic engine and are handled by the AI-assisted layer, always marked `requires_human_review = true` where appropriate.

---

## 2. Shared finding schema (proposed — pending confirmation)

Every rule type below produces findings in this structure. Field names are proposals for the FastAPI backend.

| Field | Type | Required | Description |
|---|---|---|---|
| `finding_id` | string | yes | Unique ID for this finding instance, e.g. `F-0001`. Stable within a single review run. |
| `rule_id` | string | yes | ID of the rule that produced the finding, e.g. `BR-BANNED-001`. |
| `category` | string (enum) | yes | One of: `banned_term`, `preferred_term`, `required_phrase`, `product_name`, `formatting`, `missing_content`, `approved_fact`, `fact_metadata`, `length_limit`. |
| `severity` | string (enum) | yes | Proposed: `critical`, `high`, `medium`, `low`, `info`. Final values pending confirmation. |
| `matched_text` | string \| null | yes | The exact text that triggered the finding. `null` for "missing content" findings. |
| `start_offset` | int \| null | yes | Zero-based, end-exclusive UTF-16 offset where `matched_text` begins in the draft. `null` if not applicable. |
| `end_offset` | int \| null | yes | End-exclusive UTF-16 offset where `matched_text` ends. `null` if not applicable. |
| `explanation` | string | yes | Plain-language explanation of why this was flagged. |
| `source_reference` | object \| null | yes | The guideline or fact that supports the finding. See §3. |
| `suggested_fix` | string \| null | yes | A proposed correction, if one can be generated safely. `null` if the engine cannot suggest a fix. |
| `confidence` | float (0.0–1.0) | yes | For deterministic rules this is `1.0` when the match is exact and unambiguous; lower when a rule is heuristic. Must be documented per rule. |
| `requires_human_review` | bool | yes | `true` when the rule cannot fully decide the issue and a human must confirm. |
| `ai_label` | string \| null | yes | Original AI label, independent of `category`, `severity`, and `requires_human_review`. One of `VIOLATION`, `NEEDS_HUMAN_JUDGEMENT`, `UNSUPPORTED`, `CONTRADICTED`, `OUTDATED`; `null` for deterministic-only findings. |

### 3. `source_reference` sub-object

```json
{
  "source_type": "guideline | approved_fact | brand_config",
  "source_id": "string",
  "source_version": "string | null",
  "quoted_text": "string | null",
  "valid_until": "ISO-8601 date (YYYY-MM-DD) | null"
}
```

`source_version` is `null` when the approved source has no recorded version. The
backend must not invent a version, substitute an empty string, or accept a
citation version that disagrees with the loaded source.
