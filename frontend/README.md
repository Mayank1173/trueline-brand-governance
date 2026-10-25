# Trueline Frontend

Next.js + TypeScript + Tailwind CSS frontend for Trueline, an explainable brand-governance tool. It reviews marketing drafts against brand guidelines **before** publication. AI recommends; a human decides.

## Status

| Area | State |
|---|---|
| Draft Review | Live against the backend, with a mock mode for offline demos |
| Dashboard | Live review list and counts (falls back to labelled sample data if the backend fails) |
| Revision History | Live status and system events. Reviewer decisions appear once the backend saves them |
| Brand Guidelines | Live rules and approved facts, read-only |
| Approvals | Live persisted reviews and approval/rejection decisions |

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

To use mock mode explicitly, set `NEXT_PUBLIC_USE_MOCK=true`. The frontend otherwise
uses the real API and reports connection errors instead of silently treating a missing
configuration as a demo deployment.

## Environment variables

Only public values belong here. Never put API keys or Supabase service-role secrets in frontend code.

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_USE_MOCK` | `false` / unset (live API) | Set to `true` to switch to mock/sample data |
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
| `/approvals` | Select a persisted review, approve or reject it, and inspect persisted history |
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
    decisionService.ts    Human decision POST service
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

## API endpoints used

`POST /api/review`, `GET /api/reviews`, `GET /api/reviews/{id}/history`, `POST /api/reviews/{id}/decision`, `GET /api/brands/{id}/guidelines`, `GET /api/brands/{id}/facts`.

The decision request accepts `approved` or `rejected`, plus optional caller-supplied
`reviewer` and `comment` fields. A successful response includes the updated
status and `decision_event`; the UI then reloads persisted history. Repeating a
decision for an already approved or rejected review returns HTTP 409 and is
shown as an error rather than treated as success. The backend does not currently
authenticate or authorize reviewer identity.

## Known gaps

- Browser-level approval verification is manual; no automated UI test framework is configured
- The header badge ("Live backend configured" / "Demo mode") reflects the environment variable, not a health check
- `ai_status = success` and the timeout/degraded paths have not been seen live
- Dashboard review rows are not clickable (no review detail page yet)
- No automated UI tests
- Accessibility has not been formally tested, and no WCAG compliance is claimed
- Light mode has not been checked on every component
- The background image `public/images/bg-stars.jpg` has an unconfirmed source and licence; the Dashboard illustration was AI-generated

## Notes for teammates

- The root `.gitignore` originally ignored every `lib/` folder, which hid `frontend/src/lib`. An exception (`!frontend/src/lib/`) was added.
- Theme token names such as `maroon` are kept for compatibility but now hold the current sage/amber palette values.
