# Frontend AI integration handoff

The review request is unchanged. Do not send AI configuration, keys, or new
fields from the browser.

```json
{
  "brand_id": "brand_001",
  "draft_text": "...",
  "purpose": "marketing"
}
```

The response adds two optional top-level fields to submit, list, and detail
responses. Existing finding fields are unchanged.

```ts
type AIStatus =
  | "disabled"
  | "skipped"
  | "not_configured"
  | "unavailable"
  | "timeout"
  | "degraded"
  | "success";

interface AIReviewFields {
  ai_status: AIStatus | null;
  ai_error: string | null;
}
```

Use `null` for reviews created before these fields existed.

## Suggested UI behavior

- Render findings exactly as today. AI findings use the same `FindingResponse`
  shape and are already citation-grounded by the backend.
- Do not show an "AI reviewed" badge unless `ai_status === "success"`.
- For `skipped`, show deterministic results only. The seed/demo rule set is all
  computed, so the demo normally returns `skipped`.
- For `disabled`, `not_configured`, `unavailable`, `timeout`, or `degraded`,
  show a neutral notice such as "AI review did not complete; deterministic
  checks are shown and human review is required." Use `ai_error` only as
  supporting detail.
- Never infer success from an empty `ai_error` or from finding count. Trust
  `ai_status`.
- Never expose or request an Anthropic key in the frontend.

## Status semantics

| Status | UI interpretation |
|---|---|
| `skipped` | No AI work was configured; no failure |
| `success` | AI ran and all AI citations were grounded |
| `disabled` | AI rules exist but the feature flag is off |
| `not_configured` | Enabled but the key/provider is missing |
| `unavailable` | Optional AI package is not installed |
| `timeout` | Provider timed out |
| `degraded` | Provider failed or ungrounded AI findings were rejected |

Every non-success status above (`disabled` through `degraded`) forces the review
status to `needs_human_review`. Deterministic findings remain present.

## Contract test expectation

The frontend contract test should accept the additive `ai_status` and
`ai_error` keys. It must not require them on old fixtures; both may be `null`.
No existing request or finding key changes.
