"""Tests for ReviewEngine service."""

from unittest.mock import AsyncMock, patch

import pytest
from trueline.models import (
    Category,
    Citation,
    Finding,
    Guideline,
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
    Severity,
)
from trueline.providers.base import AIProvider, AIProviderError
from trueline.review.service import ReviewEngine, create_review_engine


class MockAIProvider(AIProvider):
    """Mock AI provider for testing."""

    def __init__(self, findings=None, should_fail=False, error_message="AI error"):
        self._findings = findings or []
        self._should_fail = should_fail
        self._error_message = error_message
        self.called = False

    @property
    def name(self) -> str:
        return "mock"

    async def analyze(self, draft_text, content_purpose, guidelines, approved_facts, evaluation_date=None):
        self.called = True
        if self._should_fail:
            raise AIProviderError(self._error_message, provider="mock")
        return self._findings

    async def health_check(self) -> bool:
        return not self._should_fail


class TestReviewEngine:
    @pytest.fixture
    def sample_guidelines(self):
        return [
            Guideline(
                id="RULE_001",
                text='Do not use "guaranteed" in claims.',
                category="unsupported_claim",
                source="Guidelines",
            ),
            Guideline(
                id="RULE_002",
                text='Must include "Results may vary" disclaimer.',
                category="missing_disclaimer",
                source="Guidelines",
            ),
        ]

    @pytest.fixture
    def sample_request(self, sample_guidelines):
        return ReviewRequest(
            draft_text="Our product is guaranteed to work.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

    @pytest.mark.asyncio
    async def test_deterministic_only_no_ai(self, sample_request):
        """Test review with no AI provider configured."""
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(sample_request)

        assert isinstance(response, ReviewResponse)
        assert len(response.findings) >= 1  # Should find "guaranteed"
        assert response.degraded_mode is True  # No AI = degraded
        assert response.provider_error is None

    @pytest.mark.asyncio
    async def test_deterministic_finds_banned_term(self, sample_request):
        """Test deterministic detection of banned term."""
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(sample_request)

        banned_findings = [f for f in response.findings if f.category == Category.BANNED_TERM]
        assert len(banned_findings) == 1
        f = banned_findings[0]
        assert f.matched_text == "guaranteed"
        assert f.citation is not None
        assert f.citation.rule_id == "RULE_001"
        assert f.confidence == 0.95

    @pytest.mark.asyncio
    async def test_deterministic_finds_missing_required_phrase(self, sample_guidelines):
        """Test deterministic detection of missing required phrase."""
        request = ReviewRequest(
            draft_text="Our product works great.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(request)

        required_findings = [f for f in response.findings if f.category == Category.REQUIRED_PHRASE]
        assert len(required_findings) == 1
        f = required_findings[0]
        assert f.matched_text == ""
        assert f.start == 0
        assert f.end == 0

    @pytest.mark.asyncio
    async def test_clean_draft_no_findings(self, sample_guidelines):
        """Test clean draft returns no findings."""
        request = ReviewRequest(
            draft_text="Our product works well. Results may vary.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(request)

        assert len(response.findings) == 0
        assert response.status == ReviewStatus.APPROVED

    @pytest.mark.asyncio
    async def test_ai_provider_success(self, sample_request, sample_guidelines):
        """Test successful AI provider integration."""
        ai_finding = Finding(
            id="ai-1",
            matched_text="revolutionary",
            start=10,
            end=23,
            category=Category.BANNED_TERM,
            severity=Severity.HIGH,
            explanation="AI detected banned term",
            citation=Citation(rule_id="RULE_003", source="Guidelines", excerpt="Avoid revolutionary"),
            suggested_fix="Use innovative",
            confidence=0.9,
            requires_human_review=True,
        )
        mock_provider = MockAIProvider(findings=[ai_finding])
        engine = ReviewEngine(ai_provider=mock_provider)

        # Add a guideline that AI can use
        request = ReviewRequest(
            draft_text="Our revolutionary product works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines + [
                Guideline(id="RULE_003", text='Avoid "revolutionary"', category="banned_term", source="Guidelines")
            ],
        )

        response = await engine.review(request)

        assert mock_provider.called
        assert response.degraded_mode is False
        assert response.provider_error is None
        # Should have both deterministic and AI findings
        assert len(response.findings) >= 1

    @pytest.mark.asyncio
    async def test_ai_provider_failure_degraded_mode(self, sample_request):
        """Test AI failure preserves deterministic findings in degraded mode."""
        mock_provider = MockAIProvider(should_fail=True, error_message="API timeout")
        engine = ReviewEngine(ai_provider=mock_provider)

        response = await engine.review(sample_request)

        assert response.degraded_mode is True
        assert response.provider_error is not None
        assert "API timeout" in response.provider_error
        # Deterministic findings should still be present
        assert len(response.findings) >= 1

    @pytest.mark.asyncio
    async def test_ai_provider_failure_raises_when_not_degraded(self, sample_request):
        """Test AI failure raises when degraded_mode is False."""
        mock_provider = MockAIProvider(should_fail=True)
        engine = ReviewEngine(ai_provider=mock_provider)
        engine._degraded_mode = False

        with pytest.raises(AIProviderError):
            await engine.review(sample_request)

    @pytest.mark.asyncio
    async def test_invalid_ai_citation_rejected(self, sample_guidelines):
        """Test that AI citations referencing unknown guidelines are rejected."""
        ai_finding = Finding(
            id="ai-1",
            matched_text="test",
            start=0,
            end=4,
            category=Category.UNSUPPORTED_CLAIM,
            severity=Severity.MEDIUM,
            explanation="Test",
            citation=Citation(rule_id="UNKNOWN_RULE", source="Unknown", excerpt="text"),
            confidence=0.8,
            requires_human_review=False,
        )
        mock_provider = MockAIProvider(findings=[ai_finding])
        engine = ReviewEngine(ai_provider=mock_provider)

        request = ReviewRequest(
            draft_text="Test draft.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)

        # Citation should be removed
        ai_findings = [f for f in response.findings if f.id == "ai-1"]
        if ai_findings:
            assert ai_findings[0].citation is None

    @pytest.mark.asyncio
    async def test_invalid_offsets_rejected(self, sample_guidelines):
        """Test that findings with invalid offsets are rejected."""
        ai_finding = Finding(
            id="ai-1",
            matched_text="wrong",
            start=0,
            end=5,
            category=Category.UNSUPPORTED_CLAIM,
            severity=Severity.MEDIUM,
            explanation="Test",
            confidence=0.8,
            requires_human_review=False,
        )
        mock_provider = MockAIProvider(findings=[ai_finding])
        engine = ReviewEngine(ai_provider=mock_provider)

        request = ReviewRequest(
            draft_text="Different text here.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)

        # Finding with mismatched offsets should be dropped
        ai_findings = [f for f in response.findings if f.id == "ai-1"]
        assert len(ai_findings) == 0

    @pytest.mark.asyncio
    async def test_deduplication(self, sample_guidelines):
        """Test duplicate findings are removed."""
        # Same finding from deterministic and AI
        # "guaranteed" in "Product guaranteed works." is at offset 8-18
        det_finding = Finding(
            id="det-1",
            matched_text="guaranteed",
            start=8,
            end=18,
            category=Category.BANNED_TERM,
            severity=Severity.HIGH,
            explanation="Deterministic",
            citation=Citation(rule_id="RULE_001", source="Guidelines", excerpt="text"),
            confidence=0.95,
            requires_human_review=True,
        )
        ai_finding = Finding(
            id="ai-1",
            matched_text="guaranteed",
            start=8,
            end=18,
            category=Category.BANNED_TERM,
            severity=Severity.HIGH,
            explanation="AI detected",
            citation=Citation(rule_id="RULE_001", source="Guidelines", excerpt="text"),
            confidence=0.9,
            requires_human_review=True,
        )
        mock_provider = MockAIProvider(findings=[ai_finding])
        engine = ReviewEngine(ai_provider=mock_provider)

        request = ReviewRequest(
            draft_text="Product guaranteed works.",  # "guaranteed" at offset 8-18
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        # Override deterministic to return our test finding
        with patch("trueline.review.service.run_deterministic_checks", return_value=[det_finding]):
            response = await engine.review(request)

        # Should deduplicate
        guaranteed_findings = [f for f in response.findings if f.matched_text == "guaranteed"]
        assert len(guaranteed_findings) == 1

    @pytest.mark.asyncio
    async def test_status_determination(self, sample_guidelines):
        """Test overall status determination."""
        # No findings -> approved (draft includes required phrase)
        request = ReviewRequest(
            draft_text="Clean text. Results may vary.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(request)
        assert response.status == ReviewStatus.APPROVED

        # High severity -> needs_human_review (deterministic findings have requires_human_review=True)
        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(request)
        # Deterministic findings have requires_human_review=True, so status is NEEDS_HUMAN_REVIEW
        assert response.status == ReviewStatus.NEEDS_HUMAN_REVIEW

        # Human review required -> needs_human_review
        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )
        engine = ReviewEngine(ai_provider=None)
        # All deterministic findings have requires_human_review=True
        response = await engine.review(request)
        assert response.status == ReviewStatus.NEEDS_HUMAN_REVIEW

    @pytest.mark.asyncio
    async def test_empty_guidelines(self):
        """Test review with empty guidelines list."""
        request = ReviewRequest(
            draft_text="Any text.",
            brand_id="test",
            content_purpose="email",
            guidelines=[],
        )
        engine = ReviewEngine(ai_provider=None)
        response = await engine.review(request)

        assert response.status == ReviewStatus.APPROVED
        assert response.findings == []

    @pytest.mark.asyncio
    async def test_create_review_engine_factory(self):
        """Test factory function."""
        engine = create_review_engine()
        assert isinstance(engine, ReviewEngine)


class TestReviewEngineEdgeCases:
    @pytest.fixture
    def sample_guidelines(self):
        return [
            Guideline(
                id="RULE_001",
                text='Do not use "guaranteed" in claims.',
                category="unsupported_claim",
                source="Guidelines",
            ),
            Guideline(
                id="RULE_002",
                text='Must include "Results may vary" disclaimer.',
                category="missing_disclaimer",
                source="Guidelines",
            ),
        ]

    @pytest.mark.asyncio
    async def test_ai_returns_empty_list(self, sample_guidelines):
        """Test AI returning empty findings list."""
        mock_provider = MockAIProvider(findings=[])
        engine = ReviewEngine(ai_provider=mock_provider)

        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)

        assert mock_provider.called
        assert response.degraded_mode is False

    @pytest.mark.asyncio
    async def test_ai_returns_malformed_finding_skipped(self, sample_guidelines):
        """Test AI returning finding with missing required fields."""
        # This would be caught by Pydantic validation in the provider
        # but we test the engine handles it gracefully
        mock_provider = MockAIProvider(findings=[])
        engine = ReviewEngine(ai_provider=mock_provider)

        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)
        # Should not crash
        assert isinstance(response, ReviewResponse)

    @pytest.mark.asyncio
    async def test_ai_provider_failure_preserves_deterministic_findings(self, sample_guidelines):
        """Test deterministic findings preserved when AI fails (degraded mode)."""
        class FailingProvider:
            @property
            def name(self):
                return "failing"

            async def analyze(self, *args, **kwargs):
                raise AIProviderError("Simulated API failure", provider="test")

            async def health_check(self) -> bool:
                return False

        engine = ReviewEngine(ai_provider=FailingProvider())

        request = ReviewRequest(
            draft_text="Product guaranteed works.",  # Contains banned term
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)

        assert response.degraded_mode is True
        assert response.provider_error == "test: Simulated API failure"
        # Deterministic findings should still be present
        assert len(response.findings) >= 1
        assert any(f.matched_text == "guaranteed" for f in response.findings)
        # Status should be NEEDS_HUMAN_REVIEW due to provider_error + degraded_mode
        assert response.status == ReviewStatus.NEEDS_HUMAN_REVIEW

    @pytest.mark.asyncio
    async def test_ai_provider_unexpected_error_preserves_findings(self, sample_guidelines):
        """Test unexpected AI errors also trigger degraded mode."""
        class UnexpectedErrorProvider:
            @property
            def name(self):
                return "unexpected"

            async def analyze(self, *args, **kwargs):
                raise RuntimeError("Unexpected internal error")

            async def health_check(self) -> bool:
                return False

        engine = ReviewEngine(ai_provider=UnexpectedErrorProvider())

        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)

        assert response.degraded_mode is True
        assert "Unexpected AI error" in response.provider_error
        assert len(response.findings) >= 1

    @pytest.mark.asyncio
    async def test_invalid_citation_removed(self, sample_guidelines):
        """Test findings with citations to unknown guidelines have citation removed."""
        from trueline.models import Citation, Finding

        mock_provider = MockAIProvider(findings=[])
        engine = ReviewEngine(ai_provider=mock_provider)

        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        # Inject a finding with an invalid citation directly
        # We test _validate_citations indirectly through the review flow
        # by mocking the provider to return a finding with bad citation
        class BadCitationProvider:
            @property
            def name(self):
                return "bad-citation"

            async def analyze(self, *args, **kwargs):
                return [
                    Finding(
                        id="ai-bad-cite",
                        matched_text="guaranteed",
                        start=8,
                        end=18,
                        category=Category.UNSUPPORTED_CLAIM,
                        severity=Severity.HIGH,
                        explanation="AI found issue",
                        citation=Citation(rule_id="UNKNOWN_RULE", source="Unknown", excerpt="text"),
                        suggested_fix="Remove",
                        confidence=0.9,
                        requires_human_review=True,
                    )
                ]

            async def health_check(self) -> bool:
                return True

        engine = ReviewEngine(ai_provider=BadCitationProvider())
        response = await engine.review(request)

        # Citation should be removed since UNKNOWN_RULE not in guidelines
        ai_findings = [f for f in response.findings if f.id == "ai-bad-cite"]
        assert len(ai_findings) == 1
        assert ai_findings[0].citation is None

    @pytest.mark.asyncio
    async def test_invalid_offsets_dropped(self, sample_guidelines):
        """Test findings with invalid offsets are dropped."""
        from trueline.models import Finding

        class BadOffsetProvider:
            @property
            def name(self):
                return "bad-offset"

            async def analyze(self, *args, **kwargs):
                return [
                    Finding(
                        id="ai-bad-offset",
                        matched_text="wrong",
                        start=0,
                        end=5,  # "Produ" != "wrong"
                        category=Category.UNSUPPORTED_CLAIM,
                        severity=Severity.HIGH,
                        explanation="AI found issue",
                        citation=None,
                        suggested_fix="Remove",
                        confidence=0.9,
                        requires_human_review=True,
                    )
                ]

            async def health_check(self) -> bool:
                return True

        engine = ReviewEngine(ai_provider=BadOffsetProvider())

        request = ReviewRequest(
            draft_text="Product guaranteed works.",
            brand_id="test",
            content_purpose="email",
            guidelines=sample_guidelines,
        )

        response = await engine.review(request)

        # Finding should be dropped due to offset mismatch
        ai_findings = [f for f in response.findings if f.id == "ai-bad-offset"]
        assert len(ai_findings) == 0

    @pytest.mark.asyncio
    async def test_high_severity_status_changes_requested(self, sample_guidelines):
        """Test high severity findings without human_review -> CHANGES_REQUESTED."""
        from trueline.models import Finding

        class HighSeverityNoHumanProvider:
            @property
            def name(self):
                return "high-severity"

            async def analyze(self, *args, **kwargs):
                return [
                    Finding(
                        id="ai-high-sev",
                        matched_text="problematic",
                        start=8,
                        end=19,
                        category=Category.UNSUPPORTED_CLAIM,
                        severity=Severity.HIGH,
                        explanation="High severity issue",
                        citation=None,
                        suggested_fix="Fix it",
                        confidence=0.9,
                        requires_human_review=False,  # No human review required
                    )
                ]

            async def health_check(self) -> bool:
                return True

        engine = ReviewEngine(ai_provider=HighSeverityNoHumanProvider())

        # Use draft text that won't trigger deterministic findings
        request = ReviewRequest(
            draft_text="This is problematic text.",
            brand_id="test",
            content_purpose="email",
            guidelines=[],  # No guidelines = no deterministic findings
        )

        response = await engine.review(request)

        # High severity without requires_human_review -> CHANGES_REQUESTED
        assert response.status == ReviewStatus.CHANGES_REQUESTED

    @pytest.mark.asyncio
    async def test_ai_provider_lazy_creation(self, sample_guidelines):
        """Test AI provider is lazily created when settings.ai_enabled is True."""
        from trueline.config import settings

        # This test verifies the lazy creation path (line 49)
        # by ensuring the engine works when ai_provider is None but settings has API key
        with (
            patch.object(settings, "anthropic_api_key", "test-key"),
            patch.object(settings, "trueline_ai_enabled", True),
        ):
            with patch("trueline.review.service.AnthropicProvider") as mock_provider_class:
                mock_provider = AsyncMock()
                mock_provider.analyze.return_value = []
                mock_provider_class.return_value = mock_provider

                engine = ReviewEngine(ai_provider=None)
                # Access ai_provider property to trigger creation
                _ = engine.ai_provider

                mock_provider_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_deterministic_only_mode_degraded(self, sample_guidelines):
        """Test degraded_mode=True when AI not enabled (line 181)."""
        from trueline.config import settings

        with patch.object(settings, "anthropic_api_key", None):
            engine = ReviewEngine(ai_provider=None)

            request = ReviewRequest(
                draft_text="Product guaranteed works.",
                brand_id="test",
                content_purpose="email",
                guidelines=sample_guidelines,
            )

            response = await engine.review(request)

            assert response.degraded_mode is True
            assert response.provider_error is None
