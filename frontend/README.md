# Trueline Frontend

Next.js + TypeScript + Tailwind CSS frontend for Trueline, an explainable brand-governance tool. It reviews marketing drafts against brand guidelines **before** publication. AI recommends; a human decides.

## Status

| Area | State |
|---|---|
| Draft Review | Live against the backend, with a mock mode for offline demos |
| Dashboard | Live review list and counts (falls back to labelled sample data if the backend fails) |
| Revision History | Live status and system events. Reviewer decisions appear once the backend saves them |
| Brand Guidelines | Live rules and approved facts, read-only |
| Approvals | **Mock only.** The UI is built; the backend decision endpoint is not connected yet |

## Local setup

Requires Node.js 18.18 or newer.

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

### Running against the real backend

1. Start the backend (from its own folder):
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```
   Check http://localhost:8000/docs.
2. Create `frontend/.env.local` (never committed):
   ```
   NEXT_PUBLIC_USE_MOCK=false
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
3. Restart `npm run dev`. Environment variables are only read at startup.

Delete `.env.local` to return to mock mode.

## Environment variables

Only public values belong here. Never put API keys or Supabase service-role secrets in frontend code.

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_USE_MOCK` | mock is on unless set to `false` | Switches between mock/sample data and the real API |
| `NEXT_PUBLIC_API_URL` | none | Base URL of the FastAPI backend, used when mock is off |

## Checks

Run from `frontend/`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```

There are no automated UI tests yet.

## Routes

| Route | Description |
|---|---|
| `/` | Redirects to `/dashboard` |
| `/dashboard` | Review status counts and recent reviews |
| `/guidelines` | Brand rules and approved facts, read-only |
| `/review` | Draft Review: submit a draft, see findings, accept or dismiss fixes, re-run |
| `/approvals` | Approve / Request changes / Reject UI. **Mock decisions only** |
| `/history` | Per-review audit trail, split into status/system events and reviewer decisions |

## Structure

```
src/
  app/                 Routes and layout
  components/          AppSidebar, AppHeader, ThemeToggle, DraftEditor, FindingCard,
                       CitationPanel, SeverityBadge, StatusBadge, DisplayStatus,
                       AiStatusNotice, ActivityLog, RevisionHistory, ApprovalActions,
                       ConfirmDialog, EmptyState, SampleDataNotice
  lib/
    types.ts              API types
    api.ts                Fetch helpers and error handling
    reviewService.ts      Review requests (mock/live switch, 30 s timeout)
    decisionService.ts    MOCK ONLY decision service. Swap point for the real endpoint
    reviewLabel.ts        Display helpers (short IDs, status text, finding counts)
    applyFix.ts           Applies a suggested fix to the draft safely
    format.ts             Deterministic UTC timestamp formatting
    workflowTypes.ts      History and sample-data types
    mock/                 Mock review service and sample data (never used as real data)
```

## How the UI treats AI and human decisions

- **Clean reviews are not "Approved".** A review with zero findings shows **Awaiting Human Approval** until a human approves it.
- **"AI reviewed" is shown only when the backend reports `ai_status = success`.** `skipped` shows "Deterministic checks only". Any other non-success status shows that the AI review did not complete and human review is required.
- **Accepting a fix edits the draft but does not mark it resolved.** The finding stays "not verified" until the review is re-run.
- **Missing citations are never invented.** A finding without a citation shows a warning.
- **Status and severity use icons and text, not colour alone.**
- **Facts that are no longer current** are marked "Not current" on the Guidelines page.
- The Guidelines page always shows an "Illustrative demo data" disclaimer.

## Mock approval decisions

`/approvals` runs on a sample draft with mock decisions. Mock decisions are labelled `[MOCK]`, attributed to "Mock reviewer (not a real person)", are not sent anywhere, and never appear in Revision History.

When the backend decision endpoint exists, replace the body of `submitDecision()` in `src/lib/decisionService.ts` with the real request. Nothing else should need to change.

## API endpoints used

`POST /api/review`, `GET /api/reviews`, `GET /api/reviews/{id}/history`, `GET /api/brands/{id}/guidelines`, `GET /api/brands/{id}/facts`.

There is **no approve/decision endpoint yet.** The contract is defined by the backend and documented in `docs/api-contracts.md`.

## Known gaps

- Approvals use mock decisions; the real decision endpoint is not connected
- Reviewer decisions in History stay empty until the backend records them
- The brand list on Draft Review is a mock list, and Guidelines uses the fixed ID `brand_001` (could use `GET /api/brands`)
- The header badge ("Live backend connected" / "Demo mode") reflects the environment variable, not a health check
- `ai_status = success` and the timeout/degraded paths have not been seen live
- Dashboard review rows are not clickable (no review detail page yet)
- No automated UI tests
- Accessibility has not been formally tested, and no WCAG compliance is claimed
- Light mode has not been checked on every component
- The background image `public/images/bg-stars.jpg` has an unconfirmed source and licence; the Dashboard illustration was AI-generated

## Notes for teammates

- The root `.gitignore` originally ignored every `lib/` folder, which hid `frontend/src/lib`. An exception (`!frontend/src/lib/`) was added.
- Theme token names such as `maroon` are kept for compatibility but now hold the current sage/amber palette values.