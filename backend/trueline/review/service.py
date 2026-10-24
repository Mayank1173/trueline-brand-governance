"""Review Engine service for the Trueline AI Review Engine.

This module provides the main ReviewEngine class that orchestrates
deterministic checks and AI-powered analysis.
"""

import logging
from datetime import date
from typing import Literal

from trueline.config import settings
from trueline.models import (
    ApprovedFact,
    Finding,
    FindingLabel,
    Guideline,
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
    Severity,
)
from trueline.providers.anthropic import AnthropicProvider
from trueline.providers.base import AIProvider, AIProviderError
from trueline.review.deterministic import evaluate_fact_status, run_deterministic_checks

logger = logging.getLogger(__name__)


CheckMethod = Literal["computed", "ai", "hybrid"]


def _filter_active_facts(facts: list[ApprovedFact], evaluation_date: date) -> list[ApprovedFact]:
    """Filter facts to only those active on the evaluation date."""
    return [f for f in facts if evaluate_fact_status(f, evaluation_date) == "active"]


def _parse_evaluation_date(eval_date: str | None) -> date:
    """Parse evaluation date string, defaulting to today."""
    if eval_date:
        try:
            return date.fromisoformat(eval_date)
        except ValueError:
            logger.warning(f"Invalid evaluation_date format: {eval_date}, using today")
    return date.today()


def _split_guidelines_by_method(
    guidelines: list[Guideline],
) -> tuple[list[Guideline], list[Guideline], bool]:
    """Split guidelines into computed (deterministic) and AI/hybrid.

    Returns: (computed_guidelines, ai_hybrid_guidelines, has_explicit_method)
    has_explicit_method is True if any guideline has check_method set.
    """
    computed = []
    ai_hybrid = []
    has_explicit = False
    for g in guidelines:
        if g.check_method:
            has_explicit = True
            method = g.check_method
            if method == "computed":
                computed.append(g)
            else:
                ai_hybrid.append(g)
        else:
            # Legacy: no check_method specified, add to both for backward compat
            computed.append(g)
            ai_hybrid.append(g)
    return computed, ai_hybrid, has_explicit


