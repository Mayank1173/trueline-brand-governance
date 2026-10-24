# Trueline Backend

FastAPI review API for deterministic, explainable brand-governance checks.
Deterministic findings always come from database-driven rules and cite the
approved guideline or approved fact loaded for the requested brand. An optional
AI layer can add findings for guidelines marked `ai`/`hybrid`; it is disabled by
default, never replaces deterministic checks, and reports its execution status.

## What is implemented

- `POST /api/review` — validate a draft, run deterministic checks, optionally
  run grounded AI checks, validate citations against the database, persist the
  review, return findings with `ai_status`/`ai_error`.
- `GET /health` — process and database health.
- `GET /api/reviews` — paginated review list, optionally filtered by brand.
- `GET /api/reviews/{review_id}` — persisted review and findings.
- `GET /api/reviews/{review_id}/history` — audit events for a review.
- `GET /api/brands` — brands available to the UI.
- `GET /api/brands/{brand_id}` — one brand.
- `GET /api/brands/{brand_id}/guidelines` — active rules and their source text.
- `GET /api/brands/{brand_id}/facts` — approved facts and validity status.

Swagger UI is available at `/docs`; ReDoc at `/redoc`.

## Architecture

| Module | Responsibility |
|---|---|
| `app/main.py` | App factory, lifespan, CORS, error handlers, request-size limit |
| `app/config.py` | Environment settings (`TRUELINE_*`) |
| `app/database.py` | SQLAlchemy engine/session; SQLite locally, PostgreSQL-compatible |
| `app/models.py` | Brands, guidelines, approved facts, reviews, findings, audit events |
| `app/schemas.py` | Pydantic v2 request/response models |
| `app/repositories.py` | Queries and model-to-engine adapters |
| `app/rule_engine/` | Independent deterministic engine with no FastAPI/DB imports |
| `app/citations.py` | Strict source/version/quote validation |
| `app/evaluation.py` | Pure helpers for precise-finding vs sentence-annotation matching |
| `app/ai_labels.py` | Allowed original AI label values |
| `app/ai_review.py` | Optional AI bridge, strict citation grounding, execution statuses |
| `app/services.py` | Review orchestration, merge/dedupe, transaction handling |
| `app/seed.py`, `app/seed_data.py` | Clearly labelled illustrative demo data |
| `app/ai.py` | Legacy assistant protocol; not used by `ReviewService` |
| `trueline/providers/` | Swappable AI providers (Anthropic) |
| `migrations/` | Alembic revisions for the review schema |

### Review flow

1. Validate the request with Pydantic and configured size limits.
2. Load the brand, active guidelines, and approved facts **scoped to that brand**.
3. Run `RuleEngine` over computed/hybrid rules (no network, no model). AI-only
   rules are excluded from the deterministic engine.
4. If enabled and configured, send ai/hybrid guidelines and active facts to the
   AI provider. AI findings with missing, unknown, mismatched, or ungrounded
   citations are rejected; rejected findings make the run `degraded`.
5. Merge AI findings with deterministic findings, keeping deterministic results
   on overlap, and validate every citation against the loaded source rows.
6. Derive status: `needs_human_review` if any finding needs a human or AI did
   not complete cleanly, otherwise `changes_requested` if there are findings,
   otherwise `approved`.
7. Insert review, findings, AI status/error, and two audit events in one
   transaction.
8. Return the response only after the commit succeeds. A failed commit returns
   `503` and is rolled back.

## Windows PowerShell setup

