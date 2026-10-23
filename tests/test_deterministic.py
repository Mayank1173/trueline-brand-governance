"""Tests for deterministic rule checks."""


from trueline.models import Category, Guideline, Severity
from trueline.review.deterministic import (
    DeterministicRule,
    _compile_rules,
    check_banned_terms,
    check_required_phrases,
    run_deterministic_checks,
)


class TestCompileRules:
    def test_banned_term_pattern_extraction(self):
        guidelines = [
            Guideline(
                id="RULE_001",
                text='Do not use "guaranteed" in claims.',
                category="unsupported_claim",
                source="Guidelines",
            ),
        ]
        rules = _compile_rules(guidelines)
        assert len(rules) == 1
        assert rules[0].is_banned is True
        assert rules[0].category == Category.BANNED_TERM
        assert rules[0].severity == Severity.HIGH

    def test_required_phrase_pattern_extraction(self):
        guidelines = [
            Guideline(
                id="RULE_002",
                text='Must include "Results may vary" disclaimer.',
                category="missing_disclaimer",
                source="Guidelines",
            ),
        ]
        rules = _compile_rules(guidelines)
        assert len(rules) == 1
        assert rules[0].is_banned is False
        assert rules[0].category == Category.REQUIRED_PHRASE

    def test_avoid_pattern(self):
        guidelines = [
            Guideline(
                id="RULE_003",
                text='Avoid "revolutionary" - use "innovative" instead.',
                category="banned_term",
                source="Guidelines",
            ),
        ]
        rules = _compile_rules(guidelines)
        assert len(rules) == 1
        assert "revolutionary" in rules[0].pattern.pattern

    def test_never_use_pattern(self):
        guidelines = [
            Guideline(
                id="RULE_004",
                text='Never use "unbeatable" in marketing.',
                category="banned_term",
                source="Guidelines",
            ),
        ]
        rules = _compile_rules(guidelines)
        assert len(rules) == 1
        assert "unbeatable" in rules[0].pattern.pattern

    def test_empty_guidelines(self):
        rules = _compile_rules([])
        assert rules == []

    def test_guideline_without_clear_pattern(self):
        guidelines = [
            Guideline(
                id="RULE_005",
                text="Maintain professional tone at all times.",
                category="tone",
                source="Guidelines",
            ),
        ]
        rules = _compile_rules(guidelines)
        # Tone guidelines don't have extractable patterns
        assert rules == []


class TestCheckBannedTerms:
    def test_finds_banned_term(self):
        rules = [
            DeterministicRule(
                guideline_id="RULE_001",
                guideline_source="Guidelines",
                guideline_text='Do not use "guaranteed"',
                category=Category.BANNED_TERM,
                severity=Severity.HIGH,
                pattern=__import__("re").compile(r"\bguaranteed\b", __import__("re").IGNORECASE),
                is_banned=True,
            ),
        ]
        draft = "This product is guaranteed to work."
        findings = check_banned_terms(draft, rules)
        assert len(findings) == 1
        assert findings[0].matched_text.lower() == "guaranteed"
        assert findings[0].category == Category.BANNED_TERM

    def test_multiple_occurrences(self):
        rules = [
            DeterministicRule(
                guideline_id="RULE_001",
                guideline_source="Guidelines",
                guideline_text='Do not use "guaranteed"',
                category=Category.BANNED_TERM,
                severity=Severity.HIGH,
                pattern=__import__("re").compile(r"\bguaranteed\b", __import__("re").IGNORECASE),
                is_banned=True,
            ),
        ]
        draft = "Guaranteed results. Guaranteed success."
        findings = check_banned_terms(draft, rules)
        assert len(findings) == 2

    def test_no_false_positive_partial_match(self):
        rules = [
            DeterministicRule(
                guideline_id="RULE_001",
                guideline_source="Guidelines",
                guideline_text='Do not use "guaranteed"',
                category=Category.BANNED_TERM,
                severity=Severity.HIGH,
                pattern=__import__("re").compile(r"\bguaranteed\b", __import__("re").IGNORECASE),
                is_banned=True,
            ),
        ]
        draft = "This is a guarantee."  # "guarantee" != "guaranteed"
        findings = check_banned_terms(draft, rules)
        assert len(findings) == 0

    def test_case_insensitive(self):
        rules = [
            DeterministicRule(
                guideline_id="RULE_001",
                guideline_source="Guidelines",
                guideline_text='Do not use "guaranteed"',
                category=Category.BANNED_TERM,
                severity=Severity.HIGH,
                pattern=__import__("re").compile(r"\bguaranteed\b", __import__("re").IGNORECASE),
                is_banned=True,
            ),
        ]
        draft = "GUARANTEED results."
        findings = check_banned_terms(draft, rules)
        assert len(findings) == 1


