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
- AI: not implemented in the MVP. `backend/app/ai.py` defines a disabled
  integration boundary only. No model calls are made and no AI-generated facts
  or citations are accepted.

## Implemented flow

1. `POST /api/review` validates the request.
2. The service loads the brand, active guidelines, and approved facts.
3. The deterministic engine produces findings with exact offsets.
4. Citation validation checks source existence, brand scope, version, and quote.
5. Review, findings, and audit events are persisted in one transaction.
6. The API returns frontend-compatible findings; persistence failure returns
   `503` rather than a false success.

## Not implemented

- Authentication, authorization, roles, or multi-tenant isolation.
- RAG or any retrieval pipeline over embeddings/pgvector.
- Live AI provider integration.
- Production deployment verification, including PostgreSQL runtime testing.

Any future AI layer must consume already-validated findings and must not invent
approved facts, source IDs, source versions, or citations.
