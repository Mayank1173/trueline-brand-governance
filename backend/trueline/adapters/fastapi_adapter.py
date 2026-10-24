"""Adapter between AI Review Engine models and FastAPI backend schemas.

This module provides pure conversion functions with no business logic.
All business logic remains in the AI engine and FastAPI rule engine respectively.
"""

from datetime import date
from enum import StrEnum

from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    FindingLabel,
    Guideline,
    ReviewStatus,
    Severity,
)
from trueline.models import (
    ReviewRequest as AIReviewRequest,
)
from trueline.models import (
    ReviewResponse as AIReviewResponse,
)


class FastAPICategory(StrEnum):
    """FastAPI backend accepted categories (from schemas.py)."""
    UNSUPPORTED_CLAIM = "unsupported_claim"
    BANNED_TERM = "banned_term"
    PREFERRED_TERMINOLOGY = "preferred_terminology"
    REQUIRED_PHRASE = "required_phrase"
    PRODUCT_NAME = "product_name"
    FORMATTING = "formatting"
    LENGTH_LIMIT = "length_limit"
    TONE = "tone"
    FACT_METADATA = "fact_metadata"
    MISSING_CONTENT = "missing_content"
    APPROVED_FACT = "approved_fact"


class FastAPISeverity(StrEnum):
    """FastAPI backend severity values."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FastAPIReviewStatus(StrEnum):
    """FastAPI backend review status values."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    APPROVED = "approved"


class FastAPISourceType(StrEnum):
    """FastAPI citation source types."""
    GUIDELINE = "guideline"
    APPROVED_FACT = "approved_fact"
    BRAND_CONFIG = "brand_config"


# ──────────────────────────────────────────────────────────────────────────────
# Category Mapping
# ──────────────────────────────────────────────────────────────────────────────

_AI_TO_FASTAPI_CATEGORY: dict[Category, FastAPICategory] = {
    Category.BANNED_TERM: FastAPICategory.BANNED_TERM,
    Category.BANNED_LANGUAGE: FastAPICategory.BANNED_TERM,
    Category.UNSUPPORTED_CLAIM: FastAPICategory.UNSUPPORTED_CLAIM,
    Category.CLAIMS: FastAPICategory.UNSUPPORTED_CLAIM,
    Category.PREFERRED_TERMINOLOGY: FastAPICategory.PREFERRED_TERMINOLOGY,
    Category.TERMINOLOGY: FastAPICategory.PREFERRED_TERMINOLOGY,
    Category.REQUIRED_PHRASE: FastAPICategory.REQUIRED_PHRASE,
    Category.REQUIRED_WORDING: FastAPICategory.REQUIRED_PHRASE,
    Category.MISSING_DISCLAIMER: FastAPICategory.REQUIRED_PHRASE,
    Category.PRODUCT_NAME_INCONSISTENCY: FastAPICategory.PRODUCT_NAME,
    Category.NAMING: FastAPICategory.PRODUCT_NAME,
    Category.TONE: FastAPICategory.TONE,
    Category.FORMATTING: FastAPICategory.FORMATTING,
    Category.LENGTH_LIMIT: FastAPICategory.LENGTH_LIMIT,
    Category.MISSING_CONTENT: FastAPICategory.MISSING_CONTENT,
    Category.FACT_METADATA: FastAPICategory.FACT_METADATA,
    Category.APPROVED_FACT: FastAPICategory.APPROVED_FACT,
}

# Categories with no direct AI equivalent (deterministic-only in FastAPI)
_FASTAPI_ONLY_CATEGORIES: set[FastAPICategory] = set()


def map_category(ai_category: Category) -> FastAPICategory:
    """Map AI engine category to FastAPI category.

    Args:
        ai_category: Category from AI engine

    Returns:
        Corresponding FastAPI category

    Note:
        Some FastAPI categories (fact_metadata, approved_fact) have no AI
        equivalent and are only used by the deterministic rule engine.
    """
    return _AI_TO_FASTAPI_CATEGORY.get(ai_category, FastAPICategory.UNSUPPORTED_CLAIM)


def map_severity(ai_severity: Severity) -> FastAPISeverity:
    """Map AI severity to FastAPI severity (direct mapping)."""
    return FastAPISeverity(ai_severity.value)


