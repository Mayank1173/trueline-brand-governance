"""FastAPI integration tests for the AI Review Engine via adapter.

These tests exercise the full chain:
FastAPI Request → Adapter → AI Engine → Adapter → FastAPI Response
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from trueline.adapters.fastapi_adapter import (
    FastAPICategory,
    FastAPIReviewRequest,
    FastAPIReviewResponse,
    FastAPISeverity,
    FastAPISourceType,
    convert_review_request,
    convert_review_response,
)
from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    FindingLabel,
    Guideline,
    ReviewRequest as AIReviewRequest,
    ReviewResponse as AIReviewResponse,
    ReviewStatus,
    Severity,
)
from trueline.review.service import ReviewEngine


class MockAIProvider:
    """Mock AI provider for integration testing."""

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
            from trueline.providers.base import AIProviderError
            raise AIProviderError(self._error_message, provider="mock")
        return self._findings

    async def health_check(self) -> bool:
        return not self._should_fail


def create_test_guidelines():
    """Create test guidelines matching FastAPI deterministic engine expectations."""
    return [
        Guideline(
            id="RULE_001",
            text='Do not use "guaranteed" in claims.',
            category="unsupported_claim",
            source="Brand Guidelines",
            document_id="NS-DOC-EDITORIAL",
            section="2.1",
        ),
        Guideline(
            id="RULE_002",
            text='Must include "Results may vary" disclaimer.',
            category="missing_disclaimer",
            source="Brand Guidelines",
            document_id="NS-DOC-EDITORIAL",
            section="3.1",
        ),
        Guideline(
            id="RULE_003",
            text='Avoid "revolutionary" - use "innovative" instead.',
            category="banned_term",
            source="Brand Guidelines",
            document_id="NS-DOC-EDITORIAL",
            section="4.1",
        ),
    ]


def create_test_facts():
    """Create test approved facts."""
    return [
        ApprovedFact(
            id="FACT_001",
            claim="Northstar processes 10M transactions daily",
            evidence="Internal metrics dashboard Q3 2024",
            category="performance",
            valid_from="2024-01-01",
            expires_on="2025-12-31",
        ),
        ApprovedFact(
            id="FACT_002",
            claim="Northstar uptime is 99.99%",
            evidence="SLA report 2024",
            category="reliability",
            valid_from="2024-01-01",
            expires_on="2024-06-30",  # Expired
        ),
    ]


class TestFastAPIAdapterIntegration:
    """Test the adapter with realistic AI engine responses."""

    def setup_method(self):
        self.guidelines = create_test_guidelines()
        self.facts = create_test_facts()
        self.draft_text = "Our revolutionary product is guaranteed to work."

    def test_request_conversion(self):
        """Test FastAPI request → AI engine request conversion."""
        fastapi_request = FastAPIReviewRequest(
            brand_id="northstar",
            draft_text=self.draft_text,
            purpose="marketing",
        )

        ai_request = convert_review_request(
            fastapi_request, self.guidelines, self.facts, date(2026, 1, 15)
        )

        assert isinstance(ai_request, AIReviewRequest)
        assert ai_request.draft_text == self.draft_text
        assert ai_request.brand_id == "northstar"
        assert ai_request.content_purpose == "marketing"
        assert ai_request.guidelines == self.guidelines
        assert ai_request.approved_facts == self.facts
        assert ai_request.evaluation_date == "2026-01-15"

    def test_response_conversion_deterministic_findings(self):
        """Test AI engine response → FastAPI response with deterministic findings."""
        ai_findings = [
            Finding(
                id="det-RULE_001-13",
                matched_text="guaranteed",
                start=13,
                end=23,
                category=Category.UNSUPPORTED_CLAIM,
                severity=Severity.HIGH,
                explanation="Text contains banned term per guideline RULE_001: Do not use \"guaranteed\" in claims.",
                citation=Citation(
                    rule_id="RULE_001",
                    source="Brand Guidelines",
                    excerpt='Do not use "guaranteed" in claims.',
                    document_id="NS-DOC-EDITORIAL",
                    section="2.1",
                ),
                suggested_fix="Use 'ensured' instead",
                confidence=0.95,
                requires_human_review=True,
                label=None,
                rule_id="RULE_001",
            ),
            Finding(
                id="det-RULE_003-4",
                matched_text="revolutionary",
                start=4,
                end=15,
                category=Category.BANNED_TERM,
                severity=Severity.HIGH,
                explanation="Text contains banned term per guideline RULE_003: Avoid \"revolutionary\" - use \"innovative\" instead.",
                citation=Citation(
                    rule_id="RULE_003",
                    source="Brand Guidelines",
                    excerpt='Avoid "revolutionary" - use "innovative" instead.',
                    document_id="NS-DOC-EDITORIAL",
                    section="4.1",
                ),
                suggested_fix="Use innovative",
                confidence=0.95,
                requires_human_review=True,
                label=None,
                rule_id="RULE_003",
            ),
        ]

        ai_response = AIReviewResponse(
            review_id="review-abc123",
            status=ReviewStatus.CHANGES_REQUESTED,
            findings=ai_findings,
            degraded_mode=False,
            provider_error=None,
        )

        fastapi_response = convert_review_response(
            ai_response, self.draft_text, self.guidelines, self.facts
        )

        assert isinstance(fastapi_response, FastAPIReviewResponse)
        assert fastapi_response.review_id == "review-abc123"
        assert fastapi_response.status.value == "changes_requested"
        assert len(fastapi_response.findings) == 2

        # Check first finding (guaranteed)
        f1 = fastapi_response.findings[0]
        assert f1.id == "det-RULE_001-13"
        assert f1.finding_id == "det-RULE_001-13"
        assert f1.rule_id == "RULE_001"
        assert f1.matched_text == "guaranteed"
        assert f1.start == 13  # ASCII text, Unicode == UTF-16
        assert f1.end == 23
        assert f1.category == FastAPICategory.UNSUPPORTED_CLAIM
        assert f1.severity == FastAPISeverity.HIGH
        assert f1.citation is not None
        assert f1.citation.rule_id == "RULE_001"
        assert f1.citation.source_type == FastAPISourceType.GUIDELINE
        assert f1.citation.source_id == "RULE_001"
        assert f1.citation.source_version is None
        assert f1.citation.quoted_text == 'Do not use "guaranteed" in claims.'
        assert f1.citation.valid_until is None
        assert f1.requires_human_review is True

        # Check second finding (revolutionary)
        f2 = fastapi_response.findings[1]
        assert f2.matched_text == "revolutionary"
        assert f2.category == FastAPICategory.BANNED_TERM
        assert f2.rule_id == "RULE_003"

    def test_response_conversion_ai_findings_with_label(self):
        """Test AI findings with FindingLabel are correctly mapped."""
        ai_findings = [
            Finding(
                id="ai-1",
                matched_text="unbeatable",
                start=10,
                end=20,
                category=Category.UNSUPPORTED_CLAIM,
                severity=Severity.HIGH,
                explanation="AI detected unsupported claim",
                citation=Citation(
                    rule_id="RULE_001",
                    source="Brand Guidelines",
                    excerpt="Do not use absolute claims",
                ),
                suggested_fix="Use 'highly effective'",
                confidence=0.85,
                requires_human_review=False,
                label=FindingLabel.NEEDS_HUMAN_JUDGEMENT,
                rule_id="RULE_001",
            ),
            Finding(
                id="ai-2",
                matched_text="outdated claim",
                start=30,
                end=42,
                category=Category.UNSUPPORTED_CLAIM,
                severity=Severity.HIGH,
                explanation="Contradicted by current facts",
                citation=Citation(
                    rule_id="FACT_001",
                    source="Internal Metrics",
                    excerpt="Processes 10M daily",
                ),
                suggested_fix="Update to current figures",
                confidence=0.9,
                requires_human_review=False,
                label=FindingLabel.CONTRADICTED,
                rule_id="FACT_001",
            ),
        ]

        ai_response = AIReviewResponse(
            review_id="review-ai-123",
            status=ReviewStatus.NEEDS_HUMAN_REVIEW,
            findings=ai_findings,
            degraded_mode=False,
            provider_error=None,
        )

        fastapi_response = convert_review_response(
            ai_response, "test text with unbeatable and outdated claim here", self.guidelines, self.facts
        )

        # Both should have requires_human_review = True due to labels
        for f in fastapi_response.findings:
            assert f.requires_human_review is True

        assert fastapi_response.findings[0].ai_label == "needs_human_judgement"
        assert fastapi_response.findings[1].ai_label == "contradicted"

        # Status should be NEEDS_HUMAN_REVIEW
        assert fastapi_response.status.value == "needs_human_review"

    def test_response_conversion_fact_citation(self):
        """Test citation conversion for approved facts."""
        ai_findings = [
            Finding(
                id="fact-1",
                matched_text="Free returns within 30 days",
                start=10,
                end=35,
                category=Category.UNSUPPORTED_CLAIM,
                severity=Severity.HIGH,
                explanation="Fact expired",
                citation=Citation(
                    rule_id="FACT_002",
                    source="SLA Report",
                    excerpt="Uptime 99.99%",
                ),
                confidence=1.0,
                requires_human_review=True,
                label=FindingLabel.OUTDATED,
                rule_id="FACT_002",
            ),
        ]

        ai_response = AIReviewResponse(
            review_id="review-fact-1",
            status=ReviewStatus.NEEDS_HUMAN_REVIEW,
            findings=ai_findings,
        )

        fastapi_response = convert_review_response(
            ai_response, "Offer: Free returns within 30 days.", self.guidelines, self.facts
        )

        f = fastapi_response.findings[0]
        assert f.citation is not None
        assert f.citation.source_type == FastAPISourceType.APPROVED_FACT
        assert f.citation.source_id == "FACT_002"
        assert f.citation.valid_until == date(2024, 6, 30)

    def test_response_conversion_missing_phrase_no_offsets(self):
        """Test missing required phrase findings have null offsets."""
        ai_findings = [
            Finding(
                id="missing-1",
                matched_text="",
                start=0,
                end=0,
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                explanation="Missing required disclaimer",
                citation=Citation(
                    rule_id="RULE_002",
                    source="Brand Guidelines",
                    excerpt='Must include "Results may vary"',
                ),
                suggested_fix="Add 'Results may vary'",
                confidence=0.9,
                requires_human_review=True,
                label=None,
                rule_id="RULE_002",
            ),
        ]

        ai_response = AIReviewResponse(
            review_id="review-missing-1",
            status=ReviewStatus.CHANGES_REQUESTED,
            findings=ai_findings,
        )

        fastapi_response = convert_review_response(
            ai_response, "Product works great.", self.guidelines, self.facts
        )

        f = fastapi_response.findings[0]
        assert f.matched_text == ""
        assert f.start is None
        assert f.end is None
        assert f.category == FastAPICategory.REQUIRED_PHRASE


class TestReviewEngineIntegration:
    """Test the full ReviewEngine with mocked AI provider through adapter."""

    @pytest.mark.asyncio
    async def test_full_pipeline_deterministic_only(self):
        """Test full pipeline with no AI provider (deterministic only)."""
        guidelines = create_test_guidelines()
        facts = create_test_facts()
        draft = "Our product is guaranteed to work."

        engine = ReviewEngine(ai_provider=None)
        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="northstar",
            content_purpose="marketing",
            guidelines=guidelines,
            approved_facts=facts,
        )

        ai_response = await engine.review(ai_request)

        # Should have deterministic findings
        assert len(ai_response.findings) >= 1
        assert any(f.matched_text == "guaranteed" for f in ai_response.findings)

        # Convert to FastAPI response
        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, facts
        )

        assert fastapi_response.status.value in ("changes_requested", "needs_human_review")
        assert len(fastapi_response.findings) >= 1
        for f in fastapi_response.findings:
            assert f.rule_id is not None
            assert f.citation is not None
            assert f.citation.source_type == FastAPISourceType.GUIDELINE

    @pytest.mark.asyncio
    async def test_full_pipeline_with_ai_success(self):
        """Test full pipeline with successful AI provider."""
        guidelines = create_test_guidelines()
        facts = create_test_facts()
        draft = "Our revolutionary product guarantees success."

        ai_finding = Finding(
            id="ai-1",
            matched_text="revolutionary",
            start=4,
            end=15,
            category=Category.BANNED_TERM,
            severity=Severity.HIGH,
            explanation="Banned hype word",
            citation=Citation(
                rule_id="RULE_003",
                source="Brand Guidelines",
                excerpt='Avoid "revolutionary"',
            ),
            suggested_fix="Use innovative",
            confidence=0.9,
            requires_human_review=True,
            label=FindingLabel.VIOLATION,
            rule_id="RULE_003",
        )

        mock_provider = MockAIProvider(findings=[ai_finding])
        engine = ReviewEngine(ai_provider=mock_provider)

        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="northstar",
            content_purpose="marketing",
            guidelines=guidelines,
            approved_facts=facts,
        )

        ai_response = await engine.review(ai_request)

        assert mock_provider.called
        assert ai_response.degraded_mode is False
        assert ai_response.provider_error is None
        assert len(ai_response.findings) >= 2  # deterministic + AI

        # Convert to FastAPI
        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, facts
        )

        assert fastapi_response.status.value == "needs_human_review"
        assert len(fastapi_response.findings) >= 2

    @pytest.mark.asyncio
    async def test_full_pipeline_ai_failure_degraded_mode(self):
        """Test AI failure preserves deterministic findings in degraded mode."""
        guidelines = create_test_guidelines()
        facts = create_test_facts()
        draft = "Our product is guaranteed to work."

        mock_provider = MockAIProvider(should_fail=True, error_message="API timeout")
        engine = ReviewEngine(ai_provider=mock_provider)

        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="northstar",
            content_purpose="marketing",
            guidelines=guidelines,
            approved_facts=facts,
        )

        ai_response = await engine.review(ai_request)

        assert ai_response.degraded_mode is True
        assert ai_response.provider_error is not None
        assert "API timeout" in ai_response.provider_error
        # Deterministic findings should still be present
        assert len(ai_response.findings) >= 1
        assert any(f.matched_text == "guaranteed" for f in ai_response.findings)

        # Convert to FastAPI - status should be NEEDS_HUMAN_REVIEW due to degraded mode
        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, facts
        )

        assert fastapi_response.status.value == "needs_human_review"
        assert len(fastapi_response.findings) >= 1

    @pytest.mark.asyncio
    async def test_full_pipeline_ai_failure_no_degraded_raises(self):
        """Test AI failure raises when degraded_mode=False."""
        guidelines = create_test_guidelines()
        facts = create_test_facts()
        draft = "Our product is guaranteed to work."

        mock_provider = MockAIProvider(should_fail=True, error_message="API timeout")
        engine = ReviewEngine(ai_provider=mock_provider)
        engine._degraded_mode = False

        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="northstar",
            content_purpose="marketing",
            guidelines=guidelines,
            approved_facts=facts,
        )

        with pytest.raises(Exception) as exc_info:
            await engine.review(ai_request)

        assert "API timeout" in str(exc_info.value)


class TestUnicodeOffsetsEndToEnd:
    """Test Unicode offset conversion through the full pipeline."""

    @pytest.mark.asyncio
    async def test_emoji_in_draft_before_match(self):
        """Test emoji before matched text - offsets should be correct for frontend."""
        guidelines = [
            Guideline(
                id="RULE_EMOJI",
                text='Do not use "guaranteed"',
                category="banned_term",
                source="Guidelines",
            ),
        ]
        draft = "Product 🚀 guaranteed"  # 🚀 = U+1F680 (2 UTF-16 units)

        engine = ReviewEngine(ai_provider=None)
        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="test",
            content_purpose="test",
            guidelines=guidelines,
        )

        ai_response = await engine.review(ai_request)

        assert len(ai_response.findings) == 1
        finding = ai_response.findings[0]
        assert finding.matched_text == "guaranteed"
        # AI engine uses Unicode code points
        assert finding.start == 10  # "Product " (8) + 🚀 (1) + " " (1) = 10
        assert finding.end == 20

        # Convert to FastAPI (UTF-16)
        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, []
        )

        fastapi_finding = fastapi_response.findings[0]
        # UTF-16: "Product " (8) + 🚀 (2) + " " (1) = 11
        assert fastapi_finding.start == 11
        assert fastapi_finding.end == 21

        # Verify frontend slicing would work: draft.slice(11, 21) in JS
        # In Python, verify by converting back
        from trueline.adapters.fastapi_adapter import utf16_to_unicode_offset
        unicode_start = utf16_to_unicode_offset(draft, fastapi_finding.start)
        unicode_end = utf16_to_unicode_offset(draft, fastapi_finding.end)
        assert draft[unicode_start:unicode_end] == "guaranteed"

    @pytest.mark.asyncio
    async def test_emoji_inside_matched_text(self):
        """Test emoji inside matched text using explicit patterns."""
        guidelines = [
            Guideline(
                id="RULE_EMOJI2",
                text='Do not use "🚀 launch"',
                category="banned_term",
                source="Guidelines",
                patterns=[r"🚀 launch"],
            ),
        ]
        draft = "Product 🚀 launch today"

        engine = ReviewEngine(ai_provider=None)
        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="test",
            content_purpose="test",
            guidelines=guidelines,
        )

        ai_response = await engine.review(ai_request)

        assert len(ai_response.findings) == 1
        finding = ai_response.findings[0]
        assert finding.matched_text == "🚀 launch"

        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, []
        )

        fastapi_finding = fastapi_response.findings[0]
        # Verify the matched text is correct
        from trueline.adapters.fastapi_adapter import utf16_to_unicode_offset
        unicode_start = utf16_to_unicode_offset(draft, fastapi_finding.start)
        unicode_end = utf16_to_unicode_offset(draft, fastapi_finding.end)
        assert draft[unicode_start:unicode_end] == "🚀 launch"

    @pytest.mark.asyncio
    async def test_cjk_text_offsets(self):
        """Test CJK text offsets (BMP, 1:1 mapping)."""
        guidelines = [
            Guideline(
                id="RULE_CJK",
                text='Do not use "保证"',
                category="banned_term",
                source="Guidelines",
            ),
        ]
        draft = "产品 保证 质量"  # "产品 " (3) + "保证" (2) + " 质量" (3)

        engine = ReviewEngine(ai_provider=None)
        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="test",
            content_purpose="test",
            guidelines=guidelines,
        )

        ai_response = await engine.review(ai_request)

        assert len(ai_response.findings) == 1
        finding = ai_response.findings[0]
        assert finding.matched_text == "保证"
        # CJK is BMP, so Unicode == UTF-16
        assert finding.start == 3
        assert finding.end == 5

        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, []
        )

        fastapi_finding = fastapi_response.findings[0]
        assert fastapi_finding.start == 3
        assert fastapi_finding.end == 5

        from trueline.adapters.fastapi_adapter import utf16_to_unicode_offset
        unicode_start = utf16_to_unicode_offset(draft, fastapi_finding.start)
        unicode_end = utf16_to_unicode_offset(draft, fastapi_finding.end)
        assert draft[unicode_start:unicode_end] == "保证"

    @pytest.mark.asyncio
    async def test_accented_text_offsets(self):
        """Test accented characters (BMP, 1:1 mapping)."""
        guidelines = [
            Guideline(
                id="RULE_ACCENT",
                text='Do not use "café"',
                category="banned_term",
                source="Guidelines",
            ),
        ]
        draft = "Visit our café today"  # "café" = c a f é (é = U+00E9, BMP)

        engine = ReviewEngine(ai_provider=None)
        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="test",
            content_purpose="test",
            guidelines=guidelines,
        )

        ai_response = await engine.review(ai_request)

        assert len(ai_response.findings) == 1
        finding = ai_response.findings[0]
        assert finding.matched_text == "café"
        assert finding.start == 10
        assert finding.end == 14

        fastapi_response = convert_review_response(
            ai_response, draft, guidelines, []
        )

        fastapi_finding = fastapi_response.findings[0]
        assert fastapi_finding.start == 10
        assert fastapi_finding.end == 14


class TestCategoryMappingIntegration:
    """Test category mapping through the full pipeline."""

    @pytest.mark.asyncio
    async def test_fact_metadata_category(self):
        """Test FACT_METADATA category maps correctly."""
        guidelines = [
            Guideline(
                id="RULE_FACT",
                text="Check fact expiry",
                category="fact_metadata",
                source="Guidelines",
            ),
        ]
        draft = "Free returns within 30 days"

        engine = ReviewEngine(ai_provider=None)
        ai_request = AIReviewRequest(
            draft_text=draft,
            brand_id="test",
            content_purpose="test",
            guidelines=guidelines,
        )

        ai_response = await engine.review(ai_request)

        # Deterministic engine may not produce fact_metadata without fact checking
        # This test verifies the category mapping exists in adapter
        from trueline.adapters.fastapi_adapter import map_category
        from trueline.models import Category

        assert map_category(Category.FACT_METADATA) == FastAPICategory.FACT_METADATA
        assert map_category(Category.APPROVED_FACT) == FastAPICategory.APPROVED_FACT

    @pytest.mark.asyncio
    async def test_all_ai_categories_mapped(self):
        """Verify all AI categories have a mapping."""
        from trueline.adapters.fastapi_adapter import map_category
        from trueline.models import Category

        for cat in Category:
            result = map_category(cat)
            assert result is not None
            assert isinstance(result, FastAPICategory)


class TestResponseSchemaValidation:
    """Verify FastAPI response schema compliance."""

    def test_finding_response_has_required_fields(self):
        """Verify all required FindingResponse fields are present."""
        from trueline.adapters.fastapi_adapter import FastAPIFindingResponse

        finding = FastAPIFindingResponse(
            id="test-1",
            finding_id="test-1",
            rule_id="RULE_001",
            matched_text="test",
            start=0,
            end=4,
            category=FastAPICategory.BANNED_TERM,
            severity=FastAPISeverity.HIGH,
            explanation="Test",
            citation=None,
            suggested_fix=None,
            confidence=0.9,
            requires_human_review=False,
        )

        dumped = finding.model_dump()
        required_fields = {
            "id", "finding_id", "rule_id", "matched_text", "start", "end",
            "category", "severity", "explanation", "citation", "suggested_fix",
            "confidence", "requires_human_review", "ai_label"
        }
        assert set(dumped.keys()) == required_fields

    def test_citation_out_has_required_fields(self):
        """Verify all required CitationOut fields are present."""
        from trueline.adapters.fastapi_adapter import FastAPICitationOut
        from trueline.adapters.fastapi_adapter import FastAPISourceType
        from datetime import date

        citation = FastAPICitationOut(
            rule_id="RULE_001",
            source="Guidelines",
            excerpt="Test excerpt",
            source_type=FastAPISourceType.GUIDELINE,
            source_id="NS-DOC-001",
            source_version="v1.0",
            quoted_text="Test excerpt",
            valid_until=date(2025, 12, 31),
        )

        dumped = citation.model_dump()
        required_fields = {
            "rule_id", "source", "excerpt", "source_type", "source_id",
            "source_version", "quoted_text", "valid_until"
        }
        assert set(dumped.keys()) == required_fields

    def test_review_response_has_required_fields(self):
        """Verify all required ReviewResponse fields are present."""
        from trueline.adapters.fastapi_adapter import FastAPIReviewResponse, FastAPIReviewStatus

        response = FastAPIReviewResponse(
            review_id="review-1",
            status=FastAPIReviewStatus.APPROVED,
            findings=[],
        )

        dumped = response.model_dump()
        required_fields = {"review_id", "status", "findings"}
        assert set(dumped.keys()) == required_fields