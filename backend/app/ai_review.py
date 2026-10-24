"""Optional bridge from the FastAPI backend to the AI review engine.

The backend deterministic rule engine remains authoritative for computed
rules. This bridge only sends guidelines explicitly marked ``ai`` or ``hybrid``
to the AI provider, converts its findings into backend ``FindingDraft`` objects,
and rejects any finding whose citation cannot be grounded in the loaded database
rows.

If the ``trueline`` package is not installed, the bridge reports ``unavailable``
and the backend continues to run deterministically.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .ai_labels import AILabel
from .models import ApprovedFact as FactRow
from .models import Guideline as GuidelineRow
from .rule_engine.models import CitationDraft, FindingDraft

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised through the available/unavailable paths
    from trueline.adapters.fastapi_adapter import convert_finding_to_response
    from trueline.config import settings as ai_settings
    from trueline.models import ApprovedFact as AIFact
    from trueline.models import Guideline as AIGuideline
    from trueline.providers.anthropic import AnthropicProvider
    from trueline.providers.base import AIProviderError

    AI_ENGINE_AVAILABLE = True
except Exception:  # pragma: no cover - depends on optional install
    convert_finding_to_response = None  # type: ignore[assignment]
    ai_settings = None  # type: ignore[assignment]
    AIFact = None  # type: ignore[assignment,misc]
    AIGuideline = None  # type: ignore[assignment,misc]
    AnthropicProvider = None  # type: ignore[assignment,misc]
    AIProviderError = Exception  # type: ignore[assignment,misc]
    AI_ENGINE_AVAILABLE = False


# Execution states are persisted on the review and surfaced by the API.
AI_STATUS_DISABLED = "disabled"
AI_STATUS_SKIPPED = "skipped"
AI_STATUS_NOT_CONFIGURED = "not_configured"
AI_STATUS_UNAVAILABLE = "unavailable"
AI_STATUS_TIMEOUT = "timeout"
AI_STATUS_DEGRADED = "degraded"
AI_STATUS_SUCCESS = "success"

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


@dataclass(frozen=True)
class AIReviewOutcome:
    """Result of one AI attempt, including truthful execution metadata."""

    findings: list[FindingDraft] = field(default_factory=list)
    status: str = AI_STATUS_SKIPPED
    error: str | None = None
    rejected_count: int = 0

    @property
    def needs_human_review(self) -> bool:
        """AI-required work that did not complete cleanly requires a human."""
        return self.status in {
            AI_STATUS_DISABLED,
            AI_STATUS_NOT_CONFIGURED,
            AI_STATUS_UNAVAILABLE,
            AI_STATUS_TIMEOUT,
            AI_STATUS_DEGRADED,
        }


def _config(row: GuidelineRow) -> dict[str, Any]:
    return row.config_json or {}


def guideline_check_method(row: GuidelineRow) -> str:
    value = str(_config(row).get("check_method", "computed")).strip().lower()
    return value if value in {"computed", "ai", "hybrid"} else "computed"


def has_ai_guidelines(guidelines: list[GuidelineRow]) -> bool:
    return any(guideline_check_method(row) in {"ai", "hybrid"} for row in guidelines)


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
        check_method=guideline_check_method(row),
        match_type=row.match_type,
        severity_default=row.severity,
        required_phrase=required_phrase,
        case_sensitive=bool(config.get("case_sensitive", False)),
    )


def _fact_status(row: FactRow, evaluation_date: date) -> str:
    """Evaluate a stored fact without treating historical rows as active."""
    if not row.is_active:
        return "inactive"
    if row.superseded_by:
        return "superseded"
    if row.valid_until is not None and evaluation_date > row.valid_until:
        return "expired"
    if row.valid_from is not None and evaluation_date < row.valid_from:
        return "not_yet_valid"
    return "active"


def _to_ai_fact(row: FactRow, evaluation_date: date) -> Any:
    return AIFact(
        id=row.id,
        claim=row.statement,
        evidence=row.source_label,
        source_version=row.source_version,
        category="fact",
        valid_from=row.valid_from.isoformat() if row.valid_from else None,
        expires_on=row.valid_until.isoformat() if row.valid_until else None,
        status_on_evaluation_date=_fact_status(row, evaluation_date),
        superseded_by=row.superseded_by,
    )


def build_ai_inputs(
    guidelines: list[GuidelineRow],
    facts: list[FactRow],
    evaluation_date: date | None = None,
) -> tuple[list[Any], list[Any]]:
    """Convert DB rows and keep only guidelines marked ai/hybrid.

    Facts are converted with their evaluated status and supersession metadata.
    The caller is responsible for sending only active facts to the provider.
    """
    if evaluation_date is None:
        evaluation_date = date.today()
    ai_guidelines = [
        _to_ai_guideline(row)
        for row in guidelines
        if guideline_check_method(row) in {"ai", "hybrid"}
    ]
    return ai_guidelines, [_to_ai_fact(row, evaluation_date) for row in facts]


def _safe_error(exc: BaseException) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return message[:500]


def _is_timeout(exc: BaseException) -> bool:
    original = getattr(exc, "original_error", None)
    if isinstance(exc, TimeoutError) or isinstance(original, TimeoutError):
        return True
    text = f"{exc} {original}".lower()
    return "timeout" in text or "timed out" in text


def _citation_is_grounded(
    row: GuidelineRow | FactRow,
    source_type: str,
    *,
    rule_id: str,
    source_version: str | None,
    quoted_text: str,
) -> bool:
    version = row.version if source_type == "guideline" else row.source_version
    content = row.content if source_type == "guideline" else row.statement
    expected_rule_id = row.rule_id if source_type == "guideline" else row.id
    if expected_rule_id != rule_id:
        return False
    return (
        (version or None) == (source_version or None)
        and bool(quoted_text)
        and quoted_text in content
    )


def _to_finding_draft(
    ai_findings: list[Any],
    draft_text: str,
    guideline_rows: list[GuidelineRow],
    fact_rows: list[FactRow],
    evaluation_date: date,
) -> tuple[list[FindingDraft], int]:
    """Convert AI findings into backend drafts and count ungrounded rejects."""
    guideline_by_id = {row.rule_id: row for row in guideline_rows}
    fact_by_id = {row.id: row for row in fact_rows}
    drafts: list[FindingDraft] = []
    rejected = 0

    for finding in ai_findings:
        citation = finding.citation
        if citation is None:
            rejected += 1
            logger.warning(
                "Rejecting AI finding %s: no citation to an approved source",
                finding.rule_id or finding.id,
            )
            continue

        if finding.start is None or finding.end is None:
            if finding.matched_text:
                rejected += 1
                logger.warning(
                    "Rejecting AI finding %s: missing text offsets",
                    finding.rule_id or finding.id,
                )
                continue
        elif (
            finding.start < 0
            or finding.end > len(draft_text)
            or finding.start > finding.end
            or draft_text[finding.start : finding.end] != finding.matched_text
        ):
            rejected += 1
            logger.warning(
                "Rejecting AI finding %s: offsets do not match the draft",
                finding.rule_id or finding.id,
            )
            continue

        cited_id = citation.rule_id
        guideline = guideline_by_id.get(cited_id)
        fact = fact_by_id.get(cited_id)
        if guideline is None and fact is None:
            rejected += 1
            logger.warning(
                "Rejecting AI finding %s: unknown citation source %s",
                finding.rule_id or finding.id,
                cited_id,
            )
            continue

        converted = convert_finding_to_response(
            finding,
            draft_text,
            guideline=_to_ai_guideline(guideline) if guideline is not None else None,
            approved_fact=(
                _to_ai_fact(fact, evaluation_date) if fact is not None else None
            ),
        )
        converted_citation = converted.citation
        if converted_citation is None:
            rejected += 1
            continue

        source_type = converted_citation.source_type.value
        source_id = (
            guideline.id
            if guideline is not None and source_type == "guideline"
            else converted_citation.source_id
        )
        source = (
            guideline
            if source_type == "guideline"
            else fact_by_id.get(source_id)
        )
        if source is None or not _citation_is_grounded(
            source,
            source_type,
            rule_id=converted.rule_id,
            source_version=converted_citation.source_version,
            quoted_text=converted_citation.quoted_text,
        ):
            rejected += 1
            logger.warning(
                "Rejecting AI finding %s: citation does not match stored source %s",
                converted.rule_id,
                source_id,
            )
            continue

        citation_draft = CitationDraft(
            source_type=source_type,
            source_id=source_id,
            source_version=converted_citation.source_version,
            source_label=converted_citation.source,
            quoted_text=converted_citation.quoted_text,
            valid_until=converted_citation.valid_until,
        )
        drafts.append(
            FindingDraft(
                rule_id=converted.rule_id,
                matched_text=converted.matched_text,
                start=converted.start,
                end=converted.end,
                category=converted.category.value,
                severity=converted.severity.value,
                explanation=converted.explanation,
                citation=citation_draft,
                suggested_fix=converted.suggested_fix,
                confidence=converted.confidence,
                requires_human_review=converted.requires_human_review,
                ai_label=AILabel(converted.ai_label) if converted.ai_label else None,
            )
        )

    return drafts, rejected


def run_ai_review(
    *,
    draft_text: str,
    brand_id: str,
    purpose: str,
    guidelines: list[GuidelineRow],
    facts: list[FactRow],
    evaluation_date: date,
    provider: Any | None = None,
    enabled: bool = True,
) -> AIReviewOutcome:
    """Run the optional AI review and return findings plus execution metadata.

    Only guidelines marked ``ai`` or ``hybrid`` and facts active on the
    evaluation date are sent to the model. Provider failures never raise; they
    return a degraded outcome so deterministic results remain available.
    """
    if not has_ai_guidelines(guidelines):
        return AIReviewOutcome(status=AI_STATUS_SKIPPED)

    if not AI_ENGINE_AVAILABLE:
        return AIReviewOutcome(
            status=AI_STATUS_UNAVAILABLE,
            error="AI review package is not installed.",
        )

    if not enabled:
        return AIReviewOutcome(
            status=AI_STATUS_DISABLED,
            error="AI review is disabled by configuration.",
        )

    if provider is None:
        if not ai_settings.ai_enabled:
            return AIReviewOutcome(
                status=AI_STATUS_NOT_CONFIGURED,
                error=(
                    "AI review requires TRUELINE_AI_ENABLED=true and "
                    "ANTHROPIC_API_KEY."
                ),
            )
        provider = AnthropicProvider()

    ai_guideline_rows = [
        row
        for row in guidelines
        if guideline_check_method(row) in {"ai", "hybrid"}
    ]
    active_fact_rows = [
        row for row in facts if _fact_status(row, evaluation_date) == "active"
    ]
    ai_guidelines, ai_facts = build_ai_inputs(
        ai_guideline_rows, active_fact_rows, evaluation_date
    )

    try:
        ai_findings = asyncio.run(
            provider.analyze(
                draft_text=draft_text,
                content_purpose=purpose,
                guidelines=ai_guidelines,
                approved_facts=ai_facts,
                evaluation_date=evaluation_date.isoformat(),
            )
        )
    except AIProviderError as exc:
        logger.error("AI provider failed: %s", exc)
        return AIReviewOutcome(
            status=AI_STATUS_TIMEOUT if _is_timeout(exc) else AI_STATUS_DEGRADED,
            error=_safe_error(exc),
        )
    except Exception as exc:
        logger.exception("Unexpected AI review failure")
        return AIReviewOutcome(
            status=AI_STATUS_TIMEOUT if _is_timeout(exc) else AI_STATUS_DEGRADED,
            error=_safe_error(exc),
        )

    drafts, rejected = _to_finding_draft(
        ai_findings, draft_text, ai_guideline_rows, active_fact_rows, evaluation_date
    )
    if rejected:
        return AIReviewOutcome(
            findings=drafts,
            status=AI_STATUS_DEGRADED,
            error=(
                f"{rejected} AI finding(s) rejected because their citations "
                "could not be validated against approved sources."
            ),
            rejected_count=rejected,
        )
    return AIReviewOutcome(findings=drafts, status=AI_STATUS_SUCCESS)