def map_status(ai_status: ReviewStatus) -> FastAPIReviewStatus:
    """Map AI review status to FastAPI review status (direct mapping for shared values)."""
    return FastAPIReviewStatus(ai_status.value)


# ──────────────────────────────────────────────────────────────────────────────
# Offset Conversion (Unicode code points ↔ UTF-16 code units)
# ──────────────────────────────────────────────────────────────────────────────

def _build_utf16_offset_map(text: str) -> list[int]:
    """Build prefix array mapping Unicode code point index to UTF-16 code unit offset.

    Args:
        text: The source text

    Returns:
        List where index i gives the UTF-16 offset of Unicode code point i.
        Length is len(text) + 1.
    """
    prefix = [0]
    total = 0
    for ch in text:
        # BMP characters: 1 UTF-16 code unit; non-BMP (surrogate pairs): 2
        total += 2 if ord(ch) > 0xFFFF else 1
        prefix.append(total)
    return prefix


def unicode_to_utf16_offset(text: str, unicode_index: int) -> int:
    """Convert Unicode code point offset to UTF-16 code unit offset.

    Args:
        text: The source text
        unicode_index: Zero-based Unicode code point index (0 <= index <= len(text))

    Returns:
        Zero-based UTF-16 code unit offset

    Raises:
        IndexError: If unicode_index is out of bounds
    """
    if unicode_index < 0 or unicode_index > len(text):
        raise IndexError(f"unicode_index {unicode_index} out of bounds for text length {len(text)}")
    offset_map = _build_utf16_offset_map(text)
    return offset_map[unicode_index]


def utf16_to_unicode_offset(text: str, utf16_index: int) -> int:
    """Convert UTF-16 code unit offset to Unicode code point index.

    Args:
        text: The source text
        utf16_index: Zero-based UTF-16 code unit offset

    Returns:
        Zero-based Unicode code point index

    Raises:
        IndexError: If utf16_index is out of bounds
    """
    if utf16_index < 0:
        raise IndexError(f"utf16_index {utf16_index} cannot be negative")

    offset_map = _build_utf16_offset_map(text)
    max_utf16 = offset_map[-1]
    if utf16_index > max_utf16:
        raise IndexError(f"utf16_index {utf16_index} out of bounds (max {max_utf16})")

    # Binary search for the Unicode index
    lo, hi = 0, len(offset_map) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if offset_map[mid] <= utf16_index:
            lo = mid
        else:
            hi = mid - 1
    return lo


# ──────────────────────────────────────────────────────────────────────────────
# Citation Conversion
# ──────────────────────────────────────────────────────────────────────────────

class FastAPICitationOut:
    """FastAPI CitationOut schema (matching backend/app/schemas.py)."""

    def __init__(
        self,
        rule_id: str,
        source: str,
        excerpt: str,
        source_type: FastAPISourceType,
        source_id: str,
        source_version: str | None,
        quoted_text: str,
        valid_until: date | None = None,
    ):
        self.rule_id = rule_id
        self.source = source
        self.excerpt = excerpt
        self.source_type = source_type
        self.source_id = source_id
        self.source_version = source_version
        self.quoted_text = quoted_text
        self.valid_until = valid_until

    def model_dump(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "source": self.source,
            "excerpt": self.excerpt,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "source_version": self.source_version,
            "quoted_text": self.quoted_text,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
        }


