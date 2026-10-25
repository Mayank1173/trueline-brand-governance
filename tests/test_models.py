"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError
from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    Guideline,
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
    Severity,
)


class TestCitation:
    def test_valid_citation(self):
        c = Citation(rule_id="RULE_001", source="Guidelines", excerpt="Do not use X")
        assert c.rule_id == "RULE_001"
        assert c.source == "Guidelines"
        assert c.excerpt == "Do not use X"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            Citation(rule_id="RULE_001", source="Guidelines", excerpt="text", extra="field")


class TestFinding:
    def test_valid_finding(self):
        f = Finding(
            id="f1",
            matched_text="guaranteed",
            start=10,
            end=20,
            category=Category.UNSUPPORTED_CLAIM,
            severity=Severity.HIGH,
            explanation="Violates rule",
            citation=Citation(rule_id="RULE_001", source="G", excerpt="text"),
            suggested_fix="Remove",
            confidence=0.9,
            requires_human_review=True,
        )
        assert f.matched_text == "guaranteed"
        assert f.confidence == 0.9

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            Finding(
                id="f1",
                matched_text="test",
                start=0,
                end=4,
                category=Category.BANNED_TERM,
                severity=Severity.LOW,
                explanation="test",
                confidence=1.5,  # Invalid > 1.0
            )

        with pytest.raises(ValidationError):
            Finding(
                id="f1",
                matched_text="test",
                start=0,
                end=4,
                category=Category.BANNED_TERM,
                severity=Severity.LOW,
                explanation="test",
                confidence=-0.1,  # Invalid < 0.0
            )

    def test_end_before_start_invalid(self):
        with pytest.raises(ValidationError):
            Finding(
                id="f1",
                matched_text="test",
                start=10,
                end=5,  # end < start
                category=Category.BANNED_TERM,
                severity=Severity.LOW,
                explanation="test",
                confidence=0.5,
            )

    def test_null_citation_and_fix(self):
        f = Finding(
            id="f1",
            matched_text="test",
            start=0,
            end=4,
            category=Category.BANNED_TERM,
            severity=Severity.LOW,
            explanation="test",
            citation=None,
            suggested_fix=None,
            confidence=0.5,
            requires_human_review=False,
        )
        assert f.citation is None
        assert f.suggested_fix is None

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            Finding(
                id="f1",
                matched_text="test",
                start=0,
                end=4,
                category=Category.BANNED_TERM,
                severity=Severity.LOW,
                explanation="test",
                confidence=0.5,
                requires_human_review=False,
                extra_field="not allowed",
            )


class TestGuideline:
    def test_valid_guideline(self):
        g = Guideline(
            id="RULE_001",
            title="Test Rule",
            text="Do not use X",
            category="banned_term",
            source="Guidelines",
        )
        assert g.id == "RULE_001"

    def test_optional_title(self):
        g = Guideline(
            id="RULE_001",
            text="Do not use X",
            category="banned_term",
            source="Guidelines",
        )
        assert g.title is None


class TestApprovedFact:
    def test_valid_fact(self):
        f = ApprovedFact(
            id="FACT_001",
            claim="We process 10M transactions",
            evidence="Dashboard",
            category="performance",
        )
        assert f.claim == "We process 10M transactions"


class TestReviewRequest:
    def test_valid_request(self):
        req = ReviewRequest(
            draft_text="Test draft",
            brand_id="brand1",
            content_purpose="email",
        )
        assert req.draft_text == "Test draft"
        assert req.guidelines == []
        assert req.approved_facts == []


class TestReviewResponse:
    def test_valid_response(self):
        resp = ReviewResponse(
            status=ReviewStatus.APPROVED,
            findings=[],
        )
        assert resp.status == ReviewStatus.APPROVED
        assert resp.findings == []

    def test_degraded_mode_flag(self):
        resp = ReviewResponse(
            status=ReviewStatus.NEEDS_HUMAN_REVIEW,
            findings=[],
            degraded_mode=True,
            provider_error="API timeout",
        )
        assert resp.degraded_mode is True
        assert resp.provider_error == "API timeout"
