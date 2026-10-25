"""
Pydantic models for the Trueline AI Review Engine.

PROVISIONAL SCHEMA - Subject to team review and approval.
This schema is based on the current frontend proposal and has not been
formally approved by Kushal, Nimra, and Vandana.
"""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class Severity(StrEnum):
    """Finding severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Category(StrEnum):
    """Finding categories - provisional until team agrees on shared enum."""
    BANNED_TERM = "banned_term"
    TONE = "tone"
    MISSING_DISCLAIMER = "missing_disclaimer"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    PREFERRED_TERMINOLOGY = "preferred_terminology"
    REQUIRED_PHRASE = "required_phrase"
    PRODUCT_NAME_INCONSISTENCY = "product_name_inconsistency"
    FORMATTING = "formatting"
    MISSING_CONTENT = "missing_content"
    LENGTH_LIMIT = "length_limit"


class ReviewStatus(StrEnum):
    """Overall review status."""
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class Citation(BaseModel):
    """Supporting guideline evidence for a finding."""
    rule_id: str = Field(..., description="Unique identifier of the guideline rule")
    source: str = Field(..., description="Guideline document name")
    excerpt: str = Field(..., description="Relevant excerpt from the guideline text")

    model_config = {"extra": "forbid"}


class Finding(BaseModel):
    """
    A brand violation finding with exact text offsets and citation.

    Validation rules:
    - start and end: zero-based Python string indices (exclusive end)
    - draft_text[start:end] must equal matched_text (validated externally)
    - confidence must be between 0.0 and 1.0
    - Citations must be grounded in supplied approved guidelines
    - Missing citation or suggested_fix must be null, not invented content
    """
    id: str = Field(default_factory=lambda: f"finding-{uuid4().hex[:8]}")
    matched_text: str = Field(..., description="Exact text from the original draft")
    start: int = Field(..., ge=0, description="Zero-based start offset (inclusive)")
    end: int = Field(..., ge=0, description="Zero-based end offset (exclusive)")
    category: Category
    severity: Severity
    explanation: str = Field(..., description="Why the content may violate a guideline")
    citation: Citation | None = Field(None, description="Supporting guideline evidence")
    suggested_fix: str | None = Field(None, description="Proposed correction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    requires_human_review: bool = Field(
        ..., description="Whether a human should verify the finding"
    )

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: int, info: ValidationInfo) -> int:
        if "start" in info.data and v < info.data["start"]:
            raise ValueError("end must be >= start")
        return v

    model_config = {"extra": "forbid"}


class Guideline(BaseModel):
    """Approved brand guideline evidence."""
    id: str = Field(..., description="Unique guideline identifier")
    title: str | None = Field(None, description="Short description")
    text: str = Field(..., description="The approved guideline text")
    category: str = Field(..., description="Rule category")
    source: str = Field(..., description="Guideline document name")

    model_config = {"extra": "forbid"}


class ApprovedFact(BaseModel):
    """Approved brand fact for factual accuracy checks."""
    id: str = Field(..., description="Unique fact identifier")
    claim: str = Field(..., description="The approved factual claim")
    evidence: str = Field(..., description="Supporting evidence or source")
    category: str = Field(..., description="Fact category")

    model_config = {"extra": "forbid"}


class ReviewRequest(BaseModel):
    """Input for the review engine."""
    draft_text: str = Field(..., description="The content to review")
    brand_id: str = Field(..., description="Brand identifier")
    content_purpose: str = Field(..., description="Purpose/context of the content")
    guidelines: list[Guideline] = Field(
        default_factory=list, description="Approved brand guidelines"
    )
    approved_facts: list[ApprovedFact] = Field(
        default_factory=list, description="Approved brand facts"
    )

    model_config = {"extra": "forbid"}


class ReviewResponse(BaseModel):
    """Output from the review engine."""
    review_id: str = Field(default_factory=lambda: f"review-{uuid4().hex[:8]}")
    status: ReviewStatus
    findings: list[Finding] = Field(default_factory=list)
    degraded_mode: bool = Field(
        False,
        description="True if AI provider failed and only deterministic results returned",
    )
    provider_error: str | None = Field(None, description="Error message if AI provider failed")

    model_config = {"extra": "forbid"}
