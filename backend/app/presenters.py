"""Convert ORM rows into public API schemas."""

from __future__ import annotations

from datetime import date, datetime, timezone

from .models import ApprovedFact, Brand, Guideline, Review, ReviewEvent, ReviewFinding
from .repositories import fact_is_current
from .schemas import (
    ApprovedFactResponse,
    BrandResponse,
    CitationOut,
    FindingResponse,
    GuidelineResponse,
    ReviewDetail,
    ReviewEventResponse,
    ReviewSummary,
    Severity,
    SourceType,
)


def brand_response(brand: Brand) -> BrandResponse:
    return BrandResponse(id=brand.id, name=brand.name, description=brand.description)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def citation_response(finding: ReviewFinding) -> CitationOut | None:
    if not finding.citation_source_id:
        return None
    quoted_text = finding.citation_quoted_text or ""
    return CitationOut(
        rule_id=finding.rule_id,
        source=finding.citation_source_label or finding.citation_source_id,
        excerpt=quoted_text,
        source_type=SourceType(finding.citation_source_type or "guideline"),
        source_id=finding.citation_source_id,
        source_version=finding.citation_source_version,
        quoted_text=quoted_text,
        valid_until=finding.citation_valid_until,
    )


def finding_response(finding: ReviewFinding) -> FindingResponse:
    return FindingResponse(
        id=finding.id,
        finding_id=finding.id,
        rule_id=finding.rule_id,
        matched_text=finding.matched_text,
        start=finding.start_offset,
        end=finding.end_offset,
        category=finding.category,
        severity=Severity(finding.severity),
        explanation=finding.explanation,
        citation=citation_response(finding),
        suggested_fix=finding.suggested_fix,
        confidence=finding.confidence,
        requires_human_review=finding.requires_human_review,
        ai_label=finding.ai_label,
    )


def review_summary(review: Review) -> ReviewSummary:
    return ReviewSummary(
        review_id=review.id,
        brand_id=review.brand_id,
        purpose=review.purpose,
        status=review.status,
        finding_count=len(review.findings),
        requires_human_review_count=sum(
            1 for finding in review.findings if finding.requires_human_review
        ),
        created_at=_as_utc(review.created_at),
        updated_at=_as_utc(review.updated_at),
        ai_status=review.ai_status,
        ai_error=review.ai_error,
    )


def review_detail(review: Review) -> ReviewDetail:
    summary = review_summary(review)
    return ReviewDetail(
        **summary.model_dump(),
        draft_text=review.draft_text,
        ruleset_version=review.ruleset_version,
        engine_version=review.engine_version,
        evaluation_date=review.evaluation_date,
        findings=[finding_response(finding) for finding in review.findings],
    )


def review_event_response(event: ReviewEvent) -> ReviewEventResponse:
    return ReviewEventResponse(
        id=event.id,
        event_type=event.event_type,
        actor_type=event.actor_type,
        actor=event.actor,
        action=event.action,
        comment=event.comment,
        at=_as_utc(event.created_at),
    )


def guideline_response(guideline: Guideline) -> GuidelineResponse:
    return GuidelineResponse(
        source_id=guideline.id,
        rule_id=guideline.rule_id,
        title=guideline.title,
        section=guideline.section,
        version=guideline.version,
        content=guideline.content,
        category=guideline.category,
        severity=Severity(guideline.severity),
        match_type=guideline.match_type,
        explanation=guideline.explanation,
        suggested_fix=guideline.suggested_fix,
        confidence=guideline.confidence,
        requires_human_review=guideline.requires_human_review,
    )


def fact_response(
    fact: ApprovedFact, today: date | None = None
) -> ApprovedFactResponse:
    current = fact_is_current(fact, today or datetime.now(timezone.utc).date())
    return ApprovedFactResponse(
        source_id=fact.id,
        statement=fact.statement,
        source=fact.source_label,
        source_version=fact.source_version,
        valid_from=fact.valid_from,
        valid_until=fact.valid_until,
        is_current=current,
        superseded_by=fact.superseded_by,
    )
