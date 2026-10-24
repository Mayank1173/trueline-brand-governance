"""Tests for evaluation matching logic and metrics."""

import pytest
from datetime import date
from trueline.adapters.fastapi_adapter import convert_review_response
from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    FindingLabel,
    Guideline,
    ReviewResponse as AIReviewResponse,
    ReviewStatus,
    Severity,
)
from trueline.eval import (
    ExpectedFinding,
    MatchResult,
    PredictedFinding,
    compute_metrics,
    match_findings,
    compute_span_overlap,
)


class TestSpanOverlap:
    def test_exact_match(self):
        overlap = compute_span_overlap(10, 20, 10, 20)
        assert overlap == 1.0

    def test_partial_overlap_50_percent(self):
        # predicted [10:20], expected [15:25] -> overlap 5, expected_len 10 -> 0.5
        overlap = compute_span_overlap(10, 20, 15, 25)
        assert overlap == 0.5

    def test_partial_overlap_below_50(self):
        # predicted [10:15], expected [10:20] -> overlap 5, expected_len 10 -> 0.5
        overlap = compute_span_overlap(10, 15, 10, 20)
        assert overlap == 0.5

    def test_partial_overlap_below_50_percent(self):
        # predicted [10:14], expected [10:20] -> overlap 4, expected_len 10 -> 0.4
        overlap = compute_span_overlap(10, 14, 10, 20)
        assert overlap == 0.4

    def test_no_overlap(self):
        overlap = compute_span_overlap(10, 20, 30, 40)
        assert overlap == 0.0

    def test_contained(self):
        # predicted [10:30], expected [15:20] -> overlap 5, expected_len 5 -> 1.0
        overlap = compute_span_overlap(10, 30, 15, 20)
        assert overlap == 1.0

    def test_none_offsets(self):
        overlap = compute_span_overlap(None, None, 10, 20)
        assert overlap == 0.0


class TestMatchFindings:
    def setup_method(self):
        self.predicted_base = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="revolutionary",
            start=23,
            end=36,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )

        self.expected_base = ExpectedFinding(
            test_case_id="NS-TC-001",
            finding_id="NS-DRAFT-01-F1",
            rule_or_fact_id="NS-BAN-001",
            acceptable_alternate_ids=[],
            finding_type="banned_term",
            span_text="revolutionary",
            start=23,
            end=36,
            expected_finding="Test",
            citation="NS-DOC-EDITORIAL",
            severity="medium",
            label="violation",
            suggested_fix="Replace",
            human_review_required=False,
            case_type="positive",
        )

    def test_exact_match(self):
        matches, fps, fns = match_findings([self.predicted_base], [self.expected_base])
        assert len(matches) == 1
        assert len(fps) == 0
        assert len(fns) == 0
        assert matches[0].match_score == 1.0

    def test_rule_id_mismatch(self):
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-002",  # Different rule ID
            matched_text="revolutionary",
            start=23,
            end=36,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-002",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred], [self.expected_base])
        assert len(matches) == 0
        assert len(fps) == 1
        assert len(fns) == 1

    def test_span_below_50_percent(self):
        # Predicted span [23:30] (7 chars), expected [23:36] (13 chars)
        # Overlap = 7, expected_len = 13, ratio = 7/13 ≈ 0.54 > 0.5 -> match
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="revolutio",
            start=23,
            end=30,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred], [self.expected_base])
        assert len(matches) == 1

    def test_span_below_50_percent_no_match(self):
        # Predicted span [23:28] (5 chars), expected [23:36] (13 chars)
        # Overlap = 5, expected_len = 13, ratio = 5/13 ≈ 0.38 < 0.5 -> no match
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="revol",
            start=23,
            end=28,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred], [self.expected_base])
        assert len(matches) == 0
        assert len(fps) == 1
        assert len(fns) == 1

    def test_citation_rule_id_match(self):
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-OTHER-001",  # Different rule_id
            matched_text="revolutionary",
            start=23,
            end=36,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",  # But citation matches
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred], [self.expected_base])
        assert len(matches) == 1  # Should match via citation_rule_id

    def test_acceptable_alternate_ids(self):
        exp = ExpectedFinding(
            test_case_id="NS-TC-001",
            finding_id="NS-DRAFT-01-F1",
            rule_or_fact_id="NS-BAN-001",
            acceptable_alternate_ids=["NS-BAN-002", "NS-BAN-003"],
            finding_type="banned_term",
            span_text="revolutionary",
            start=23,
            end=36,
            expected_finding="Test",
            citation="NS-DOC-EDITORIAL",
            severity="medium",
            label="violation",
            suggested_fix="Replace",
            human_review_required=False,
            case_type="positive",
        )
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-002",  # In acceptable alternates
            matched_text="revolutionary",
            start=23,
            end=36,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-002",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred], [exp])
        assert len(matches) == 1

    def test_one_to_one_matching(self):
        # Two predictions, one expected - only one should match
        pred1 = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="revolutionary",
            start=23,
            end=36,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        pred2 = PredictedFinding(
            test_case_id="test",
            finding_id="pred-2",
            rule_id="NS-BAN-001",
            matched_text="revolutionary",
            start=23,
            end=36,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.8,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred1, pred2], [self.expected_base])
        assert len(matches) == 1
        assert len(fps) == 1


