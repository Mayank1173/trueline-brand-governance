# Architecture

## Current implementation

- Frontend: Next.js, TypeScript, Tailwind CSS (existing; not modified by backend work).
- Backend: FastAPI, Pydantic v2, SQLAlchemy 2.
- Database: SQLite for local development and automated tests. PostgreSQL is the
  intended deployment database.
- Rule engine: deterministic, data-driven checks loaded from approved guideline
  records for the requested brand. It has no network dependency.
- Citations: every finding citation is validated against a real database row
  belonging to the requested brand, including source version and quoted text.
- AI: optional and disabled by default. `backend/app/ai_review.py` bridges the
  backend to `backend/trueline/providers/anthropic.py`. AI is used only for
  guidelines marked `ai` or `hybrid`; computed-only reviews never call it.
  AI output cannot create facts or citations, and any finding whose citation is
  missing, unknown, mismatched, or ungrounded is rejected. AI execution status
  (`ai_status`) and a safe error (`ai_error`) are persisted and returned.
  `backend/app/ai.py` is a legacy, unused assistant protocol.

## Implemented flow

1. `POST /api/review` validates the request.
2. The service loads the brand, active guidelines, and approved facts.
3. The deterministic engine runs only `computed`/`hybrid` rules and produces
   findings with exact offsets.
4. If configured, the AI bridge sends `ai`/`hybrid` guidelines and facts active
   on the evaluation date to the provider. It rejects findings whose citations
   are missing, unknown, mismatched, or not grounded in the loaded rows.
5. Deterministic and AI findings are merged; deterministic findings win for the
   same issue and duplicates are not emitted.
6. Citation validation checks source existence, brand scope, version, and quote.
7. Review, findings, `ai_status`/`ai_error`, and audit events are persisted in one
   transaction. AI failures never abort the deterministic review.
8. The API returns frontend-compatible findings; persistence failure returns
   `503` rather than a false success.

## AI failure behavior

AI execution is best-effort and additive. `skipped` means no AI rules apply and
makes no provider call. `disabled`, `not_configured`, `unavailable`, `timeout`,
and `degraded` are persisted truthfully, keep deterministic findings, and force
`needs_human_review`. `success` requires every AI finding to remain grounded.
The AI bridge uses `asyncio.run`, so it must not be invoked from an already
running event loop without an async refactor.

## Not implemented

- Authentication, authorization, roles, or multi-tenant isolation.
- RAG or any retrieval pipeline over embeddings/pgvector.
- Production deployment verification, including PostgreSQL runtime testing.
- Live paid-provider verification; provider calls are mocked in tests.

Approved facts, source IDs, source versions, and citations are never invented by
the AI layer. An AI finding has to cite a loaded guideline or approved fact.
