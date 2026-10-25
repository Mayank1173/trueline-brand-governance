from __future__ import annotations

import pytest

from trueline.eval import (
    PredictedFinding,
    _is_acceptable_alternative,
    build_guidelines_and_facts,
    convert_to_predicted,
    load_northstar_data,
    run_evaluation,
    run_review_engine,
)


@pytest.fixture(scope="module")
def dataset():
    return load_northstar_data()


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory):
    return run_evaluation(tmp_path_factory.mktemp("northstar-eval"))


def test_loads_authoritative_utf8_dataset(dataset):
    eval_data, _, guidelines_data = dataset
    assert eval_data["evaluation_as_of_date"] == "2026-10-23"
    assert len(eval_data["test_cases"]) == 54
    assert len(guidelines_data["rules"]) == 23
    snippet = next(s for s in eval_data["snippets"] if s["id"] == "NS-SNIP-04")
    assert "\U0001f4c5" in snippet["text"]


def test_emoji_span_is_normalized_to_code_points(dataset):
    _, _, guidelines_data = dataset
    guidelines, facts = build_guidelines_and_facts(guidelines_data)
    fmt = next(g for g in guidelines if g.id == "NS-FMT-004")
    text = "\U0001f680\U0001f680"
    response = run_review_engine(text, [fmt], facts)
    predicted = convert_to_predicted(response, text, [fmt], facts, "emoji")
    assert len(predicted) == 1
    assert predicted[0].rule_id == "NS-FMT-004"
    assert (predicted[0].start, predicted[0].end) == (0, 2)
    assert predicted[0].matched_text == text


def test_required_phrase_missing_uses_trigger_sentence_span(dataset):
    _, _, guidelines_data = dataset
    guidelines, facts = build_guidelines_and_facts(guidelines_data)
    req = next(g for g in guidelines if g.id == "NS-REQ-001")
    text = "The Team plan costs $12 per team member per month, billed annually."
    response = run_review_engine(text, [req], facts)
    predicted = convert_to_predicted(response, text, [req], facts, "req")
    assert len(predicted) == 1
    assert predicted[0].start is not None and predicted[0].end is not None
    assert "$12 per team member per month" in text[predicted[0].start:predicted[0].end]


def test_no_finding_cases_do_not_create_false_negatives(report):
    by_input = {r["input_id"]: r for r in report["per_input_results"]}
    for input_id in ("draft:NS-DRAFT-10", "snippet:NS-SNIP-05", "snippet:NS-SNIP-06"):
        row = by_input[input_id]
        assert row["expected_count"] == 0
        assert row["fn"] == 0
    assert report["metrics"]["counts"]["total_expected"] == 38


def test_superseded_fact_cases_match(report):
    by_input = {r["input_id"]: r for r in report["per_input_results"]}
    matches = by_input["draft:NS-DRAFT-06"]["matches"]
    assert any(m["expected_rule"] == "NS-FACT-010" for m in matches)
    assert any(m["expected_rule"] == "NS-FACT-003" for m in matches)


def test_acceptable_alternative_outcome_requires_explicit_label():
    finding = PredictedFinding(
        test_case_id="NS-TC-037",
        finding_id="x",
        rule_id="NS-NAME-001",
        matched_text="North Star",
        start=0,
        end=10,
        category="product_name",
        severity="medium",
        explanation="",
        citation_rule_id="NS-NAME-001",
        citation_source_type="guideline",
        suggested_fix=None,
        confidence=0.9,
        requires_human_review=True,
        label="needs_human_judgement",
    )
    alternatives = [
        {"outcome": "needs_human_judgement", "rule_or_fact_id": "NS-NAME-001"}
    ]
    assert _is_acceptable_alternative(finding, alternatives)
    finding.label = None
    assert not _is_acceptable_alternative(finding, alternatives)
