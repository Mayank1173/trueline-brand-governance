# Trueline API Contracts

Status: implemented by the FastAPI backend in `backend/`. Local base URL:
`http://localhost:8000`. OpenAPI/Swagger UI: `/docs`.

The frontend is unchanged and remains the integration source of truth for
`POST /api/review`. Where the leader/rule-engine proposal used different field
names, this API returns a compatible superset (see
[Compatibility decisions](#compatibility-decisions)).

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Process and database health |
| `POST` | `/api/review` | Submit a draft for deterministic review |
| `GET` | `/api/reviews` | Paginated review history |
| `GET` | `/api/reviews/{review_id}` | One persisted review with findings |
| `GET` | `/api/reviews/{review_id}/history` | Audit events for a review |
| `GET` | `/api/brands` | Brands |
| `GET` | `/api/brands/{brand_id}` | One brand |
| `GET` | `/api/brands/{brand_id}/guidelines` | Active guidelines/source text |
| `GET` | `/api/brands/{brand_id}/facts` | Approved facts and validity |

No authentication is implemented. All endpoints are currently open. Do not
deploy to an untrusted public environment without adding access controls.

## POST /api/review

### Request

```json
{
  "brand_id": "brand_001",
  "draft_text": "Our cheapest plan is guaranteed. Terms apply.",
  "purpose": "marketing"
}
```

| Field | Type | Rules |
|---|---|---|
| `brand_id` | string | Required, non-empty after trimming, max 64 chars, must exist |
| `draft_text` | string | Required, non-empty after trimming, configured max 20,000 chars |
| `purpose` | string or null | Optional; free-form, trimmed, default `general`; max 200 chars |

Unknown request fields are rejected. Request bodies above
`TRUELINE_MAX_REQUEST_BYTES` receive `413`.

### Success response — `200 OK`

This is a real response shape produced from the seeded **illustrative** demo
data. Brand, guideline, and fact values are fictional.

```json
{
  "review_id": "review_e5f38cffb0464388877a2814ee618871",
  "status": "needs_human_review",
  "findings": [
    {
      "id": "review_e5f38cffb0464388877a2814ee618871-F-0001",
      "finding_id": "review_e5f38cffb0464388877a2814ee618871-F-0001",
      "rule_id": "BR-TERM-014",
      "matched_text": "cheapest",
      "start": 4,
      "end": 12,
      "category": "banned_term",
      "severity": "medium",
      "explanation": "The draft uses a banned price superlative that is not supported by the illustrative brand guidelines.",
      "citation": {
        "rule_id": "BR-TERM-014",
        "source": "Trueline Demo Brand Guidelines (ILLUSTRATIVE DEMO DATA - NOT OFFICIAL TRUELINE BRAND POLICY) §2.3",
        "excerpt": "Avoid 'cheapest' and other unverifiable price superlatives.",
        "source_type": "guideline",
        "source_id": "GL-B1-TERM-014",
        "source_version": "demo-ruleset-2026.10",
        "quoted_text": "Avoid 'cheapest' and other unverifiable price superlatives.",
        "valid_until": null
      },
      "suggested_fix": "great value",
      "confidence": 1.0,
      "requires_human_review": false
    },
    {
      "id": "review_e5f38cffb0464388877a2814ee618871-F-0002",
      "finding_id": "review_e5f38cffb0464388877a2814ee618871-F-0002",
      "rule_id": "BR-CLAIM-001",
      "matched_text": "guaranteed",
      "start": 21,
      "end": 31,
      "category": "unsupported_claim",
      "severity": "high",
      "explanation": "This wording makes an absolute guarantee. The deterministic check found the claim language; a human must confirm whether an approved, current fact supports it.",
      "citation": {
        "rule_id": "BR-CLAIM-001",
        "source": "Trueline Demo Brand Guidelines (ILLUSTRATIVE DEMO DATA - NOT OFFICIAL TRUELINE BRAND POLICY) §4.2",
        "excerpt": "Do not promise guaranteed outcomes unless an approved, current fact supports it.",
        "source_type": "guideline",
        "source_id": "GL-B1-CLAIM-001",
        "source_version": "demo-ruleset-2026.10",
        "quoted_text": "Do not promise guaranteed outcomes unless an approved, current fact supports it.",
        "valid_until": null
      },
      "suggested_fix": "designed to help",
      "confidence": 1.0,
      "requires_human_review": true
    }
  ]
}
```

### Finding fields

| Field | Type | Notes |
|---|---|---|
| `id` | string | Frontend key. Unique and stable within the review |
| `finding_id` | string | Same value as `id`; leader/rule-engine name |
| `rule_id` | string | Stable rule identifier |
| `matched_text` | string | Exact draft text, or `""` for missing phrase/length |
| `start` | int or null | Zero-based, end-exclusive UTF-16 offset |
| `end` | int or null | End-exclusive UTF-16 offset |
| `category` | string | `banned_term`, `unsupported_claim`, `preferred_terminology`, `required_phrase`, `product_name`, `formatting`, `length_limit`, `tone`, `fact_metadata` |
| `severity` | string | `low`, `medium`, or `high` |
| `explanation` | string | Plain-language reason grounded in the rule |
| `citation` | object or null | Null only when no source supports the finding |
| `suggested_fix` | string or null | Null means no safe automatic fix |
| `confidence` | float | `0.0`–`1.0`; deterministic matches currently use `1.0` |
| `requires_human_review` | bool | True for uncertain/claim/tone/expired-fact findings |

Citation fields:

- Frontend contract: `rule_id`, `source`, `excerpt`.
- Grounding metadata: `source_type` (`guideline` or `approved_fact`),
  `source_id`, `source_version`, `quoted_text`, `valid_until`.

`excerpt` and `quoted_text` are the same exact source text. Sources are validated
against rows belonging to the requested brand; the backend returns `500` rather
than an invented citation if validation fails.

### Review status

| Status | Meaning |
|---|---|
| `approved` | No findings from the configured rules |
| `changes_requested` | Findings exist and none require human judgment |
| `needs_human_review` | At least one finding requires human judgment |

`draft` and `in_review` exist in the frontend type union for workflow states
but are not emitted by `POST /api/review`.

### Error format

All application errors use one shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
      {
        "loc": ["body", "draft_text"],
        "msg": "Value error, draft_text must not be empty or whitespace-only",
        "type": "value_error"
      }
    ]
  }
}
```

| Status | Code examples | Cause |
|---|---|---|
| `404` | `not_found` | Unknown brand or review |
| `413` | `draft_too_large`, `request_too_large` | Configured size limit exceeded |
| `422` | `validation_error`, `purpose_too_long` | Invalid body, type, or query parameter |
| `500` | `citation_validation_failed`, `rule_engine_error` | Internal consistency/configuration failure |
| `503` | `database_unavailable` | Database unavailable; nothing was saved |

No stack traces or secrets are returned to clients.

## GET endpoints

### `GET /health`

```json
{
  "status": "ok",
  "database": "connected",
  "environment": "local",
  "version": "0.1.0"
}
```

Returns `503` with `status: "degraded"` and `database: "unavailable"` when the
database cannot be reached.

### `GET /api/reviews`

Query parameters:

- `brand_id` (optional, must exist)
- `limit` (1–100, default 50)
- `offset` (>= 0, default 0)

```json
{
  "items": [
    {
      "review_id": "review_...",
      "brand_id": "brand_001",
      "purpose": "marketing",
      "status": "changes_requested",
      "finding_count": 1,
      "requires_human_review_count": 0,
      "created_at": "2026-10-23T19:00:00Z",
      "updated_at": "2026-10-23T19:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

Timestamps are returned in UTC with a `Z` suffix.

### `GET /api/reviews/{review_id}`

Returns the review summary fields plus `draft_text`, `ruleset_version`,
`engine_version`, `evaluation_date`, and the full `findings` array.

### `GET /api/reviews/{review_id}/history`

```json
{
  "review_id": "review_...",
  "events": [
    {
      "id": "event_...",
      "event_type": "review_created",
      "actor_type": "system",
      "actor": "Trueline API",
      "action": "Review request accepted.",
      "comment": null,
      "at": "2026-10-23T19:00:00Z"
    }
  ]
}
```

### `GET /api/brands`

Returns an array of `{id, name, description}`. The seeded illustrative brands
are `brand_001` and `brand-demo`.

### `GET /api/brands/{brand_id}/guidelines`

```json
{
  "brand": { "id": "brand_001", "name": "...", "description": "..." },
  "guidelines": [
    {
      "source_id": "GL-B1-TERM-014",
      "rule_id": "BR-TERM-014",
      "title": "...",
      "section": "2.3",
      "version": "demo-ruleset-2026.10",
      "content": "Avoid 'cheapest' and other unverifiable price superlatives.",
      "category": "banned_term",
      "severity": "medium",
      "match_type": "term",
      "explanation": "...",
      "suggested_fix": "great value",
      "confidence": 1.0,
      "requires_human_review": false
    }
  ]
}
```

### `GET /api/brands/{brand_id}/facts`

Returns `{brand, approved_facts}`. Each fact includes `source_id`, `statement`,
`source`, `source_version`, `valid_from`, `valid_until`, and `is_current`.

## Compatibility decisions

The current frontend (`frontend/src/lib/types.ts`) and the proposed leader
schema use different names. The implementation keeps both where practical:

| Concern | Decision |
|---|---|
| Finding ID | Return both `id` and `finding_id` with the same value |
| Citation | Return frontend fields plus grounded source metadata |
| Severity | `low`, `medium`, `high` (frontend/rule-engine intersection) |
| Status | Frontend workflow statuses; no `completed` string |
| Missing phrase | `matched_text: ""`, `start: null`, `end: null` |
| Offsets | UTF-16 code units matching JavaScript `slice`; ASCII is identical to Python indices |
| Categories | Frontend names used where possible; `fact_metadata` added for expired facts |

These choices remain provisional if Mayank/Vandana finalize a different schema.
Changing them requires updating the frontend contract first.

## Local server and environment

```powershell
cd backend
Copy-Item ..\.env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Frontend connection:

```powershell
# frontend/.env.local
NEXT_PUBLIC_USE_MOCK=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## How to test with PowerShell

```powershell
$body = @{
  brand_id   = "brand_001"
  draft_text = "Our cheapest plan is guaranteed. Terms apply."
  purpose    = "marketing"
} | ConvertTo-Json

$result = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/review `
  -ContentType "application/json" -Body $body

$result.review_id
$result.status
$result.findings | Select-Object rule_id, matched_text, start, end, category

# Retrieve the persisted review and its history
Invoke-RestMethod http://localhost:8000/api/reviews/$($result.review_id) |
  ConvertTo-Json -Depth 8
Invoke-RestMethod http://localhost:8000/api/reviews/$($result.review_id)/history |
  ConvertTo-Json -Depth 8
```

Demo data is illustrative and must not be presented as official brand policy.
