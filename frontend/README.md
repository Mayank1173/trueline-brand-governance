# Trueline Frontend

Explainable AI brand-governance review screen. Checks marketing drafts against brand guidelines BEFORE publication. It does not schedule or generate content.

Stack: Next.js (App Router) + TypeScript + Tailwind CSS v4. Font: IBM Plex Mono.

## Run

    cd frontend
    npm install
    npm run dev

Open http://localhost:3000. The real backend is used unless mock mode is explicitly enabled.

## Routes

| Route | Purpose | Data |
|---|---|---|
| `/` | Redirects to `/dashboard` | n/a |
| `/dashboard` | Draft overview | Sample data |
| `/review` | Core screen: submit a draft, see findings | Mock review service |
| `/guidelines` | Read-only brand guidelines | Sample data |
| `/approvals` | Approve / request changes / reject | Sample data, decisions in React state only |
| `/history` | Revisions and activity | Sample data |

Every page backed by fake data shows a "Sample data" notice.

## Mock vs real API

Set `NEXT_PUBLIC_USE_MOCK=true` for an offline demo. Any other value uses the real API. Set `NEXT_PUBLIC_API_URL` to the backend base URL before building. Public environment variables are compiled into the browser bundle; do not put secrets in frontend env vars.

## API contract (approved by Mayank, NOT yet confirmed by backend)

`POST /api/review` with `{brand_id, draft_text, purpose}` returns `{review_id, status, findings[]}`.

- `status`: approved | changes_requested | needs_human_review
- `severity`: low | medium | high
- `start`/`end`: zero-based offsets into the original draft, `end` exclusive
- `citation`: `{rule_id, source, excerpt}` or null. Never invented; null shows a "human should verify" warning
- `suggested_fix`: string or null. Null hides "Accept fix"
- `confidence`: 0.0 to 1.0, shown as "AI confidence score", not a calibrated probability
- `requires_human_review`: boolean

## Behaviour rules

- Accepting a fix edits the draft and marks the finding "fix applied, not verified until you re-run the review". Never "resolved".
- Dismissed findings stay visible and can be reopened.
- A banner shows when the draft differs from the reviewed text.
- AI recommendations and human decisions are visually distinct.
- Request changes and Reject require a comment.
- Severity and status badges always have an icon plus a text label, never colour alone.

## Verification (run on 22 Oct 2026)

- `npx tsc --noEmit`: no output on a fresh clone of this branch
- `npm run lint`: no output (clean)
- Manually confirmed: dev server runs; a sample draft on `/review` returns 6 findings
- NOT verified: accept-fix flow, error state, mobile layout, no-fix and no-citation cards, Dashboard, Guidelines, Approvals, History pages
- No automated tests. No formal accessibility testing; no WCAG claims.

## Known gaps

- Dashboard rows are not clickable
- Fact expiry is not checked against today's date
- Role switcher (Reviewer/Editor) is a demo control, not real permissions
- Approval decisions are not persisted
- No UI tests
- No formal accessibility testing

## Open questions for backend

1. How is a missing-required-phrase finding represented in start/end? The frontend assumes empty `matched_text` means "append", with offsets omitted.
2. Final category list. The UI shows the raw string for unknown categories.
3. Real endpoints for brands, guidelines, history and reviewer decisions.