def convert_citation(
    ai_citation: Citation | None,
    draft_text: str,
    guideline: Guideline | None = None,
    approved_fact: ApprovedFact | None = None,
) -> FastAPICitationOut | None:
    """Convert AI engine Citation to FastAPI CitationOut.

    Args:
        ai_citation: Citation from AI engine (may be None)
        draft_text: Original draft text (for quoted_text verification)
        guideline: Source guideline if available (for metadata enrichment)
        approved_fact: Source approved fact if available (for metadata enrichment)

    Returns:
        FastAPICitationOut or None if ai_citation is None

    Note:
        - source_version comes from the approved guideline/fact metadata when
          available and is null otherwise. The adapter never invents a version.
        - valid_until is only derived from an approved fact's expiry date.
    """
    if ai_citation is None:
        return None

    # Determine source type and enrich metadata from the approved source.
    # Never invent a version: null means the source has no recorded version.
    if approved_fact is not None:
        source_type = FastAPISourceType.APPROVED_FACT
        source_id = approved_fact.id
        source_version = approved_fact.source_version
        quoted_text = approved_fact.claim
        valid_until = None
        if approved_fact.expires_on:
            try:
                valid_until = date.fromisoformat(approved_fact.expires_on)
            except ValueError:
                pass
    else:
        source_type = FastAPISourceType.GUIDELINE
        source_id = (
            guideline.id
            if guideline is not None
            else (ai_citation.document_id or ai_citation.rule_id)
        )
        source_version = guideline.version if guideline is not None else None
        quoted_text = ai_citation.excerpt
        valid_until = None

    return FastAPICitationOut(
        rule_id=ai_citation.rule_id,
        source=ai_citation.source,
        excerpt=ai_citation.excerpt,
        source_type=source_type,
        source_id=source_id,
        source_version=source_version,
        quoted_text=quoted_text,
        valid_until=valid_until,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Finding Conversion
# ──────────────────────────────────────────────────────────────────────────────

class FastAPIFindingResponse:
    """FastAPI FindingResponse schema (matching backend/app/schemas.py)."""

    def __init__(
        self,
        id: str,
        finding_id: str,
        rule_id: str,
        matched_text: str,
        start: int | None,
        end: int | None,
        category: FastAPICategory,
        severity: FastAPISeverity,
        explanation: str,
        citation: FastAPICitationOut | None,
        suggested_fix: str | None,
        confidence: float,
        requires_human_review: bool,
        ai_label: str | None = None,
    ):
        self.id = id
        self.finding_id = finding_id
        self.rule_id = rule_id
        self.matched_text = matched_text
        self.start = start
        self.end = end
        self.category = category
        self.severity = severity
        self.explanation = explanation
        self.citation = citation
        self.suggested_fix = suggested_fix
        self.confidence = confidence
        self.requires_human_review = requires_human_review
        self.ai_label = ai_label

    def model_dump(self) -> dict[str, object]:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "rule_id": self.rule_id,
            "matched_text": self.matched_text,
            "start": self.start,
            "end": self.end,
            "category": self.category.value,
            "severity": self.severity.value,
            "explanation": self.explanation,
            "citation": self.citation.model_dump() if self.citation else None,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
            "requires_human_review": self.requires_human_review,
            "ai_label": self.ai_label,
        }


def _derive_requires_human_review(finding: Finding) -> bool:
    """Determine requires_human_review from finding fields including label."""
    if finding.requires_human_review:
        return True
    if finding.label == FindingLabel.NEEDS_HUMAN_JUDGEMENT:
        return True
    # High severity non-violation labels also need human review
    if finding.severity == Severity.HIGH and finding.label in (
        FindingLabel.UNSUPPORTED,
        FindingLabel.CONTRADICTED,
        FindingLabel.OUTDATED,
    ):
        return True
    return False


def _derive_rule_id(finding: Finding, guideline: Guideline | None = None) -> str:
    """Extract or derive rule_id for FastAPI requirement.

    FastAPI requires rule_id at top level. AI engine now has it in finding.rule_id.
    Priority: finding.rule_id > citation.rule_id > guideline.id > category fallback.
    """
    if finding.rule_id:
        return finding.rule_id
    if finding.citation and finding.citation.rule_id:
        return finding.citation.rule_id
    if guideline:
        return guideline.id
    # Fallback: use category as rule_id prefix
    return f"rule-{finding.category.value}"