class TestComputeMetrics:
    def test_perfect_match(self):
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="test",
            start=0,
            end=4,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        exp = ExpectedFinding(
            test_case_id="NS-TC-001",
            finding_id="NS-DRAFT-01-F1",
            rule_or_fact_id="NS-BAN-001",
            acceptable_alternate_ids=[],
            finding_type="banned_term",
            span_text="test",
            start=0,
            end=4,
            expected_finding="Test",
            citation="NS-DOC-EDITORIAL",
            severity="medium",
            label="violation",
            suggested_fix="Replace",
            human_review_required=False,
            case_type="positive",
        )
        pred_obj = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="test",
            start=0,
            end=4,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        exp_obj = ExpectedFinding(
            test_case_id="NS-TC-001",
            finding_id="NS-DRAFT-01-F1",
            rule_or_fact_id="NS-BAN-001",
            acceptable_alternate_ids=[],
            finding_type="banned_term",
            span_text="test",
            start=0,
            end=4,
            expected_finding="Test",
            citation="NS-DOC-EDITORIAL",
            severity="medium",
            label="violation",
            suggested_fix="Replace",
            human_review_required=False,
            case_type="positive",
        )
        matches, fps, fns = match_findings([pred_obj], [exp_obj])
        metrics = compute_metrics(
            matches, [], [], [pred_obj], [exp_obj], set(), 0
        )
        assert metrics["finding_precision"] == 1.0
        assert metrics["finding_recall"] == 1.0
        assert metrics["finding_f1"] == 1.0
        assert metrics["counts"]["true_positives"] == 1

    def test_all_false_positives(self):
        pred = PredictedFinding(
            test_case_id="test",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="test",
            start=0,
            end=4,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        matches, fps, fns = match_findings([pred], [])
        metrics = compute_metrics(
            matches, fps, [], [pred], [], set(), 0
        )
        assert metrics["finding_precision"] == 0.0
        assert metrics["finding_recall"] == 0.0
        assert metrics["counts"]["false_positives"] == 1

    def test_all_false_negatives(self):
        exp = ExpectedFinding(
            test_case_id="NS-TC-001",
            finding_id="NS-DRAFT-01-F1",
            rule_or_fact_id="NS-BAN-001",
            acceptable_alternate_ids=[],
            finding_type="banned_term",
            span_text="test",
            start=0,
            end=4,
            expected_finding="Test",
            citation="NS-DOC-EDITORIAL",
            severity="medium",
            label="violation",
            suggested_fix="Replace",
            human_review_required=False,
            case_type="positive",
        )
        matches, fps, fns = match_findings([], [exp])
        metrics = compute_metrics(
            matches, [], fns, [], [exp], set(), 0
        )
        assert metrics["finding_precision"] == 0.0
        assert metrics["finding_recall"] == 0.0
        assert metrics["counts"]["false_negatives"] == 1

    def test_compliant_inputs_fp_rate(self):
        pred = PredictedFinding(
            test_case_id="draft:NS-DRAFT-10",
            finding_id="pred-1",
            rule_id="NS-BAN-001",
            matched_text="test",
            start=0,
            end=4,
            category="banned_language",
            severity="medium",
            explanation="Test",
            citation_rule_id="NS-BAN-001",
            citation_source_type="guideline",
            suggested_fix="Replace",
            confidence=0.9,
            requires_human_review=False,
        )
        compliant_inputs = {("draft", "NS-DRAFT-10"), ("draft", "NS-DRAFT-11")}
        metrics = compute_metrics(
            [], [pred], [], [pred], [], compliant_inputs, 1
        )
        # 1 compliant input has findings out of 2 total compliant inputs
        assert metrics["false_positive_rate_compliant"] == 0.5
        assert metrics["false_positives_per_compliant_input"] == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])