from __future__ import annotations

from datetime import date

import pytest

from app.rule_engine import (
    FactDefinition,
    RuleConfigurationError,
    RuleDefinition,
    RuleEngine,
)


def make_rule(**overrides) -> RuleDefinition:
    defaults = {
        "rule_id": "BR-TEST-001",
        "source_id": "GL-TEST-001",
        "source_version": "v1",
        "source_label": "Test Guidelines §1",
        "quoted_text": "Test rule source text.",
        "category": "banned_term",
        "severity": "medium",
        "match_type": "term",
        "explanation": "Test explanation.",
        "patterns": ("badword",),
        "suggested_fix": "goodword",
        "confidence": 1.0,
        "requires_human_review": False,
        "case_sensitive": False,
        "word_boundary": True,
    }
    defaults.update(overrides)
    return RuleDefinition(**defaults)


def test_term_rule_is_case_insensitive_and_reports_all_occurrences():
    text = "BadWord appears here; badword again."
    findings = RuleEngine([make_rule()]).review(text)
    assert [finding.matched_text for finding in findings] == ["BadWord", "badword"]
    assert [(finding.start, finding.end) for finding in findings] == [(0, 7), (22, 29)]
    for finding in findings:
        assert text[finding.start : finding.end] == finding.matched_text


def test_word_boundary_does_not_match_inside_another_word():
    findings = RuleEngine([make_rule()]).review("superbadword and badword")
    assert [finding.matched_text for finding in findings] == ["badword"]
    assert findings[0].start == 17


def test_case_sensitive_matching_is_supported():
    rule = make_rule(case_sensitive=True, patterns=("TrueLine",))
    findings = RuleEngine([rule]).review("TrueLine and Trueline and TRUELINE")
    assert [finding.matched_text for finding in findings] == ["TrueLine"]


def test_preferred_terminology_suggests_replacement():
    rule = make_rule(
        category="preferred_terminology",
        patterns=("users",),
        suggested_fix="customers",
    )
    finding = RuleEngine([rule]).review("Users are users.")[0]
    assert finding.category == "preferred_terminology"
    assert finding.suggested_fix == "customers"
    assert finding.matched_text == "Users"


def test_required_phrase_missing_has_empty_match_and_no_offsets():
    rule = make_rule(
        match_type="required_phrase",
        category="required_phrase",
        patterns=("Terms apply.",),
        suggested_fix="Terms apply.",
        word_boundary=False,
    )
    findings = RuleEngine([rule]).review("A promotional sentence.")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.matched_text == ""
    assert finding.start is None
    assert finding.end is None
    assert "Terms apply." in finding.explanation


def test_required_phrase_present_produces_no_finding():
    rule = make_rule(
        match_type="required_phrase",
        category="required_phrase",
        patterns=("Terms apply.",),
        word_boundary=False,
    )
    assert RuleEngine([rule]).review("Great offer. Terms apply.") == []


def test_regex_rule_reports_each_span():
    rule = make_rule(
        rule_id="BR-FMT-TEST",
        category="formatting",
        match_type="regex",
        patterns=("!{2,}",),
        suggested_fix="!",
        word_boundary=False,
    )
    findings = RuleEngine([rule]).review("Wow!!! Really!! Yes!")
    assert [finding.matched_text for finding in findings] == ["!!!", "!!"]


def test_term_rule_without_patterns_raises_configuration_error():
    rule = make_rule(patterns=())
    with pytest.raises(RuleConfigurationError):
        RuleEngine([rule]).review("text")


def test_regex_rule_without_patterns_raises_configuration_error():
    rule = make_rule(match_type="regex", patterns=())
    with pytest.raises(RuleConfigurationError):
        RuleEngine([rule]).review("text")


def test_invalid_regex_raises_configuration_error():
    rule = make_rule(match_type="regex", patterns=("([",))
    with pytest.raises(RuleConfigurationError):
        RuleEngine([rule]).review("text")


def test_length_limit_uses_character_count():
    rule = make_rule(
        rule_id="BR-LIMIT-TEST",
        category="length_limit",
        match_type="length_limit",
        patterns=(),
        max_chars=5,
        suggested_fix=None,
    )
    findings = RuleEngine([rule]).review("123456")
    assert len(findings) == 1
    assert findings[0].matched_text == ""
    assert findings[0].start is None
    assert "6 characters" in findings[0].explanation
    assert RuleEngine([rule]).review("12345") == []


def test_offsets_are_utf16_code_units_for_javascript_compatibility():
    text = "😀 users"
    rule = make_rule(patterns=("users",))
    finding = RuleEngine([rule]).review(text)[0]
    assert finding.matched_text == "users"
    assert finding.start == 3
    assert finding.end == 8


def test_same_rule_overlaps_are_resolved_longest_first():
    rule = make_rule(patterns=("bad", "badword"), word_boundary=False)
    findings = RuleEngine([rule]).review("badword")
    assert [finding.matched_text for finding in findings] == ["badword"]


def test_different_rules_may_overlap_and_are_both_reported():
    first = make_rule(rule_id="BR-ONE", patterns=("guaranteed",))
    second = make_rule(
        rule_id="BR-TWO", category="unsupported_claim", patterns=("guaranteed",)
    )
    findings = RuleEngine([first, second]).review("guaranteed")
    assert {finding.rule_id for finding in findings} == {"BR-ONE", "BR-TWO"}


def test_purpose_scoping_skips_non_matching_rules():
    rule = make_rule(
        match_type="required_phrase",
        patterns=("Terms apply.",),
        applies_to_purposes=("marketing",),
        word_boundary=False,
    )
    engine = RuleEngine([rule])
    assert len(engine.review("No disclaimer", purpose="marketing")) == 1
    assert engine.review("No disclaimer", purpose="email") == []


def test_expired_fact_is_flagged_with_fact_citation():
    fact = FactDefinition(
        id="FACT-TEST-1",
        statement="Free returns within 30 days.",
        source_label="Test fact library",
        source_version="v1",
        valid_until=date(2020, 1, 1),
    )
    findings = RuleEngine([], [fact]).review(
        "Offer: Free returns within 30 days.", evaluation_date=date(2026, 10, 23)
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "fact_metadata"
    assert finding.citation is not None
    assert finding.citation.source_type == "approved_fact"
    assert finding.citation.source_id == "FACT-TEST-1"
    assert finding.requires_human_review is True


def test_current_fact_is_not_flagged():
    fact = FactDefinition(
        id="FACT-TEST-2",
        statement="Battery lasts up to 10 hours.",
        source_label="Test fact library",
        source_version="v1",
    )
    assert (
        RuleEngine([], [fact]).review(
            "Battery lasts up to 10 hours.", evaluation_date=date(2026, 10, 23)
        )
        == []
    )


def test_engine_is_repeatable_and_deterministically_ordered():
    rules = [
        make_rule(rule_id="BR-B", patterns=("badword",)),
        make_rule(rule_id="BR-A", patterns=("badword",)),
    ]
    engine = RuleEngine(rules)
    first = engine.review("badword")
    second = engine.review("badword")
    assert first == second
    assert [finding.rule_id for finding in first] == ["BR-A", "BR-B"]


def test_empty_text_does_not_crash():
    rule = make_rule(
        match_type="required_phrase",
        patterns=("Terms apply.",),
        word_boundary=False,
    )
    findings = RuleEngine([rule]).review("")
    assert len(findings) == 1
    assert findings[0].matched_text == ""


def test_empty_rule_set_returns_no_findings():
    assert RuleEngine([]).review("anything") == []