class ReviewEngine:
    """
    Main review engine that combines deterministic and AI-powered analysis.

    Usage:
        engine = ReviewEngine()
        request = ReviewRequest(...)
        response = await engine.review(request)
    """

    def __init__(self, ai_provider: AIProvider | None = None):
        """
        Initialize the review engine.

        Args:
            ai_provider: Optional AI provider instance. If not provided and
                        AI is enabled in settings, an AnthropicProvider is created.
        """
        self._ai_provider = ai_provider
        self._degraded_mode = settings.review_degraded_mode

    @property
    def ai_provider(self) -> AIProvider | None:
        """Get or create the AI provider."""
        if self._ai_provider is None and settings.ai_enabled:
            self._ai_provider = AnthropicProvider()
        return self._ai_provider

    def _determine_status(
        self, findings: list[Finding], provider_error: str | None
    ) -> ReviewStatus:
        """Determine overall review status from findings."""
        if provider_error and self._degraded_mode:
            return ReviewStatus.NEEDS_HUMAN_REVIEW

        if not findings:
            return ReviewStatus.APPROVED

        # Check for findings that need human judgement (label-based)
        if any(f.label == FindingLabel.NEEDS_HUMAN_JUDGEMENT for f in findings):
            return ReviewStatus.NEEDS_HUMAN_REVIEW

        # Check if any finding requires human review (legacy field)
        if any(f.requires_human_review for f in findings):
            return ReviewStatus.NEEDS_HUMAN_REVIEW

        # Check for high severity findings that are not just violations
        # (contradicted, unsupported, outdated with high severity -> needs human review)
        needs_review_labels = (
            FindingLabel.UNSUPPORTED,
            FindingLabel.CONTRADICTED,
            FindingLabel.OUTDATED,
        )
        high_severity_needs_review = any(
            f.severity == Severity.HIGH and f.label in needs_review_labels
            for f in findings
        )
        if high_severity_needs_review:
            return ReviewStatus.NEEDS_HUMAN_REVIEW

        # Check for high severity violations -> changes requested
        if any(f.severity == Severity.HIGH for f in findings):
            return ReviewStatus.CHANGES_REQUESTED

        return ReviewStatus.CHANGES_REQUESTED

    def _deduplicate_findings(self, findings: list[Finding]) -> list[Finding]:
        """Remove duplicate findings based on matched_text and offsets."""
        seen = set()
        unique = []
        for f in findings:
            key = (f.matched_text, f.start, f.end, f.category)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _validate_citations(
        self,
        findings: list[Finding],
        guidelines: list[Guideline],
        approved_facts: list[ApprovedFact] | None = None,
    ) -> list[Finding]:
        """Validate that all citations reference supplied guidelines or facts."""
        valid_ids = {g.id for g in guidelines}
        valid_ids.update(f.id for f in approved_facts or [])
        validated = []

        for f in findings:
            if f.citation and f.citation.rule_id not in valid_ids:
                logger.warning(
                    f"Finding {f.id} cites unknown source {f.citation.rule_id}; "
                    f"removing citation"
                )
                # Create new finding with citation removed
                f = Finding(
                    **f.model_dump(exclude={"citation"}),
                    citation=None,
                )
            validated.append(f)

        return validated

    def _verify_offsets(
        self, findings: list[Finding], draft_text: str
    ) -> list[Finding]:
        """Verify that all finding offsets match the draft text exactly."""
        verified = []

        for f in findings:
            if f.start < 0 or f.end > len(draft_text) or f.start > f.end:
                logger.warning(
                    f"Finding {f.id} has invalid offsets start={f.start}, end={f.end}; skipping"
                )
                continue

            actual = draft_text[f.start:f.end]
            if actual != f.matched_text:
                logger.warning(
                    f"Finding {f.id} offset mismatch: "
                    f"draft[{f.start}:{f.end}]='{actual}' "
                    f"!= matched_text='{f.matched_text}'; skipping"
                )
                continue

            verified.append(f)

        return verified

    async def review(self, request: ReviewRequest) -> ReviewResponse:
        """
        Review draft content against brand guidelines.

        Args:
            request: ReviewRequest containing draft text, brand info, and guidelines

        Returns:
            ReviewResponse with findings and overall status
        """
        logger.info(f"Starting review for brand {request.brand_id}")

        # Parse evaluation date
        eval_date = _parse_evaluation_date(request.evaluation_date)

        # Filter approved facts to only active ones on evaluation date
        active_facts = _filter_active_facts(request.approved_facts, eval_date)
        if len(active_facts) != len(request.approved_facts):
            logger.info(
                f"Filtered {len(request.approved_facts) - len(active_facts)} "
                f"inactive/expired/superseded facts for evaluation date {eval_date}"
            )

        # Split guidelines by check method
        computed_guidelines, ai_hybrid_guidelines, has_explicit_method = (
            _split_guidelines_by_method(request.guidelines)
        )

        all_findings: list[Finding] = []
        provider_error: str | None = None
        degraded = False

        # Step 1: Run deterministic checks for computed guidelines.
        # Pass every fact, not just active ones: expired/superseded facts must be
        # visible to the checker so outdated references can be reported.
        if computed_guidelines or request.approved_facts:
            try:
                det_findings = run_deterministic_checks(
                    request.draft_text,
                    computed_guidelines,
                    approved_facts=request.approved_facts,
                    evaluation_date=eval_date,
                )
                all_findings.extend(det_findings)
                logger.info(f"Deterministic checks: {len(det_findings)} findings")
            except Exception as e:
                logger.error(f"Deterministic checks failed: {e}")
                # Don't fail the whole review for deterministic errors

        # Step 2: Run AI analysis for ai/hybrid guidelines (if available)
        ai_findings: list[Finding] = []
        # Call AI if: (1) we have AI/hybrid guidelines, OR
        # (2) legacy mode (no explicit check_method) with AI provider
        should_call_ai = bool(ai_hybrid_guidelines) or (
            not has_explicit_method and self.ai_provider
        )

        if self.ai_provider and should_call_ai:
            try:
                # For legacy mode, pass all guidelines to AI
                ai_guidelines = ai_hybrid_guidelines if has_explicit_method else request.guidelines
                ai_findings = await self.ai_provider.analyze(
                    draft_text=request.draft_text,
                    content_purpose=request.content_purpose,
                    guidelines=ai_guidelines,
                    approved_facts=active_facts,
                    evaluation_date=request.evaluation_date,
                )
                all_findings.extend(ai_findings)
                logger.info(f"AI analysis: {len(ai_findings)} findings")
            except AIProviderError as e:
                provider_error = str(e)
                degraded = True
                logger.error(f"AI provider failed: {e}")
                if not self._degraded_mode:
                    raise
            except Exception as e:
                provider_error = f"Unexpected AI error: {e}"
                degraded = True
                logger.error(f"Unexpected AI error: {e}")
                if not self._degraded_mode:
                    raise
        elif should_call_ai:
            # Only set degraded if there were explicitly AI/hybrid guidelines or legacy mode
            logger.info("AI provider not configured; skipping AI analysis")
            degraded = not settings.ai_enabled
        else:
            logger.info("No AI/hybrid guidelines to process")

        # Step 3: Validate and deduplicate findings
        all_findings = self._verify_offsets(all_findings, request.draft_text)
        all_findings = self._validate_citations(
            all_findings, request.guidelines, request.approved_facts
        )
        all_findings = self._deduplicate_findings(all_findings)

        # Step 4: Determine overall status
        status = self._determine_status(all_findings, provider_error)

        logger.info(f"Review complete: {len(all_findings)} total findings, status={status}")

        return ReviewResponse(
            status=status,
            findings=all_findings,
            degraded_mode=degraded,
            provider_error=provider_error,
        )


def create_review_engine(ai_provider: AIProvider | None = None) -> ReviewEngine:
    """Factory function to create a ReviewEngine instance."""
    return ReviewEngine(ai_provider=ai_provider)
