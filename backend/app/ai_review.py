"""Optional bridge from the FastAPI backend to the AI review engine.

The backend deterministic rule engine remains authoritative for computed
rules. This bridge only sends guidelines explicitly marked ``ai`` or ``hybrid``
to the AI engine, converts its findings into backend ``FindingDraft`` objects,
and rejects any citation that cannot be grounded in the loaded database rows.

If the ``trueline`` package is not installed, the bridge is disabled and the
backend continues to run deterministically.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import Any

from .ai_labels import AILabel
from .models import ApprovedFact as FactRow
from .models import Guideline as GuidelineRow
from .rule_engine.models import CitationDraft, FindingDraft

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised through the available/unavailable paths
    from trueline.adapters.fastapi_adapter import convert_review_response
    from trueline.models import ApprovedFact as AIFact
    from trueline.models import Guideline as AIGuideline
    from trueline.models import ReviewRequest as AIReviewRequest
    from trueline.providers.base import AIProvider
    from trueline.review.service import create_review_engine

    AI_ENGINE_AVAILABLE = True
except Exception:  # pragma: no cover - depends on optional install
    convert_review_response = None  # type: ignore[assignment]
    AIFact = None  # type: ignore[assignment,misc]
    AIGuideline = None  # type: ignore[assignment,misc]
    AIReviewRequest = None  # type: ignore[assignment,misc]
    AIProvider = None  # type: ignore[assignment,misc]
    create_review_engine = None  # type: ignore[assignment]
    AI_ENGINE_AVAILABLE = False


AI_CATEGORY_MAP: dict[str, str] = {
    "tone": "tone",
    "naming": "naming",
    "terminology": "terminology",
    "banned_language": "banned_language",
    "banned_term": "banned_term",
    "required_wording": "required_wording",
    "required_phrase": "required_wording",
    "formatting": "formatting",
    "claims": "claims",
    "unsupported_claim": "unsupported_claim",
    "preferred_terminology": "preferred_terminology",
    "product_name": "product_name_inconsistency",
    "length_limit": "length_limit",
    "missing_content": "missing_content",
}


def _config(row: GuidelineRow) -> dict[str, Any]:
    return row.config_json or {}


def _ai_check_method(row: GuidelineRow) -> str:
    value = str(_config(row).get("check_method", "computed")).strip().lower()
    return value if value in {"computed", "ai", "hybrid"} else "computed"


def _to_ai_guideline(row: GuidelineRow) -> Any:
    """Convert a database guideline row into an AI-engine guideline."""
    config = _config(row)
    backend_category = row.category.strip().lower()
    ai_category = AI_CATEGORY_MAP.get(backend_category, "banned_term")

    patterns = [str(item) for item in config.get("patterns", []) if str(item).strip()]
    required_phrase = config.get("required_phrase")
    trigger_patterns = [
        str(item) for item in config.get("trigger_patterns", []) if str(item).strip()
    ]

    if backend_category in {"required_phrase", "required_wording"}:
        # A backend required_phrase rule stores the phrase itself in patterns.
        # It is not a trigger. Explicit trigger_patterns are opt-in.
        if not required_phrase and len(patterns) == 1:
            required_phrase = patterns[0]
        patterns = []

    return AIGuideline(
        id=row.rule_id,
        title=row.title,
        text=row.content,
        category=ai_category,
        source=row.title,
        version=row.version,
        document_id=row.id,
        section=row.section,
        patterns=patterns,
        trigger_patterns=trigger_patterns,
        check_method=_ai_check_method(row),
        match_type=row.match_type,
        severity_default=row.severity,
        required_phrase=required_phrase,
        case_sensitive=bool(config.get("case_sensitive", False)),
    )


def _to_ai_fact(row: FactRow) -> Any:
    return AIFact(
        id=row.id,
        claim=row.statement,
        evidence=row.source_label,
        source_version=row.source_version,
        category="fact",
        valid_from=row.valid_from.isoformat() if row.valid_from else None,
        expires_on=row.valid_until.isoformat() if row.valid_until else None,
    )


def build_ai_inputs(
    guidelines: list[GuidelineRow], facts: list[FactRow]
) -> tuple[list[Any], list[Any]]:
    """Convert DB rows and keep only guidelines marked ai/hybrid."""
    ai_guidelines = [
        _to_ai_guideline(row)
        for row in guidelines
        if _ai_check_method(row) in {"ai", "hybrid"}
    ]
    return ai_guidelines, [_to_ai_fact(row) for row in facts]


def _sanitize_citation(
    finding: FindingDraft,
    guideline_rows: dict[str, GuidelineRow],
    fact_rows: dict[str, FactRow],
) -> FindingDraft:
    """Drop a citation that is not grounded in the loaded database rows."""
    citation = finding.citation
    if citation is None:
        return finding

    if citation.source_type == "guideline":
        row = guideline_rows.get(citation.source_id)
        valid = (
            row is not None
            and row.rule_id == finding.rule_id
            and (row.version or None) == (citation.source_version or None)
            and bool(citation.quoted_text)
            and citation.quoted_text in row.content
        )
    elif citation.source_type == "approved_fact":
        fact = fact_rows.get(citation.source_id)
        valid = (
            fact is not None
            and (fact.source_version or None) == (citation.source_version or None)
            and bool(citation.quoted_text)
            and citation.quoted_text in fact.statement
        )
    else:
        valid = False

    if valid:
        return finding

    logger.warning(
        "Dropping ungrounded AI citation on finding %s (%s)",
        finding.rule_id,
        citation.source_id,
    )
    return FindingDraft(
        rule_id=finding.rule_id,
        matched_text=finding.matched_text,
        start=finding.start,
        end=finding.end,
        category=finding.category,
        severity=finding.severity,
        explanation=finding.explanation,
        citation=None,
        suggested_fix=finding.suggested_fix,
        confidence=finding.confidence,
        requires_human_review=True,
        ai_label=finding.ai_label,
    )


def _to_finding_draft(
    response: Any,
    draft_text: str,
    guideline_rows: list[GuidelineRow],
    fact_rows: list[FactRow],
) -> list[FindingDraft]:
    """Convert an AI response into backend finding drafts."""
    ai_guidelines = [_to_ai_guideline(row) for row in guideline_rows]
    ai_facts = [_to_ai_fact(row) for row in fact_rows]
    fastapi_response = convert_review_response(
        response, draft_text, ai_guidelines, ai_facts
    )

    guideline_by_id = {row.id: row for row in guideline_rows}
    fact_by_id = {row.id: row for row in fact_rows}
    drafts: list[FindingDraft] = []

    for finding in fastapi_response.findings:
        citation = None
        if finding.citation is not None:
            citation = CitationDraft(
                source_type=finding.citation.source_type.value,
                source_id=finding.citation.source_id,
                source_version=finding.citation.source_version,
                source_label=finding.citation.source,
                quoted_text=finding.citation.quoted_text,
                valid_until=finding.citation.valid_until,
            )

        draft = FindingDraft(
            rule_id=finding.rule_id,
            matched_text=finding.matched_text,
            start=finding.start,
            end=finding.end,
            category=finding.category.value,
            severity=finding.severity.value,
            explanation=finding.explanation,
            citation=citation,
            suggested_fix=finding.suggested_fix,
            confidence=finding.confidence,
            requires_human_review=finding.requires_human_review,
            ai_label=AILabel(finding.ai_label.upper()) if finding.ai_label else None,
        )
        drafts.append(_sanitize_citation(draft, guideline_by_id, fact_by_id))

    return drafts


def run_ai_review(
    *,
    draft_text: str,
    brand_id: str,
    purpose: str,
    guidelines: list[GuidelineRow],
    facts: list[FactRow],
    evaluation_date: date,
    provider: Any | None = None,
) -> list[FindingDraft]:
    """Run the optional AI review and return backend finding drafts.

    Only guidelines marked ``ai`` or ``hybrid`` are sent to the model. The
    caller is responsible for checking ``AI_ENGINE_AVAILABLE`` and for handling
    provider failures according to its degraded-mode policy.
    """
    if not AI_ENGINE_AVAILABLE:
        return []

    ai_guidelines, ai_facts = build_ai_inputs(guidelines, facts)
    if not ai_guidelines:
        return []

    engine = create_review_engine(ai_provider=provider)
    request = AIReviewRequest(
        draft_text=draft_text,
        brand_id=brand_id,
        content_purpose=purpose,
        guidelines=ai_guidelines,
        approved_facts=ai_facts,
        evaluation_date=evaluation_date.isoformat(),
    )
    response = asyncio.run(engine.review(request))
    return _to_finding_draft(response, draft_text, guidelines, facts)
