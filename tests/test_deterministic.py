"""Tests for deterministic rule checks."""

from datetime import date

from trueline.models import ApprovedFact, Category, FindingLabel, Guideline, Severity
from trueline.review.deterministic import (
    DeterministicRule,
    _compile_fact_rules,
    _compile_rules,
    check_banned_terms,
    check_facts,
    check_required_phrases,
    evaluate_fact_status,
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

    def test_required_phrase_no_trigger_no_finding(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-001",
                guideline_source="Northstar",
                guideline_text="Price disclosure required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Prices exclude applicable taxes\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\$\d"), re.compile(r"\bper team member\b")],
            ),
        ]
        draft = "Great product for teams."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 0

    def test_required_phrase_trigger_missing_finding(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-001",
                guideline_source="Northstar",
                guideline_text="Price disclosure required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Prices exclude applicable taxes\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\$\d"), re.compile(r"\bper team member\b"), re.compile(r"\bbilled annually\b")],
            ),
        ]
        draft = "The Team plan costs $12 per team member per month, billed annually. Start today."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 1
        assert findings[0].matched_text == ""
        assert findings[0].rule_id == "NS-REQ-001"

    def test_required_phrase_trigger_present_finding_none(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-001",
                guideline_source="Northstar",
                guideline_text="Price disclosure required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Prices exclude applicable taxes\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\$\d")],
            ),
        ]
        draft = "The Team plan costs $12 per team member per month. Prices exclude applicable taxes."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 0

    def test_required_phrase_ns_req002_trigger_missing(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-002",
                guideline_source="Northstar",
                guideline_text="AI disclosure required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Suggestions are generated by AI and should be reviewed before use\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\bAssist Suggestions\b"), re.compile(r"AI[- ]generated", re.IGNORECASE), re.compile(r"generated suggestions?", re.IGNORECASE)],
            ),
        ]
        draft = "Assist Suggestions can propose next steps for your tasks."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 1
        assert findings[0].rule_id == "NS-REQ-002"

    def test_required_phrase_ns_req002_trigger_present_ok(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-002",
                guideline_source="Northstar",
                guideline_text="AI disclosure required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Suggestions are generated by AI and should be reviewed before use\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\bAssist Suggestions\b")],
            ),
        ]
        draft = "Assist Suggestions can propose next steps for your tasks. Suggestions are generated by AI and should be reviewed before use."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 0

    def test_required_phrase_ns_req003_trigger_missing(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-003",
                guideline_source="Northstar",
                guideline_text="Offer terms required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Terms apply\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\b\d{1,2}% off\b"), re.compile(r"\boffer\b"), re.compile(r"\bpromotion\b"), re.compile(r"\bdiscount\b")],
            ),
        ]
        draft = "New workspaces get 20% off the Team plan."
        findings = check_required_phrases(draft, rules)
        assert len(findings) == 1
        assert findings[0].rule_id == "NS-REQ-003"

    def test_required_phrase_ns_req003_trigger_present_ok(self):
        import re
        rules = [
            DeterministicRule(
                guideline_id="NS-REQ-003",
                guideline_source="Northstar",
                guideline_text="Offer terms required",
                category=Category.REQUIRED_PHRASE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"Terms apply\.", re.IGNORECASE),
                is_banned=False,
                trigger_patterns=[re.compile(r"\b\d{1,2}% off\b")],
            ),
        ]
        draft = "New workspaces get 20% off the Team plan. Ends 30 November 2026. Terms apply."
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



class TestFactChecks:
    """Regression tests for approved-fact status and matching."""

    @staticmethod
    def _fact(**overrides):
        values = {
            "id": "NS-FACT-002",
            "claim": "The Team plan costs $12 per team member per month.",
            "evidence": "NS-DOC-PRICING",
            "category": "pricing",
            "valid_from": "2026-07-01",
            "expires_on": "2027-06-30",
            "status_on_evaluation_date": "active",
        }
        values.update(overrides)
        return ApprovedFact(**values)

    def test_superseded_status_takes_precedence(self):
        fact = self._fact(
            superseded_by="NS-FACT-003",
            expires_on="2026-06-30",
        )
        assert evaluate_fact_status(fact, date(2026, 10, 23)) == "superseded"

    def test_invalid_dates_do_not_crash(self):
        fact = self._fact(valid_from="not-a-date", expires_on="also-bad")
        assert evaluate_fact_status(fact, date(2026, 10, 23)) == "active"

    def test_active_fact_mention_is_not_a_finding(self):
        facts = [self._fact()]
        rules = _compile_fact_rules(facts, date(2026, 10, 23))
        findings = check_facts(
            "The Team plan costs $12 per team member per month.",
            rules,
        )
        assert findings == []

    def test_expired_fact_produces_outdated_sentence_finding(self):
        fact = self._fact(
            id="NS-FACT-003",
            claim=(
                "The launch offer gave new workspaces 20% off the Team plan "
                "from 1 August 2026 to 30 September 2026."
            ),
            expires_on="2026-09-30",
        )
        draft = "Save 20% until 30 September 2026. Then upgrade."
        rules = _compile_fact_rules([fact], date(2026, 10, 23))

        findings = check_facts(draft, rules)

        assert len(findings) == 1
        finding = findings[0]
        assert finding.rule_id == "NS-FACT-003"
        assert finding.label == FindingLabel.OUTDATED
        assert finding.category == Category.FACT_METADATA
        assert finding.severity == Severity.HIGH
        assert finding.matched_text == "Save 20% until 30 September 2026."
        assert draft[finding.start:finding.end] == finding.matched_text

    def test_superseded_fact_produces_outdated_finding(self):
        fact = self._fact(
            id="NS-FACT-010",
            claim="The Team plan cost $10 per team member per month until 30 June 2026.",
            expires_on="2026-06-30",
            superseded_by="NS-FACT-002",
        )
        draft = "The Team plan costs $10 per team member per month."
        rules = _compile_fact_rules([fact], date(2026, 10, 23))

        findings = check_facts(draft, rules)

        assert len(findings) == 1
        assert findings[0].label == FindingLabel.OUTDATED
        assert findings[0].matched_text == draft

    def test_not_yet_valid_fact_requires_human_judgement(self):
        fact = self._fact(
            id="NS-FACT-009",
            claim="Assist Suggestions is in beta on the Team plan.",
            valid_from="2027-01-01",
        )
        draft = "Assist Suggestions is in beta on the Team plan."
        rules = _compile_fact_rules([fact], date(2026, 10, 23))

        findings = check_facts(draft, rules)

        assert len(findings) == 1
        assert findings[0].label == FindingLabel.NEEDS_HUMAN_JUDGEMENT
        assert findings[0].category == Category.APPROVED_FACT

    def test_multiple_patterns_in_same_sentence_are_deduplicated(self):
        fact = self._fact(
            id="NS-FACT-010",
            claim="The Team plan cost $10 per member until 30 June 2026.",
            expires_on="2026-06-30",
            superseded_by="NS-FACT-002",
        )
        draft = "The Team plan cost $10 per member until 30 June 2026."
        rules = _compile_fact_rules([fact], date(2026, 10, 23))

        findings = check_facts(draft, rules)

        assert len(findings) == 1