Requires Python 3.10 or newer for the deterministic backend. The optional AI
package requires Python 3.11 or newer. Run these commands from the repository
root.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
Copy-Item ..\.env.example .env
```

Edit `backend\.env` if needed. The defaults use SQLite and seed illustrative
demo data automatically.

### Start the server

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open <http://localhost:8000/docs>. The first startup creates
`backend\trueline.db` and seeds the demo brands.

### Test the review endpoint

```powershell
$body = @{
  brand_id   = "brand_001"
  draft_text = "Our cheapest plan is guaranteed. Terms apply."
  purpose    = "marketing"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/review `
  -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8
```

Useful demo inputs:

| Draft fragment | Expected check |
|---|---|
| `cheapest` | banned term `BR-TERM-014` |
| `guaranteed` | unsupported claim `BR-CLAIM-001`, human review |
| `revolutionary` | tone `BR-VOICE-003`, human review |
| `!!!` | formatting `BR-FMT-002` |
| `users` | preferred terminology `BR-TERM-020` |
| `TrueLine`, `True Line`, `True-Line` | product name `BR-PRODUCT-001` |
| no `Terms apply.` | missing required phrase `BR-LEGAL-002` |
| `Free returns within 30 days.` | expired approved fact |
| more than 1,200 characters | length limit `BR-LIMIT-001` |

A draft with none of the demo violations and containing `Terms apply.` returns
`status: "approved"` with an empty `findings` array.

### Run tests

```powershell
cd backend
python -m pytest -q
```

Tests use isolated temporary SQLite databases and require no internet or paid
API. The migration test upgrades and downgrades a temporary database.

### Lint and format

Ruff is used if available; it is not a runtime dependency.

```powershell
ruff check app tests
ruff format --check app tests
```

## Database and migrations

Local default: `sqlite:///./trueline.db` relative to the backend working
directory. Tests use temporary SQLite files.

`TRUELINE_AUTO_CREATE_TABLES=true` (default) calls `create_all` for convenient
local/demo startup. For a deployed environment, disable it and run migrations:

```powershell
$env:TRUELINE_AUTO_CREATE_TABLES = "false"
alembic upgrade head
```

PostgreSQL example (replace placeholders; never commit real credentials):

```powershell
$env:TRUELINE_DATABASE_URL = "postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME"
$env:TRUELINE_AUTO_CREATE_TABLES = "false"
$env:TRUELINE_SEED_DEMO_DATA = "false"
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The schema uses SQLAlchemy generic types and Alembic migrations. **Only SQLite
has been verified in this workspace.** PostgreSQL has not been run or validated.

### Tables

- `brands`
- `guidelines` (rule ID, source ID, nullable version, exact quoted source text, matcher config)
- `approved_facts` (statement, source, nullable version, validity window,
  active flag, optional `superseded_by` fact ID)
- `reviews` (draft, purpose, status, ruleset/engine versions, evaluation date,
  nullable `ai_status`/`ai_error`)
- `review_findings` (span, category, severity, explanation, nullable AI label, citation fields)
- `review_events` (ordered audit trail)

## Configuration

All backend variables use the `TRUELINE_` prefix. See `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `TRUELINE_ENVIRONMENT` | `local` | Reported by `/health` |
| `TRUELINE_DATABASE_URL` | SQLite file in `backend/` | SQLAlchemy URL |
| `TRUELINE_AUTO_CREATE_TABLES` | `true` | Local convenience; use migrations in deployment |
| `TRUELINE_SEED_DEMO_DATA` | `true` | Idempotent illustrative seed |
| `TRUELINE_MAX_DRAFT_CHARS` | `20000` | Per-draft limit; larger requests get `413` |
| `TRUELINE_MAX_PURPOSE_CHARS` | `200` | Purpose-field limit |
| `TRUELINE_MAX_REQUEST_BYTES` | `1000000` | `Content-Length` request cap |
| `TRUELINE_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `TRUELINE_RULESET_VERSION` | `demo-ruleset-2026.10` | Stored on each review |
| `TRUELINE_AI_ENABLED` | `false` | Enables AI review only when `ANTHROPIC_API_KEY` is also set |
| `TRUELINE_LOG_LEVEL` | `INFO` | Python logging level |

AI provider variables (no real secret belongs in the repository):

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | empty | Required, non-empty key to enable AI |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Provider model |
| `ANTHROPIC_MAX_TOKENS` | `4096` | Provider response limit |
| `ANTHROPIC_TIMEOUT_SECONDS` | `30` | Provider request timeout |

Both the backend `Settings.ai_enabled` flag and the root `trueline.config`
settings read `TRUELINE_AI_ENABLED`. A key alone is not sufficient. To enable
AI, install the root package (which provides `trueline` and `anthropic`) into
the same environment:

```powershell
# from the repository root
pip install -e ".[dev]"
```

If the package is missing, the review still completes deterministically with
`ai_status: "unavailable"`. The test suite mocks the provider; it never makes a
paid API call. CORS never enables credentials and never defaults to a wildcard.

## Frontend connection

The existing frontend reads two public variables. Do not change frontend source.

```powershell
# frontend/.env.local
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then restart `npm run dev` in `frontend/`. The review UI sends the existing
`{brand_id, draft_text, purpose}` payload to `POST /api/review`.

## Public response compatibility decisions

The frontend contract (`frontend/src/lib/types.ts`) and the leader/rule-engine
contract use different names. The backend returns a compatible superset:

- `FindingResponse.id` (frontend) and `finding_id` (leader spec) are both present
  and equal.
- `CitationOut` includes `{rule_id, source, excerpt}` for the frontend and
  `{source_type, source_id, source_version, quoted_text, valid_until}` for
  grounded citations. `source_version` is `null` when the source has no recorded
  version; it is never fabricated. `valid_until` is `YYYY-MM-DD` or `null`.
- `FindingResponse.ai_label` is a separate nullable original AI label. Valid
  non-null values are `VIOLATION`, `NEEDS_HUMAN_JUDGEMENT`, `UNSUPPORTED`,
  `CONTRADICTED`, and `OUTDATED`. Deterministic findings leave it `null`.
- Top-level `ai_status` and `ai_error` are additive on submit, summary, and
  detail responses. Both may be `null` for rows created before migration 0003.
- Severity is `low | medium | high`.
- Status is `approved | changes_requested | needs_human_review`.
- Missing required phrases and length violations use `matched_text: ""` with
  `start: null`, `end: null`, matching the frontend's append/no-offset handling.
- Offsets are zero-based, end-exclusive **UTF-16 code units**, because the
  frontend slices JavaScript strings. This only differs from Python character
  indices for non-BMP characters such as emoji.
- Evaluation does not widen findings to sentences. `app/evaluation.py` matches a
  precise finding to a sentence annotation only on positive overlap; no-span
  findings are matched at draft/rule level instead. See
  `../docs/evaluation-matching.md`.

These choices are provisional where the team has not formally confirmed the
proposed rule-engine schema. They are documented here rather than silently
assumed.

## Deterministic rule engine

Supported matcher types:

- `term` — banned terms, preferred terminology, product names, claim/tone
  keywords. Case sensitivity and word-boundary behavior are per-rule.
- `required_phrase` — reports a missing phrase with no text span.
- `regex` — formatting checks such as repeated exclamation marks.
- `length_limit` — character-count check.
- Approved-fact expiry — an exact, case-insensitive statement occurrence is
  flagged when the fact is expired or not yet valid on the evaluation date.

All occurrences are reported. Different rules may overlap (different issues);
overlaps inside one rule are resolved longest-first for stable output. Findings
are sorted deterministically by offset, end, and rule ID.

The engine intentionally does **not** claim to verify arbitrary factual truth.
It detects configured claim language and exact expired-fact statements. Human
review remains required where indicated.

### AI label boundary

`ai_label` is the original label an AI system may have assigned; it is not a
backend decision. The deterministic engine always leaves it `null`. AI findings
may set `FindingDraft.ai_label`; `ReviewService` validates and persists it, and
both the submit and detail responses expose it. AI findings cannot create
citations or approved facts and cannot overwrite deterministic findings. A
finding with missing, unknown, mismatched, or ungrounded citation is rejected
rather than stripped. Non-null labels are validated against the five allowed
values before persistence and again when building the response.

### AI execution statuses

`ai_status` is additive in `POST /api/review`, review summaries, and review
details. `ai_error` is a safe, human-readable explanation or `null`.

| `ai_status` | Meaning | Requires human? |
|---|---|---|
| `skipped` | No ai/hybrid guidelines are configured | No |
| `success` | AI completed; all returned citations were grounded | No |
| `disabled` | `TRUELINE_AI_ENABLED` is false but AI work is configured | Yes |
| `not_configured` | Enabled but no API key/provider is available | Yes |
| `unavailable` | The `trueline` package is not installed | Yes |
| `timeout` | Provider request timed out | Yes |
| `degraded` | Provider failed or one or more AI findings were rejected | Yes |

Only facts active on the evaluation date are sent. Facts with
`status_on_evaluation_date` of `inactive`, `superseded`, `expired`, or
`not_yet_valid` are excluded; `superseded_by` is preserved when known. The AI
layer uses `asyncio.run` and is intended for the current synchronous route; do
not call it from an already-running event loop without an async refactor.

## Demo data warning

`app/seed_data.py` is **illustrative demonstration data**. It is clearly labelled
in the API source strings and is not official Trueline brand policy. Do not mix
it with real brand configuration in a production run.

## Deployment notes (local verification vs deployment)

Local verification completed in this repository:

- SQLite startup, seeding, review submission, persistence, retrieval, history
- All automated tests
- Alembic upgrade/downgrade against SQLite

Not verified here:

- PostgreSQL connectivity or migration execution
- Render or any other hosting platform
- Authentication/authorization or multi-tenant security (none implemented)
- Live Anthropic API calls (the integration and failure paths are tested with
  mocks; no paid call was made during development)

For Render-style deployment:

- Build: `pip install -r requirements.txt`
- AI build: also `pip install -e ..` from `backend/` (installs `trueline` and
  `anthropic`); without it AI reports `unavailable`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Set `TRUELINE_DATABASE_URL` to the managed PostgreSQL URL
- Set `TRUELINE_AUTO_CREATE_TABLES=false`
- Run `alembic upgrade head` as a pre-deploy/release command
- Set `TRUELINE_CORS_ORIGINS` to the deployed frontend origin
- Do not enable the demo seed in a real environment

No deployment was performed and no remote resources were modified.
