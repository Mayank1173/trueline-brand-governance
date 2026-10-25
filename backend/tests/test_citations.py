from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.citations import CitationValidationError, validate_finding_citations
from app.rule_engine.models import CitationDraft, FindingDraft


def make_finding(citation: CitationDraft | None) -> FindingDraft:
    return FindingDraft(
        rule_id="BR-TEST-001",
        matched_text="bad",
        start=0,
        end=3,
        category="banned_term",
        severity="medium",
        explanation="Test",
        citation=citation,
        suggested_fix="good",
        confidence=1.0,
        requires_human_review=False,
    )


def guideline(**overrides):
    values = {
        "id": "GL-1",
        "brand_id": "brand_001",
        "rule_id": "BR-TEST-001",
        "version": "v1",
        "content": "Exact source text.",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def fact(**overrides):
    values = {
        "id": "FACT-1",
        "brand_id": "brand_001",
        "version": "v1",
        "statement": "Approved fact text.",
        "source_version": "v1",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def citation(**overrides) -> CitationDraft:
    values = {
        "source_type": "guideline",
        "source_id": "GL-1",
        "source_version": "v1",
        "source_label": "Test §1",
        "quoted_text": "Exact source text.",
    }
    values.update(overrides)
    return CitationDraft(**values)


def test_valid_guideline_citation_passes():
    validate_finding_citations(
        [make_finding(citation())],
        brand_id="brand_001",
        guidelines={"GL-1": guideline()},
        facts={},
    )


def test_finding_without_citation_is_allowed():
    validate_finding_citations(
        [make_finding(None)],
        brand_id="brand_001",
        guidelines={},
        facts={},
    )


def test_unknown_source_is_rejected():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation(source_id="GL-MISSING"))],
            brand_id="brand_001",
            guidelines={"GL-1": guideline()},
            facts={},
        )


def test_source_from_another_brand_is_rejected():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation())],
            brand_id="brand_001",
            guidelines={"GL-1": guideline(brand_id="other")},
            facts={},
        )


def test_rule_id_must_match_source_rule():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation())],
            brand_id="brand_001",
            guidelines={"GL-1": guideline(rule_id="BR-OTHER")},
            facts={},
        )


def test_wrong_version_is_rejected():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation(source_version="v2"))],
            brand_id="brand_001",
            guidelines={"GL-1": guideline()},
            facts={},
        )


def test_unversioned_guideline_citation_is_allowed():
    validate_finding_citations(
        [make_finding(citation(source_version=None))],
        brand_id="brand_001",
        guidelines={"GL-1": guideline(version=None)},
        facts={},
    )


def test_unversioned_guideline_rejects_invented_citation_version():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation(source_version="v1"))],
            brand_id="brand_001",
            guidelines={"GL-1": guideline(version=None)},
            facts={},
        )


def test_versioned_guideline_rejects_missing_citation_version():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation(source_version=None))],
            brand_id="brand_001",
            guidelines={"GL-1": guideline()},
            facts={},
        )


def test_quote_not_present_in_source_is_rejected():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation(quoted_text="Invented quote"))],
            brand_id="brand_001",
            guidelines={"GL-1": guideline()},
            facts={},
        )


def test_valid_approved_fact_citation_passes():
    validate_finding_citations(
        [
            make_finding(
                citation(
                    source_type="approved_fact",
                    source_id="FACT-1",
                    quoted_text="Approved fact text.",
                )
            )
        ],
        brand_id="brand_001",
        guidelines={},
        facts={"FACT-1": fact()},
    )


def test_unversioned_approved_fact_citation_is_allowed():
    validate_finding_citations(
        [
            make_finding(
                citation(
                    source_type="approved_fact",
                    source_id="FACT-1",
                    source_version=None,
                    quoted_text="Approved fact text.",
                )
            )
        ],
        brand_id="brand_001",
        guidelines={},
        facts={"FACT-1": fact(source_version=None)},
    )


def test_unversioned_approved_fact_rejects_invented_citation_version():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [
                make_finding(
                    citation(
                        source_type="approved_fact",
                        source_id="FACT-1",
                        quoted_text="Approved fact text.",
                    )
                )
            ],
            brand_id="brand_001",
            guidelines={},
            facts={"FACT-1": fact(source_version=None)},
        )


def test_unknown_approved_fact_is_rejected():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [
                make_finding(
                    citation(
                        source_type="approved_fact",
                        source_id="FACT-MISSING",
                        quoted_text="Approved fact text.",
                    )
                )
            ],
            brand_id="brand_001",
            guidelines={},
            facts={},
        )


def test_unsupported_source_type_is_rejected():
    with pytest.raises(CitationValidationError):
        validate_finding_citations(
            [make_finding(citation(source_type="brand_config"))],
            brand_id="brand_001",
            guidelines={"GL-1": guideline()},
            facts={},
        )
