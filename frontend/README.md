# Trueline Frontend

Next.js + TypeScript + Tailwind CSS frontend for Trueline, an explainable brand-governance tool that reviews marketing drafts against brand guidelines before publication.

> **Status:** the Draft Review screen is built and runs against a **mock service**. No real backend or AI review is connected yet. Findings shown in the UI are sample data, not real reviews.

## Local setup

Requires Node.js 18.18 or newer.

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Environment variables

Create `frontend/.env.local` (not committed). Only public values belong here. Never put API keys or Supabase service-role secrets in frontend code.

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_USE_MOCK` | mock is **on** unless set to `false` | Switches between the mock service and the real API |
| `NEXT_PUBLIC_API_URL` | none | Base URL of the FastAPI backend, used when mock is off |

## Checks

```bash
npm run lint
npx tsc --noEmit
```

Last recorded result: `tsc --noEmit` passed with no errors. Lint has not been recorded yet. Automated UI tests have not been written yet.

## Routes

| Route | Status |
|---|---|
| `/` | Redirects to `/review` |
| `/review` | Draft Review screen (built, mock-backed) |
| `/dashboard`, `/guidelines`, `/approvals`, `/history` | Not built yet (shown as "soon" in the sidebar) |

## Structure

```
src/
  app/            Routes and layout
  components/     AppSidebar, AppHeader, DraftEditor, FindingCard,
                  CitationPanel, SeverityBadge, StatusBadge
  lib/
    types.ts            Shared types matching the API contract
    reviewService.ts    Single swap point between mock and real API
    applyFix.ts         Applies a suggested fix to the draft safely
    mock/               Mock review service (sample data only)
```

## API contract assumptions

Based on the contract agreed with Mayank. Still to be confirmed with Kushal's backend.

- `POST /api/review` with `brand_id`, `draft_text`, `purpose`
- `status`: `approved`, `changes_requested`, `needs_human_review`
- `severity`: `low`, `medium`, `high`
- `start` / `end`: zero-based character offsets into the original draft, `end` exclusive
- `citation`: object or `null`. The UI never invents a citation and warns when it is missing
- `suggested_fix`: string or `null`. The UI hides "Accept fix" when it is `null`
- `confidence`: number from 0.0 to 1.0, displayed as a score and not as a calibrated probability
- `requires_human_review`: boolean

**Open questions:** how a missing-phrase finding represents `start`/`end` (the frontend currently treats an empty `matched_text` as "append"), and the final shared list of `category` values.

## Mock behaviour

The mock service (`src/lib/mock/mockReviewService.ts`) flags a few hard-coded terms and returns a fake delay. It is not an AI review. Type `__error__` in a draft to trigger the error state.

## Behaviour notes

- Accepting a fix edits the draft but marks the finding as "not verified" until the review is re-run.
- Dismissed findings stay visible and can be reopened.
- Status and severity use icons and text, not colour alone.
- Accessibility has not been formally tested, and no WCAG compliance is claimed.