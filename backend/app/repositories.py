"""Database queries and model-to-engine adapters."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .models import ApprovedFact, Brand, Guideline, Review
from .rule_engine import FactDefinition, RuleDefinition


def get_brand(session: Session, brand_id: str) -> Brand | None:
    return session.get(Brand, brand_id)


def list_brands(session: Session) -> list[Brand]:
    return list(session.scalars(select(Brand).order_by(Brand.name, Brand.id)))


def list_active_guidelines(session: Session, brand_id: str) -> list[Guideline]:
    statement = (
        select(Guideline)
        .where(Guideline.brand_id == brand_id, Guideline.is_active.is_(True))
        .order_by(Guideline.rule_id, Guideline.id)
    )
    return list(session.scalars(statement))


def list_active_facts(session: Session, brand_id: str) -> list[ApprovedFact]:
    statement = (
        select(ApprovedFact)
        .where(ApprovedFact.brand_id == brand_id, ApprovedFact.is_active.is_(True))
        .order_by(ApprovedFact.id)
    )
    return list(session.scalars(statement))


def list_all_facts(session: Session, brand_id: str) -> list[ApprovedFact]:
    """Return every fact, including inactive/historical rows.

    The AI review layer needs historical facts to detect outdated references;
    the deterministic rule engine continues to use active facts only.
    """
    statement = (
        select(ApprovedFact)
        .where(ApprovedFact.brand_id == brand_id)
        .order_by(ApprovedFact.id)
    )
    return list(session.scalars(statement))


def guideline_to_rule(guideline: Guideline) -> RuleDefinition:
    config: dict[str, Any] = guideline.config_json or {}
    patterns = _as_string_tuple(config.get("patterns"))
    purposes = _as_string_tuple(config.get("applies_to_purposes"))
    max_chars = _as_positive_int(config.get("max_chars"))

    return RuleDefinition(
        rule_id=guideline.rule_id,
        source_id=guideline.id,
        source_version=guideline.version,
        source_label=_source_label(guideline),
        quoted_text=guideline.content,
        category=guideline.category,
        severity=guideline.severity,
        match_type=guideline.match_type,
        explanation=guideline.explanation,
        patterns=patterns,
        suggested_fix=guideline.suggested_fix,
        confidence=guideline.confidence,
        requires_human_review=guideline.requires_human_review,
        case_sensitive=bool(config.get("case_sensitive", False)),
        word_boundary=bool(config.get("word_boundary", True)),
        max_chars=max_chars,
        applies_to_purposes=purposes,
    )


def fact_to_definition(fact: ApprovedFact) -> FactDefinition:
    return FactDefinition(
        id=fact.id,
        statement=fact.statement,
        source_label=fact.source_label,
        source_version=fact.source_version,
        valid_from=fact.valid_from,
        valid_until=fact.valid_until,
        is_active=fact.is_active,
    )


def get_review(session: Session, review_id: str) -> Review | None:
    statement = (
        select(Review)
        .where(Review.id == review_id)
        .options(selectinload(Review.findings), selectinload(Review.events))
    )
    return session.scalars(statement).one_or_none()


def list_reviews(
    session: Session,
    *,
    brand_id: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Review], int]:
    filters = []
    if brand_id is not None:
        filters.append(Review.brand_id == brand_id)

    count_statement = select(func.count()).select_from(Review)
    list_statement = (
        select(Review)
        .options(selectinload(Review.findings))
        .order_by(Review.created_at.desc(), Review.id.desc())
        .limit(limit)
        .offset(offset)
    )
    if filters:
        count_statement = count_statement.where(*filters)
        list_statement = list_statement.where(*filters)

    total = int(session.scalar(count_statement) or 0)
    return list(session.scalars(list_statement)), total


def fact_is_current(fact: ApprovedFact, today: date | None = None) -> bool:
    current = today or datetime.now(timezone.utc).date()
    return not (
        (fact.valid_from and current < fact.valid_from)
        or (fact.valid_until and current > fact.valid_until)
    )


def _source_label(guideline: Guideline) -> str:
    if guideline.section:
        return f"{guideline.title} §{guideline.section}"
    return guideline.title


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(item for item in value if isinstance(item, str))
    return ()


def _as_positive_int(value: object) -> int | None:
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None
