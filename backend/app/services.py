"""Review orchestration: load approved sources, run rules, validate, persist."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .ai_labels import AILabel
from .ai_review import (
    AI_STATUS_SUCCESS,
    AIReviewOutcome,
    guideline_check_method,
    run_ai_review,
)
from .citations import validate_finding_citations
from .config import Settings
from .errors import ConflictError, NotFoundError, PersistenceError
from .models import ApprovedFact, Guideline, Review, ReviewEvent, ReviewFinding
from .repositories import (
    fact_to_definition,
    get_brand,
    get_review,
    guideline_to_rule,
    list_active_facts,
    list_active_guidelines,
    list_all_facts,
    list_brands,
    list_reviews,
)
from .rule_engine import ENGINE_VERSION, RuleEngine
from .rule_engine.models import FindingDraft
from .schemas import ReviewDecisionRequest, ReviewRequest

_AI_NEEDS_HUMAN_REVIEW = {
    "disabled",
    "not_configured",
    "unavailable",
    "timeout",
    "degraded",
}

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self, settings: Settings, ai_provider: object | None = None) -> None:
        self.settings = settings
        self.ai_provider = ai_provider

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
        all_facts = list_all_facts(session, brand.id)

        # AI-only rules must not be run by the deterministic engine. Hybrid
        # rules run deterministically and are also sent to the AI provider.
        rules = [
            guideline_to_rule(row)
            for row in guidelines
            if guideline_check_method(row) in {"computed", "hybrid"}
        ]
        fact_definitions = [fact_to_definition(row) for row in facts]

        evaluation_date = datetime.now(timezone.utc).date()
        purpose = payload.purpose or "general"

        engine = RuleEngine(rules, fact_definitions)
        deterministic_findings = engine.review(
            payload.draft_text,
            purpose=purpose,
            evaluation_date=evaluation_date,
        )

        try:
            ai_outcome = run_ai_review(
                draft_text=payload.draft_text,
                brand_id=brand.id,
                purpose=purpose,
                guidelines=guidelines,
                facts=all_facts,
                evaluation_date=evaluation_date,
                provider=self.ai_provider,
                enabled=self.settings.ai_enabled,
            )
        except Exception as exc:
            logger.exception("AI review failed safely")
            ai_outcome = AIReviewOutcome(
                status="degraded",
                error=f"AI review failed safely: {exc.__class__.__name__}",
            )

        finding_drafts = _merge_findings(
            deterministic_findings, ai_outcome.findings
        )

        validate_finding_citations(
            finding_drafts,
            brand_id=brand.id,
            guidelines={row.id: row for row in guidelines},
            facts={row.id: row for row in all_facts},
        )

        status = _review_status(finding_drafts, ai_outcome.status)
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
            ai_status=ai_outcome.status,
            ai_error=ai_outcome.error,
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
        if ai_outcome.status == AI_STATUS_SUCCESS:
            actor = "Trueline deterministic + AI review pipeline"
        elif ai_outcome.status == "skipped":
            actor = "Trueline deterministic rule engine"
        else:
            actor = "Trueline deterministic rule engine (AI not completed)"

        review.events.append(
            ReviewEvent(
                id=_new_id("event"),
                sequence=2,
                event_type="review_completed",
                actor_type="system",
                actor=actor,
                action=(
                    f"Completed review with {len(finding_drafts)} finding(s); "
                    f"status: {status}; AI status: {ai_outcome.status}."
                ),
                event_metadata={
                    "engine_version": ENGINE_VERSION,
                    "ruleset_version": self.settings.ruleset_version,
                    "finding_count": len(finding_drafts),
                    "deterministic_finding_count": len(deterministic_findings),
                    "ai_finding_count": len(ai_outcome.findings),
                    "ai_status": ai_outcome.status,
                    "ai_error": ai_outcome.error,
                    "ai_rejected_finding_count": ai_outcome.rejected_count,
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

    def decide(
        self, session: Session, review_id: str, payload: ReviewDecisionRequest
    ) -> tuple[Review, ReviewEvent]:
        """Persist one explicit human decision and its audit event atomically."""
        try:
            review = get_review(session, review_id)
            if review is None:
                raise NotFoundError(f"Unknown review_id {review_id!r}")

            eligible_statuses = {
                "pending_approval",
                "needs_human_review",
                "changes_requested",
            }
            if review.status not in eligible_statuses:
                raise ConflictError(
                    f"Review {review_id!r} is {review.status!r}; "
                    "only a review awaiting human action can be decided."
                )

            previous_status = review.status
            new_status = payload.decision.value
            reviewer = payload.reviewer or "Unknown reviewer"
            event = ReviewEvent(
                id=_new_id("event"),
                sequence=max((item.sequence for item in review.events), default=0) + 1,
                event_type=(
                    "human_approval"
                    if payload.decision.value == "approved"
                    else "human_rejection"
                ),
                actor_type="human",
                actor=reviewer,
                action=(
                    f"Reviewer recorded {payload.decision.value} decision; "
                    f"status changed from {previous_status} to {new_status}."
                ),
                comment=payload.comment,
                event_metadata={
                    "decision": payload.decision.value,
                    "previous_status": previous_status,
                    "new_status": new_status,
                    "reviewer_provided": payload.reviewer is not None,
                },
            )
            review.status = new_status
            review.events.append(event)
            session.commit()
            return review, event
        except (NotFoundError, ConflictError):
            session.rollback()
            raise
        except SQLAlchemyError as exc:
            session.rollback()
            logger.exception("Database failure while recording review decision")
            raise PersistenceError("Could not persist the review decision") from exc

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


def _review_status(findings: list[FindingDraft], ai_status: str) -> str:
    # AI-required work that did not run cleanly must never masquerade as a
    # complete approval, even when the deterministic checks found nothing.
    if ai_status in _AI_NEEDS_HUMAN_REVIEW:
        return "needs_human_review"
    if any(finding.requires_human_review for finding in findings):
        return "needs_human_review"
    if findings:
        return "changes_requested"
    return "pending_approval"


def _same_issue(left: FindingDraft, right: FindingDraft) -> bool:
    if left.rule_id != right.rule_id:
        return False
    if left.start is None or right.start is None:
        return left.start is None and right.start is None and (
            left.matched_text.casefold() == right.matched_text.casefold()
        )
    left_end = left.end if left.end is not None else left.start
    right_end = right.end if right.end is not None else right.start
    return left.start < right_end and right.start < left_end


def _merge_findings(
    deterministic: list[FindingDraft], ai_findings: list[FindingDraft]
) -> list[FindingDraft]:
    """Keep deterministic results first and drop AI duplicates of the same issue."""
    merged = list(deterministic)
    for finding in ai_findings:
        if any(_same_issue(finding, existing) for existing in merged):
            continue
        merged.append(finding)
    merged.sort(
        key=lambda item: (
            item.start is None,
            item.start if item.start is not None else 0,
            item.end if item.end is not None else 0,
            item.rule_id,
            item.category,
        )
    )
    return merged


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
