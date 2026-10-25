"""Review orchestration: load approved sources, run rules, validate, persist."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .ai_labels import AILabel
from .citations import validate_finding_citations
from .config import Settings
from .errors import NotFoundError, PersistenceError
from .models import ApprovedFact, Guideline, Review, ReviewEvent, ReviewFinding
from .repositories import (
    fact_to_definition,
    get_brand,
    get_review,
    guideline_to_rule,
    list_active_facts,
    list_active_guidelines,
    list_brands,
    list_reviews,
)
from .rule_engine import ENGINE_VERSION, RuleEngine
from .schemas import ReviewRequest

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def submit(self, session: Session, payload: ReviewRequest) -> Review:
        try:
            return self._submit(session, payload)
        except SQLAlchemyError as exc:
            session.rollback()
            logger.exception("Database failure while creating review")
            raise PersistenceError("Could not persist the review") from exc

    def _submit(self, session: Session, payload: ReviewRequest) -> Review:
        brand = get_brand(session, payload.brand_id)
        if brand is None:
            raise NotFoundError(f"Unknown brand_id {payload.brand_id!r}")

        guidelines = list_active_guidelines(session, brand.id)
        facts = list_active_facts(session, brand.id)

        rules = [guideline_to_rule(row) for row in guidelines]
        fact_definitions = [fact_to_definition(row) for row in facts]

        evaluation_date = datetime.now(timezone.utc).date()
        purpose = payload.purpose or "general"

        engine = RuleEngine(rules, fact_definitions)
        finding_drafts = engine.review(
            payload.draft_text,
            purpose=purpose,
            evaluation_date=evaluation_date,
        )

        validate_finding_citations(
            finding_drafts,
            brand_id=brand.id,
            guidelines={row.id: row for row in guidelines},
            facts={row.id: row for row in facts},
        )

        status = _review_status(finding_drafts)
        review_id = _new_id("review")
        review = Review(
            id=review_id,
            brand_id=brand.id,
            draft_text=payload.draft_text,
            purpose=purpose[: self.settings.max_purpose_chars],
            status=status,
            ruleset_version=self.settings.ruleset_version,
            engine_version=ENGINE_VERSION,
            evaluation_date=evaluation_date,
        )

        for index, draft in enumerate(finding_drafts, start=1):
            finding_id = f"{review_id}-F-{index:04d}"
            citation = draft.citation
            review.findings.append(
                ReviewFinding(
                    id=finding_id,
                    rule_id=draft.rule_id,
                    matched_text=draft.matched_text,
                    start_offset=draft.start,
                    end_offset=draft.end,
                    category=draft.category,
                    severity=draft.severity,
                    explanation=draft.explanation,
                    ai_label=AILabel(draft.ai_label).value
                    if draft.ai_label is not None
                    else None,
                    citation_source_type=citation.source_type if citation else None,
                    citation_source_id=citation.source_id if citation else None,
                    citation_source_version=citation.source_version
                    if citation
                    else None,
                    citation_source_label=citation.source_label if citation else None,
                    citation_quoted_text=citation.quoted_text if citation else None,
                    citation_valid_until=citation.valid_until if citation else None,
                    suggested_fix=draft.suggested_fix,
                    confidence=draft.confidence,
                    requires_human_review=draft.requires_human_review,
                )
            )

        review.events.append(
            ReviewEvent(
                id=_new_id("event"),
                sequence=1,
                event_type="review_created",
                actor_type="system",
                actor="Trueline API",
                action="Review request accepted.",
                event_metadata={"brand_id": brand.id, "purpose": purpose},
            )
        )
        review.events.append(
            ReviewEvent(
                id=_new_id("event"),
                sequence=2,
                event_type="review_completed",
                actor_type="system",
                actor="Trueline deterministic rule engine",
                action=(
                    f"Completed deterministic review with {len(finding_drafts)} "
                    f"finding(s); status: {status}."
                ),
                event_metadata={
                    "engine_version": ENGINE_VERSION,
                    "ruleset_version": self.settings.ruleset_version,
                    "finding_count": len(finding_drafts),
                    "requires_human_review": status == "needs_human_review",
                },
            )
        )

        session.add(review)
        session.commit()
        return review

    def get_review(self, session: Session, review_id: str) -> Review:
        try:
            review = get_review(session, review_id)
        except SQLAlchemyError as exc:
            logger.exception("Database failure while reading review")
            raise PersistenceError("Could not read the review") from exc
        if review is None:
            raise NotFoundError(f"Unknown review_id {review_id!r}")
        return review

    def list_reviews(
        self,
        session: Session,
        *,
        brand_id: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Review], int]:
        try:
            if brand_id is not None and get_brand(session, brand_id) is None:
                raise NotFoundError(f"Unknown brand_id {brand_id!r}")
            return list_reviews(session, brand_id=brand_id, limit=limit, offset=offset)
        except NotFoundError:
            raise
        except SQLAlchemyError as exc:
            logger.exception("Database failure while listing reviews")
            raise PersistenceError("Could not list reviews") from exc

    def list_brands(self, session: Session) -> list:
        try:
            return list_brands(session)
        except SQLAlchemyError as exc:
            logger.exception("Database failure while listing brands")
            raise PersistenceError("Could not list brands") from exc

    def get_guidelines(
        self, session: Session, brand_id: str
    ) -> tuple[object, list[Guideline]]:
        try:
            brand = get_brand(session, brand_id)
            if brand is None:
                raise NotFoundError(f"Unknown brand_id {brand_id!r}")
            return brand, list_active_guidelines(session, brand_id)
        except NotFoundError:
            raise
        except SQLAlchemyError as exc:
            logger.exception("Database failure while reading guidelines")
            raise PersistenceError("Could not read guidelines") from exc

    def get_facts(
        self, session: Session, brand_id: str
    ) -> tuple[object, list[ApprovedFact]]:
        try:
            brand = get_brand(session, brand_id)
            if brand is None:
                raise NotFoundError(f"Unknown brand_id {brand_id!r}")
            return brand, list_active_facts(session, brand_id)
        except NotFoundError:
            raise
        except SQLAlchemyError as exc:
            logger.exception("Database failure while reading approved facts")
            raise PersistenceError("Could not read approved facts") from exc


def _review_status(findings) -> str:
    if any(finding.requires_human_review for finding in findings):
        return "needs_human_review"
    if findings:
        return "changes_requested"
    return "approved"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
