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
    """Finding categories - provisional until team agrees on shared enum.

    Includes both original categories and Northstar dataset categories.
    """
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
    # Northstar dataset categories
    NAMING = "naming"
    TERMINOLOGY = "terminology"
    BANNED_LANGUAGE = "banned_language"
    REQUIRED_WORDING = "required_wording"
    CLAIMS = "claims"
    # Fact-related categories (for fact expiry/supersession and approved fact matches)
    FACT_METADATA = "fact_metadata"
    APPROVED_FACT = "approved_fact"


class FindingLabel(StrEnum):
    """Finding label from Northstar dataset evaluation.

    Indicates the type of finding for routing and reporting.
    """
    VIOLATION = "violation"
    NEEDS_HUMAN_JUDGEMENT = "needs_human_judgement"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    OUTDATED = "outdated"


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
    document_id: str | None = Field(
        None, description="Guideline document ID (e.g., NS-DOC-EDITORIAL)"
    )
    section: str | None = Field(
        None, description="Section within the guideline document"
    )

    model_config = {"extra": "forbid"}


class Finding(BaseModel):
    """
    A brand violation finding with exact text offsets and citation.

    Validation rules:
    - start and end: zero-based Unicode code point offsets (exclusive end)
    - draft_text[start:end] must equal matched_text (validated externally)
    - confidence must be between 0.0 and 1.0
    - Citations must be grounded in supplied approved guidelines
    - Missing citation or suggested_fix must be null, not invented content
    """
    id: str = Field(default_factory=lambda: f"finding-{uuid4().hex[:8]}")
    matched_text: str = Field(..., description="Exact text from the original draft")
    start: int = Field(
        ..., ge=0, description="Zero-based start offset (inclusive), Unicode code points"
    )
    end: int = Field(
        ..., ge=0, description="Zero-based end offset (exclusive), Unicode code points"
    )
    category: Category
    severity: Severity
    explanation: str = Field(..., description="Why the content may violate a guideline")
    citation: Citation | None = Field(None, description="Supporting guideline evidence")
    suggested_fix: str | None = Field(None, description="Proposed correction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    requires_human_review: bool = Field(
        ..., description="Whether a human should verify the finding"
    )
    label: FindingLabel | None = Field(
        None, description="Finding label for routing (violation, needs_human_judgement, etc.)"
    )
    rule_id: str | None = Field(
        None, description="Source rule/guideline ID that produced this finding"
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
    version: str | None = Field(
        None, description="Version of the approved guideline source, if recorded"
    )
    document_id: str | None = Field(
        None, description="Guideline document ID (e.g., NS-DOC-EDITORIAL)"
    )
    section: str | None = Field(
        None, description="Section within the guideline document"
    )
    patterns: list[str] = Field(
        default_factory=list, description="Explicit regex patterns for computed checks"
    )
    check_method: str | None = Field(
        None, description="Check method: computed, ai, or hybrid"
    )
    match_type: str | None = Field(
        None, description="Match type: term, regex, required_phrase, length_limit, etc."
    )
    severity_default: str | None = Field(
        None, description="Default severity: low, medium, high"
    )
    required_phrase: str | None = Field(
        None, description="Required phrase for required_wording rules"
    )
    trigger: str | None = Field(
        None, description="Trigger condition for required_wording rules"
    )
    case_sensitive: bool | None = Field(
        None,
        description=(
            "Whether pattern matching is case-sensitive "
            "(default: False for regex, True for term)"
        ),
    )

    model_config = {"extra": "forbid"}


class ApprovedFact(BaseModel):
    """Approved brand fact for factual accuracy checks."""
    id: str = Field(..., description="Unique fact identifier")
    claim: str = Field(..., description="The approved factual claim")
    evidence: str = Field(..., description="Supporting evidence or source")
    source_version: str | None = Field(
        None, description="Version of the approved fact source, if recorded"
    )
    category: str = Field(..., description="Fact category")
    valid_from: str | None = Field(
        None, description="ISO date when fact becomes valid"
    )
    expires_on: str | None = Field(
        None, description="ISO date when fact expires"
    )
    status_on_evaluation_date: str | None = Field(
        None, description="Status on evaluation date: active, expired, superseded"
    )
    superseded_by: str | None = Field(
        None, description="ID of fact that supersedes this one"
    )

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
    evaluation_date: str | None = Field(
        None, description="ISO date for fact status evaluation (default: today)"
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
