"""Pydantic v2 request/response schemas.

The public response is a compatible superset of the frontend contract in
``frontend/src/lib/types.ts``:

* ``FindingResponse.id`` is kept for the existing frontend.
* ``FindingResponse.finding_id`` is also returned for the backend/leader spec.
* ``FindingResponse.ai_label`` is the nullable original AI label; deterministic
  findings leave it ``null`` while retaining ``category`` and ``severity``.
* ``CitationOut`` contains both the frontend fields (``rule_id``, ``source``,
  ``excerpt``) and the grounded source metadata (``source_type``,
  ``source_id``, ``source_version``, ``quoted_text``, ``valid_until``).
  ``source_version`` is ``null`` when the approved source has no recorded
  version; the backend never invents one.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .ai_labels import AILabel


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ReviewStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    changes_requested = "changes_requested"
    needs_human_review = "needs_human_review"
    approved = "approved"


class FindingCategory(str, Enum):
    unsupported_claim = "unsupported_claim"
    banned_term = "banned_term"
    preferred_terminology = "preferred_terminology"
    required_phrase = "required_phrase"
    product_name = "product_name"
    formatting = "formatting"
    length_limit = "length_limit"
    tone = "tone"
    fact_metadata = "fact_metadata"
    missing_content = "missing_content"
    approved_fact = "approved_fact"


class SourceType(str, Enum):
    guideline = "guideline"
    approved_fact = "approved_fact"
    brand_config = "brand_config"


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_id: str = Field(min_length=1, max_length=64)
    draft_text: str = Field(min_length=1, max_length=2_000_000)
    purpose: str | None = Field(default=None, max_length=1_000)

    @field_validator("brand_id")
    @classmethod
    def _clean_brand_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("brand_id must not be empty")
        return value

    @field_validator("draft_text")
    @classmethod
    def _require_non_blank_draft(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("draft_text must not be empty or whitespace-only")
        return value

    @field_validator("purpose")
    @classmethod
    def _clean_purpose(cls, value: str | None) -> str:
        if value is None:
            return "general"
        value = value.strip()
        return value or "general"


class CitationOut(BaseModel):
    # Frontend contract
    rule_id: str
    source: str
    excerpt: str

    # Grounded source metadata (leader/rule-engine contract)
    source_type: SourceType
    source_id: str
    source_version: str | None
    quoted_text: str
    valid_until: date | None = None


class FindingResponse(BaseModel):
    id: str
    finding_id: str
    rule_id: str
    matched_text: str
    start: int | None = None
    end: int | None = None
    category: str
    severity: Severity
    explanation: str
    citation: CitationOut | None = None
    suggested_fix: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool
    ai_label: AILabel | None = None


class ReviewResponse(BaseModel):
    review_id: str
    status: ReviewStatus
    findings: list[FindingResponse]


class ReviewSummary(BaseModel):
    review_id: str
    brand_id: str
    purpose: str
    status: ReviewStatus
    finding_count: int
    requires_human_review_count: int
    created_at: datetime
    updated_at: datetime


class ReviewDetail(ReviewSummary):
    draft_text: str
    ruleset_version: str
    engine_version: str
    evaluation_date: date
    findings: list[FindingResponse]


class ReviewListResponse(BaseModel):
    items: list[ReviewSummary]
    total: int
    limit: int
    offset: int


class ReviewEventResponse(BaseModel):
    id: str
    event_type: str
    actor_type: str
    actor: str
    action: str
    comment: str | None = None
    at: datetime


class ReviewHistoryResponse(BaseModel):
    review_id: str
    events: list[ReviewEventResponse]


class BrandResponse(BaseModel):
    id: str
    name: str
    description: str | None = None


class GuidelineResponse(BaseModel):
    source_id: str
    rule_id: str
    title: str
    section: str | None = None
    version: str | None
    content: str
    category: str
    severity: Severity
    match_type: str
    explanation: str
    suggested_fix: str | None = None
    confidence: float
    requires_human_review: bool


class ApprovedFactResponse(BaseModel):
    source_id: str
    statement: str
    source: str
    source_version: str | None
    valid_from: date | None = None
    valid_until: date | None = None
    is_current: bool


class BrandGuidelinesResponse(BaseModel):
    brand: BrandResponse
    guidelines: list[GuidelineResponse]


class BrandFactsResponse(BaseModel):
    brand: BrandResponse
    approved_facts: list[ApprovedFactResponse]


class HealthResponse(BaseModel):
    status: str
    database: str
    environment: str
    version: str