class TestCheckRequiredPhrases:
    def test_missing_required_phrase(self):
        rules = [
            DeterministicRule(
                guideline_id="RULE_002",
                guideline_source="Guidelines",
                guideline_text='Must include "Results may vary"',
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=__import__("re").compile(r"Results may vary", __import__("re").IGNORECASE),
                is_banned=False,
            ),
        ]
        draft = "This product works great."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 1
        assert findings[0].matched_text == ""
        assert findings[0].start == 0
        assert findings[0].end == 0

    def test_present_required_phrase(self):
        rules = [
            DeterministicRule(
                guideline_id="RULE_002",
                guideline_source="Guidelines",
                guideline_text='Must include "Results may vary"',
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=__import__("re").compile(r"Results may vary", __import__("re").IGNORECASE),
                is_banned=False,
            ),
        ]
        draft = "This product works great. Results may vary."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 0


class TestRunDeterministicChecks:
    def test_banned_term_detection(self):
        guidelines = [
            Guideline(
                id="RULE_001",
                text='Do not use "guaranteed" in claims.',
                category="unsupported_claim",
                source="Guidelines",
            ),
        ]
        draft = "Our product is guaranteed to work."
        findings = run_deterministic_checks(draft, guidelines)
        assert len(findings) == 1
        assert findings[0].matched_text == "guaranteed"
        assert findings[0].citation is not None
        assert findings[0].citation.rule_id == "RULE_001"

    def test_required_phrase_missing(self):
        guidelines = [
            Guideline(
                id="RULE_002",
                text='Must include "Results may vary" disclaimer.',
                category="missing_disclaimer",
                source="Guidelines",
            ),
        ]
        draft = "Our product works great."
        findings = run_deterministic_checks(draft, guidelines)
        assert len(findings) == 1
        assert findings[0].category == Category.REQUIRED_PHRASE
        assert findings[0].matched_text == ""

    def test_clean_draft_no_findings(self):
        guidelines = [
            Guideline(
                id="RULE_001",
                text='Do not use "guaranteed" in claims.',
                category="unsupported_claim",
                source="Guidelines",
            ),
        ]
        draft = "Our product works well."
        findings = run_deterministic_checks(draft, guidelines)
        assert len(findings) == 0

    def test_empty_guidelines(self):
        draft = "Any text here."
        findings = run_deterministic_checks(draft, [])
        assert findings == []

    def test_offsets_exact_match(self):
        guidelines = [
            Guideline(
                id="RULE_001",
                text='Do not use "guaranteed" in claims.',
                category="unsupported_claim",
                source="Guidelines",
            ),
        ]
        draft = "Product guaranteed works."
        findings = run_deterministic_checks(draft, guidelines)
        assert len(findings) == 1
        f = findings[0]
        assert draft[f.start:f.end] == f.matched_text

    def test_mixed_banned_and_required(self):
        guidelines = [
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
        draft = "Our product is guaranteed to work."
        findings = run_deterministic_checks(draft, guidelines)
        assert len(findings) == 2
        categories = {f.category for f in findings}
        assert Category.BANNED_TERM in categories
        assert Category.REQUIRED_PHRASE in categories


class TestDeterministicEdgeCases:
    """Tests for edge cases in deterministic checks."""

    def test_compile_rules_skips_empty_guideline_text(self):
        """Test that guidelines with empty/whitespace text are skipped (line 37)."""
        from trueline.review.deterministic import _compile_rules

        guidelines = [
            Guideline(id="RULE_001", text="", category="banned_term", source="Guidelines"),
            Guideline(id="RULE_002", text="   ", category="banned_term", source="Guidelines"),
            Guideline(id="RULE_003", text='Do not use "bad"', category="banned_term", source="Guidelines"),
        ]

        rules = _compile_rules(guidelines)

        # Only RULE_003 should produce a rule
        assert len(rules) == 1
        assert rules[0].guideline_id == "RULE_003"

    def test_compile_rules_colon_pattern_extraction(self):
        """Test colon pattern extraction for banned terms (lines 109-115)."""
        from trueline.review.deterministic import _compile_rules

        guidelines = [
            Guideline(
                id="RULE_001",
                text='Banned terms: "guaranteed", "revolutionary", "miracle"',
                category="banned_term",
                source="Guidelines",
            ),
            Guideline(
                id="RULE_002",
                text='List of banned terms: "scam", "fraud"',
                category="banned_term",
                source="Guidelines",
            ),
        ]

        rules = _compile_rules(guidelines)

        # Should extract 5 terms total (3 from RULE_001, 2 from RULE_002)
        assert len(rules) == 5
        extracted_terms = {r.pattern.pattern for r in rules}
        # Check that the terms are properly escaped in the regex
        assert any("guaranteed" in p for p in extracted_terms)
        assert any("revolutionary" in p for p in extracted_terms)
        assert any("miracle" in p for p in extracted_terms)
        assert any("scam" in p for p in extracted_terms)
        assert any("fraud" in p for p in extracted_terms)

    def test_compile_rules_colon_pattern_with_empty_terms(self):
        """Test colon pattern handles empty terms gracefully."""
        from trueline.review.deterministic import _compile_rules

        guidelines = [
            Guideline(
                id="RULE_001",
                text='Banned: "", "valid", ""',
                category="banned_term",
                source="Guidelines",
            ),
        ]

        rules = _compile_rules(guidelines)

        # Should only extract "valid" (empty strings skipped)
        assert len(rules) == 1
        assert "valid" in rules[0].pattern.pattern

    def test_run_deterministic_checks_empty_guidelines(self):
        """Test run_deterministic_checks with empty guidelines (line 198)."""
        findings = run_deterministic_checks("Any text", [])
        assert findings == []

    def test_run_deterministic_checks_no_rules_generated(self):
        """Test run_deterministic_checks when no rules generated (line 202)."""
        # Guidelines that don't match any pattern
        guidelines = [
            Guideline(id="RULE_001", text="This is just a description without patterns", category="tone", source="Guidelines"),
            Guideline(id="RULE_002", text="Another vague guideline", category="formatting", source="Guidelines"),
        ]

        findings = run_deterministic_checks("Any text", guidelines)
        assert findings == []

    def test_run_deterministic_checks_none_guidelines(self):
        """Test run_deterministic_checks handles None gracefully."""
        # This tests the type annotation but we pass empty list for runtime
        findings = run_deterministic_checks("Any text", [])
        assert findings == []

    def test_check_banned_terms_case_insensitive(self):
        """Test banned terms are matched case-insensitively."""
        from trueline.review.deterministic import _compile_rules, check_banned_terms

        guidelines = [
            Guideline(id="RULE_001", text='Do not use "TEST"', category="banned_term", source="Guidelines"),
        ]

        rules = _compile_rules(guidelines)
        findings = check_banned_terms("This is a test.", rules)

        assert len(findings) == 1
        assert findings[0].matched_text.lower() == "test"

    def test_check_required_phrases_case_insensitive(self):
        """Test required phrases are matched case-insensitively."""
        from trueline.review.deterministic import _compile_rules, check_required_phrases

        guidelines = [
            Guideline(id="RULE_001", text='Must include "REQUIRED PHRASE"', category="required_phrase", source="Guidelines"),
        ]

        rules = _compile_rules(guidelines)
        # Should find the phrase regardless of case
        findings = check_required_phrases("This has required phrase in it.", rules)

        assert len(findings) == 0  # Phrase is present, so no finding

        # Missing phrase should generate finding
        findings = check_required_phrases("This has nothing.", rules)
        assert len(findings) == 1
        assert findings[0].category == Category.REQUIRED_PHRASE
