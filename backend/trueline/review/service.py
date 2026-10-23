"""Review Engine service for the Trueline AI Review Engine.

This module provides the main ReviewEngine class that orchestrates
deterministic checks and AI-powered analysis.
"""

import logging

from trueline.config import settings
from trueline.models import (
    Finding,
    Guideline,
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
)
from trueline.providers.anthropic import AnthropicProvider
from trueline.providers.base import AIProvider, AIProviderError
from trueline.review.deterministic import run_deterministic_checks

logger = logging.getLogger(__name__)


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

        # Check if any finding requires human review
        if any(f.requires_human_review for f in findings):
            return ReviewStatus.NEEDS_HUMAN_REVIEW

        # Check for high severity findings
        if any(f.severity == "high" for f in findings):
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
        self, findings: list[Finding], guidelines: list[Guideline]
    ) -> list[Finding]:
        """Validate that all citations reference supplied guidelines."""
        guideline_ids = {g.id for g in guidelines}
        validated = []

        for f in findings:
            if f.citation and f.citation.rule_id not in guideline_ids:
                logger.warning(
                    f"Finding {f.id} cites unknown guideline {f.citation.rule_id}; "
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

        all_findings: list[Finding] = []
        provider_error: str | None = None
        degraded = False

        # Step 1: Run deterministic checks (always runs)
        try:
            det_findings = run_deterministic_checks(request.draft_text, request.guidelines)
            all_findings.extend(det_findings)
            logger.info(f"Deterministic checks: {len(det_findings)} findings")
        except Exception as e:
            logger.error(f"Deterministic checks failed: {e}")
            # Don't fail the whole review for deterministic errors

        # Step 2: Run AI analysis (if available)
        ai_findings: list[Finding] = []
        if self.ai_provider:
            try:
                ai_findings = await self.ai_provider.analyze(
                    draft_text=request.draft_text,
                    content_purpose=request.content_purpose,
                    guidelines=request.guidelines,
                    approved_facts=request.approved_facts,
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
        else:
            logger.info("AI provider not configured; running in deterministic-only mode")
            degraded = not settings.ai_enabled

        # Step 3: Validate and deduplicate findings
        all_findings = self._verify_offsets(all_findings, request.draft_text)
        all_findings = self._validate_citations(all_findings, request.guidelines)
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