def convert_finding_to_response(
    finding: Finding,
    draft_text: str,
    guideline: Guideline | None = None,
    approved_fact: ApprovedFact | None = None,
) -> FastAPIFindingResponse:
    """Convert AI engine Finding to FastAPI FindingResponse.

    Args:
        finding: Finding from AI engine
        draft_text: Original draft text (for offset conversion)
        guideline: Source guideline if available (for rule_id, citation metadata)
        approved_fact: Source approved fact if available (for citation metadata)

    Returns:
        FastAPIFindingResponse with UTF-16 offsets and FastAPI categories
    """
    # Convert offsets from Unicode code points to UTF-16 code units
    if finding.start is not None and finding.end is not None and finding.matched_text:
        start_utf16 = unicode_to_utf16_offset(draft_text, finding.start)
        end_utf16 = unicode_to_utf16_offset(draft_text, finding.end)
    else:
        # Missing phrase or length limit findings have no offsets
        start_utf16 = None
        end_utf16 = None

    # Map category
    fastapi_category = map_category(finding.category)

    # Convert citation
    fastapi_citation = convert_citation(
        finding.citation,
        draft_text,
        guideline=guideline,
        approved_fact=approved_fact,
    )

    # Determine requires_human_review (includes label-based logic)
    requires_human = _derive_requires_human_review(finding)

    # Derive rule_id
    rule_id = _derive_rule_id(finding, guideline)

    return FastAPIFindingResponse(
        id=finding.id,
        finding_id=finding.id,  # Same value per FastAPI contract
        rule_id=rule_id,
        matched_text=finding.matched_text,
        start=start_utf16,
        end=end_utf16,
        category=fastapi_category,
        severity=map_severity(finding.severity),
        explanation=finding.explanation,
        citation=fastapi_citation,
        suggested_fix=finding.suggested_fix,
        confidence=finding.confidence,
        requires_human_review=requires_human,
        ai_label=finding.label.value if finding.label is not None else None,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Request/Response Conversion
# ──────────────────────────────────────────────────────────────────────────────

class FastAPIReviewRequest:
    """FastAPI ReviewRequest schema (matching backend/app/schemas.py)."""

    def __init__(self, brand_id: str, draft_text: str, purpose: str = "general"):
        self.brand_id = brand_id
        self.draft_text = draft_text
        self.purpose = purpose

    def model_dump(self) -> dict[str, object]:
        return {
            "brand_id": self.brand_id,
            "draft_text": self.draft_text,
            "purpose": self.purpose,
        }


def convert_review_request(
    fastapi_request: FastAPIReviewRequest,
    guidelines: list[Guideline],
    approved_facts: list[ApprovedFact],
    evaluation_date: date | None = None,
) -> AIReviewRequest:
    """Convert FastAPI ReviewRequest to AI engine ReviewRequest.

    Args:
        fastapi_request: Request from FastAPI endpoint
        guidelines: Brand guidelines loaded from database
        approved_facts: Brand approved facts loaded from database
        evaluation_date: Optional evaluation date (defaults to today)

    Returns:
        AIReviewRequest for the AI engine
    """
    return AIReviewRequest(
        draft_text=fastapi_request.draft_text,
        brand_id=fastapi_request.brand_id,
        content_purpose=fastapi_request.purpose,
        guidelines=guidelines,
        approved_facts=approved_facts,
        evaluation_date=evaluation_date.isoformat() if evaluation_date else None,
    )


class FastAPIReviewResponse:
    """FastAPI ReviewResponse schema (matching backend/app/schemas.py)."""

    def __init__(
        self,
        review_id: str,
        status: FastAPIReviewStatus,
        findings: list[FastAPIFindingResponse],
    ):
        self.review_id = review_id
        self.status = status
        self.findings = findings

    def model_dump(self) -> dict[str, object]:
        return {
            "review_id": self.review_id,
            "status": self.status.value,
            "findings": [f.model_dump() for f in self.findings],
        }


def convert_review_response(
    ai_response: AIReviewResponse,
    draft_text: str,
    guidelines: list[Guideline],
    approved_facts: list[ApprovedFact],
) -> FastAPIReviewResponse:
    """Convert AI engine ReviewResponse to FastAPI ReviewResponse.

    Args:
        ai_response: Response from AI engine
        draft_text: Original draft text (for offset conversion)
        guidelines: Brand guidelines (for citation metadata)
        approved_facts: Brand approved facts (for citation metadata)

    Returns:
        FastAPIReviewResponse with converted findings
    """
    # Build lookups for citation enrichment
    guideline_by_id = {g.id: g for g in guidelines}
    fact_by_id = {f.id: f for f in approved_facts}

    fastapi_findings = []
    for finding in ai_response.findings:
        # Find associated guideline/fact for metadata enrichment
        guideline = None
        approved_fact = None
        if finding.citation and finding.citation.rule_id:
            guideline = guideline_by_id.get(finding.citation.rule_id)
            # Also check if citation references a fact
            if not guideline:
                approved_fact = fact_by_id.get(finding.citation.rule_id)

        fastapi_finding = convert_finding_to_response(
            finding,
            draft_text,
            guideline=guideline,
            approved_fact=approved_fact,
        )
        fastapi_findings.append(fastapi_finding)

    return FastAPIReviewResponse(
        review_id=ai_response.review_id,
        status=map_status(ai_response.status),
        findings=fastapi_findings,
    )
