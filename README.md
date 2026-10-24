# Trueline — Explainable Brand Governance

Team: AETHERON

Trueline reviews draft marketing content against approved brand guidelines,
terminology, formatting requirements, and approved facts **before publication**.
Every deterministic finding cites the guideline or approved fact that produced
it. Humans make the final publication decision.

## Repository layout

| Path | Purpose |
|---|---|
| `backend/` | FastAPI + Pydantic v2 + SQLAlchemy review API, rule engine, migrations, tests |
| `frontend/` | Existing Next.js review UI (not modified by the backend work) |
| `data/` | Notes on safe development fixtures |
| `docs/` | Architecture, requirements, demo script, and API contract |
| `tests/` | QA plans and sample-dataset placeholders (Markdown only) |
| `rule-engine-spec.md` | Proposed rule-engine design, still pending team confirmation |

## Quick start (backend)

Requires Python 3.10 or newer.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Open Swagger UI at <http://localhost:8000/docs>.

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/review `
  -ContentType "application/json" `
  -Body '{"brand_id":"brand_001","draft_text":"Our cheapest plan is guaranteed. Terms apply.","purpose":"marketing"}'
```

Full setup, configuration, testing, migration, and deployment details are in
[`backend/README.md`](backend/README.md). The request/response contract is in
[`docs/api-contracts.md`](docs/api-contracts.md).

## Current scope and honesty notes

- The rule engine is **deterministic** and runs without an AI service or API key.
- Demo brands, guidelines, and facts are **illustrative** and are not official
  Trueline policy. See `backend/app/seed_data.py`.
- No authentication, authorization, or multi-tenant isolation is implemented.
- PostgreSQL is the intended deployment database, but only SQLite was verified
  locally. Migrations are written to be PostgreSQL-compatible.
- The frontend is unchanged. To connect it, set `NEXT_PUBLIC_USE_MOCK=false`
  and `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## AI review engine (`backend/trueline/`)

The optional AI review engine adds provider-backed findings on top of the
deterministic backend rule engine. It is disabled by default and never replaces
the deterministic checks.

- `backend/trueline/review/` — review orchestration and deterministic checks
- `backend/trueline/providers/` — swappable AI provider interface
- `backend/trueline/adapters/fastapi_adapter.py` — conversion to the API contract
- `backend/trueline/eval.py` — Northstar evaluation harness

Run the AI-engine tests and evaluation from the repository root:

```powershell
python -m pytest tests -q
python -m trueline.eval --output-dir eval_results
```

The backend keeps final approval with a human. AI findings without a valid
citation are never surfaced, and no citation metadata is fabricated.
