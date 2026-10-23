# Trueline AI Review Engine

Explainable AI brand-governance review engine. This module provides deterministic and AI-powered analysis of content against approved brand guidelines.

**Status**: Provisional implementation - schema and APIs subject to team review by Kushal, Nimra, and Vandana.

## Architecture

```
backend/trueline/
├── config.py              # Settings from environment variables
├── models.py              # Pydantic models (Finding, Guideline, ReviewRequest, ReviewResponse)
├── providers/
│   ├── base.py            # AIProvider protocol (swappable)
│   └── anthropic.py       # Anthropic Claude implementation
├── review/
│   ├── deterministic.py   # Rule-based checks (banned terms, required phrases)
│   └── service.py         # ReviewEngine - orchestrates deterministic + AI
└── __init__.py            # Public exports
```

## Key Features

- **Deterministic checks** - Banned terms, required phrases with exact text offsets
- **AI-powered analysis** - Anthropic Claude for complex guideline interpretation
- **Citation validation** - Every AI citation verified against supplied guidelines
- **Offset verification** - `draft[start:end] == matched_text` enforced
- **Degraded mode** - Preserves deterministic findings when AI fails
- **No hardcoded secrets** - All config via environment variables
- **Provider isolation** - AI behind clean interface for swapping

## Installation

```bash
# From repository root
pip install -e ".[dev]"

# Or install dependencies directly
pip install anthropic pydantic pydantic-settings python-dotenv pytest pytest-asyncio
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for AI-powered review
ANTHROPIC_API_KEY=your_api_key_here

# Optional model settings
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=0.0

# Review behavior
REVIEW_DEGRADED_MODE=true  # Preserve deterministic findings on AI failure
LOG_LEVEL=INFO
```

**Without `ANTHROPIC_API_KEY`**, the engine runs in deterministic-only mode.

## Usage

### Basic Review (Kushal Integration)

```python
from trueline import ReviewEngine, ReviewRequest, Guideline, ApprovedFact

# Create engine (reusable)
engine = ReviewEngine()

# Define guidelines (from Apurwa's brand guidelines library)
guidelines = [
    Guideline(
        id="RULE_001",
        title="Avoid guaranteed outcomes",
        text='Do not promise guaranteed results unless supported by an approved fact.',
        category="unsupported_claim",
        source="Northstar Brand Guidelines",
    ),
    Guideline(
        id="RULE_002",
        title="Required disclaimer",
        text='Must include "Results may vary" disclaimer.',
        category="missing_disclaimer",
        source="Northstar Brand Guidelines",
    ),
]

# Optional approved facts for factual accuracy
approved_facts = [
    ApprovedFact(
        id="FACT_001",
        claim="Northstar processes 10M transactions daily",
        evidence="Internal metrics dashboard Q3 2024",
        category="performance",
    ),
]

# Build request
request = ReviewRequest(
    draft_text="Our platform guarantees 10M transactions daily for every customer!",
    brand_id="northstar",
    content_purpose="marketing_email",
    guidelines=guidelines,
    approved_facts=approved_facts,
)

# Run review
response = await engine.review(request)

# Handle response
print(f"Status: {response.status}")  # approved, changes_requested, needs_human_review
print(f"Degraded mode: {response.degraded_mode}")
print(f"Provider error: {response.provider_error}")

for finding in response.findings:
    print(f"  [{finding.severity.upper()}] {finding.category}: {finding.matched_text}")
    print(f"    Offset: {finding.start}-{finding.end}")
    print(f"    Explanation: {finding.explanation}")
    print(f"    Citation: {finding.citation.rule_id if finding.citation else 'None'}")
    print(f"    Fix: {finding.suggested_fix}")
    print(f"    Confidence: {finding.confidence}")
    print(f"    Human review: {finding.requires_human_review}")
```

### Deterministic-Only Review

```python
# No AI provider - runs only deterministic checks
engine = ReviewEngine(ai_provider=None)
response = await engine.review(request)
# response.degraded_mode == True
```

### Custom AI Provider

```python
from trueline.providers.base import AIProvider

class MyProvider(AIProvider):
    @property
    def name(self) -> str:
        return "my-provider"

    async def analyze(self, draft_text, content_purpose, guidelines, approved_facts):
        # Your implementation
        return []

    async def health_check(self) -> bool:
        return True

engine = ReviewEngine(ai_provider=MyProvider())
```

## Models

### Finding (Provisional Schema)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique finding identifier |
| `matched_text` | string | Yes | Exact text from the original draft |
| `start` | integer | Yes | Zero-based start offset (inclusive) |
| `end` | integer | Yes | Zero-based end offset (exclusive) |
| `category` | string enum | Yes | `banned_term`, `tone`, `missing_disclaimer`, `unsupported_claim`, `preferred_terminology`, `required_phrase`, `product_name_inconsistency`, `formatting`, `missing_content`, `length_limit` |
| `severity` | string enum | Yes | `low`, `medium`, `high` |
| `explanation` | string | Yes | Why the content may violate a guideline |
| `citation` | object/null | Yes | Supporting guideline evidence |
| `suggested_fix` | string/null | Yes | Proposed correction |
| `confidence` | number | Yes | 0.0 to 1.0 |
| `requires_human_review` | boolean | Yes | Whether a human should verify |

### Citation

```json
{
  "rule_id": "RULE_001",
  "source": "Northstar Brand Guidelines",
  "excerpt": "Do not promise guaranteed results..."
}
```

### ReviewResponse

```json
{
  "review_id": "review-abc123",
  "status": "changes_requested",
  "findings": [...],
  "degraded_mode": false,
  "provider_error": null
}
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trueline --cov-report=term-missing

# Run specific test file
pytest tests/test_deterministic.py -v
pytest tests/test_service.py -v
pytest tests/test_providers.py -v
pytest tests/test_models.py -v
```

### Test Coverage

Tests cover:
- ✅ Valid findings with exact offset verification
- ✅ No findings for clean drafts
- ✅ Missing guideline evidence (empty guidelines)
- ✅ Invalid model output (malformed JSON, non-array, wrong types)
- ✅ Provider errors (API key missing, API errors, network failures)
- ✅ Citation validation (unknown rule_ids rejected)
- ✅ Offset validation (mismatched offsets rejected)
- ✅ Deterministic findings preserved during AI provider failure
- ✅ Deduplication of overlapping findings
- ✅ Status determination (approved, changes_requested, needs_human_review)

## Integration Notes for Kushal

1. **Import**: `from trueline import ReviewEngine, ReviewRequest, Guideline, ApprovedFact`
2. **Instantiate once**: Create `ReviewEngine()` at startup, reuse for all requests
3. **Async**: `engine.review(request)` is async - use `await` in FastAPI endpoint
4. **No FastAPI dependency**: Engine is framework-agnostic
5. **Error handling**: Check `response.degraded_mode` and `response.provider_error`
6. **Logging**: Uses standard `logging` module - configure in your app

## Schema Status

⚠️ **PROVISIONAL** - The Finding schema, Category enum, and ReviewResponse are based on the current frontend proposal and have not been formally approved by the team. Expect changes after Kushal, Nimra, and Vandana review.

## License

Internal use only - Team AETHERON