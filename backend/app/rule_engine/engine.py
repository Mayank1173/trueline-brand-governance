"""Deterministic rule engine.

Contract:
* Same text + rules + facts + evaluation date -> same findings.
* ``start``/``end`` are zero-based, end-exclusive UTF-16 code-unit offsets.
  UTF-16 is used because the existing frontend slices strings with JavaScript,
  which counts string positions in UTF-16 code units.
* All occurrences of a term are reported.
* Different rules may overlap; overlapping findings from different rules are
  preserved because they represent different issues. Overlaps *within* one
  rule are resolved longest-match-first to keep output stable.
* No network calls and no AI model is involved.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone

from .models import CitationDraft, FactDefinition, FindingDraft, RuleDefinition

ENGINE_VERSION = "1.0.0"

FACT_EXPIRY_RULE_ID = "BR-FACT-EXPIRED-001"

_TERM_MATCH_TYPES = {
    "term",
    "preferred_term",
    "product_name",
    "unsupported_claim",
    "tone",
}


class RuleEngineError(Exception):
    """Base class for engine failures."""


class RuleConfigurationError(RuleEngineError):
    """A stored rule cannot be interpreted safely."""


class _OffsetMap:
    """Maps Python string indices to JavaScript-compatible UTF-16 offsets."""

    def __init__(self, text: str) -> None:
        prefix = [0]
        total = 0
        for char in text:
            total += 2 if ord(char) > 0xFFFF else 1
            prefix.append(total)
        self._prefix = prefix

    def at(self, index: int) -> int:
        return self._prefix[index]


class RuleEngine:
    def __init__(
        self, rules: list[RuleDefinition], facts: list[FactDefinition] | None = None
    ):
        self.rules = list(rules)
        self.facts = list(facts or [])

    def review(
        self,
        text: str,
        *,
        purpose: str = "general",
        evaluation_date: date | None = None,
    ) -> list[FindingDraft]:
        if text is None:
            raise RuleEngineError("text must be a string")
        if not isinstance(text, str):
            raise RuleEngineError("text must be a string")

        today = evaluation_date or datetime.now(timezone.utc).date()
        offset_map = _OffsetMap(text)
        findings: list[FindingDraft] = []
        normalized_purpose = (purpose or "general").strip().casefold()

        for rule in self.rules:
            if not self._applies_to_purpose(rule, normalized_purpose):
                continue
            findings.extend(self._evaluate_rule(rule, text, offset_map))

        findings.extend(self._evaluate_facts(text, offset_map, today))

        findings.sort(
            key=lambda item: (
                item.start is None,
                item.start if item.start is not None else 0,
                item.end if item.end is not None else 0,
                item.rule_id,
                item.matched_text,
            )
        )
        return findings

    @staticmethod
    def _applies_to_purpose(rule: RuleDefinition, purpose: str) -> bool:
        if not rule.applies_to_purposes:
            return True
        allowed = {value.strip().casefold() for value in rule.applies_to_purposes}
        return purpose in allowed

    def _evaluate_rule(
        self, rule: RuleDefinition, text: str, offset_map: _OffsetMap
    ) -> list[FindingDraft]:
        if rule.match_type in _TERM_MATCH_TYPES:
            return self._term_findings(rule, text, offset_map)
        if rule.match_type == "required_phrase":
            return self._required_phrase_findings(rule, text, offset_map)
        if rule.match_type == "regex":
            return self._regex_findings(rule, text, offset_map)
        if rule.match_type == "length_limit":
            return self._length_findings(rule, text)
        raise RuleConfigurationError(
            f"Rule {rule.rule_id} has unsupported match_type {rule.match_type!r}"
        )

    def _term_findings(
        self, rule: RuleDefinition, text: str, offset_map: _OffsetMap
    ) -> list[FindingDraft]:
        if not rule.patterns:
            raise RuleConfigurationError(
                f"Rule {rule.rule_id} has no patterns configured"
            )
        spans: list[tuple[int, int]] = []
        for term in rule.patterns:
            if not term:
                raise RuleConfigurationError(
                    f"Rule {rule.rule_id} contains an empty term"
                )
            spans.extend(
                self._find_term_spans(
                    text,
                    term,
                    case_sensitive=rule.case_sensitive,
                    word_boundary=rule.word_boundary,
                )
            )
        return [
            self._text_finding(rule, text, offset_map, start, end)
            for start, end in self._resolve_same_rule_overlaps(spans)
        ]

    def _required_phrase_findings(
        self, rule: RuleDefinition, text: str, offset_map: _OffsetMap
    ) -> list[FindingDraft]:
        if not rule.patterns:
            raise RuleConfigurationError(
                f"Rule {rule.rule_id} has no required phrase configured"
            )
        findings: list[FindingDraft] = []
        for phrase in rule.patterns:
            if not phrase:
                raise RuleConfigurationError(
                    f"Rule {rule.rule_id} contains an empty required phrase"
                )
            present = bool(
                self._find_term_spans(
                    text,
                    phrase,
                    case_sensitive=rule.case_sensitive,
                    word_boundary=rule.word_boundary,
                )
            )
            if present:
                continue

            summary = rule.explanation.rstrip()
            if not summary.endswith("."):
                summary += "."
            findings.append(
                FindingDraft(
                    rule_id=rule.rule_id,
                    matched_text="",
                    start=None,
                    end=None,
                    category=rule.category,
                    severity=rule.severity,
                    explanation=f"{summary} The required phrase {phrase!r} was not found.",
                    citation=rule.citation,
                    suggested_fix=rule.suggested_fix or phrase,
                    confidence=_clamp_confidence(rule.confidence),
                    requires_human_review=rule.requires_human_review,
                )
            )
        return findings

    def _regex_findings(
        self, rule: RuleDefinition, text: str, offset_map: _OffsetMap
    ) -> list[FindingDraft]:
        if not rule.patterns:
            raise RuleConfigurationError(
                f"Rule {rule.rule_id} has no regex patterns configured"
            )
        findings: list[FindingDraft] = []
        for pattern in rule.patterns:
            if not pattern:
                raise RuleConfigurationError(
                    f"Rule {rule.rule_id} contains an empty regex"
                )
            try:
                compiled = re.compile(pattern)
            except re.error as exc:
                raise RuleConfigurationError(
                    f"Rule {rule.rule_id} has an invalid regex: {exc}"
                ) from exc

            matches = list(compiled.finditer(text))
            spans = [(match.start(), match.end()) for match in matches]
            for start, end in self._resolve_same_rule_overlaps(spans):
                findings.append(self._text_finding(rule, text, offset_map, start, end))
        return findings

    def _length_findings(self, rule: RuleDefinition, text: str) -> list[FindingDraft]:
        max_chars = rule.max_chars
        if max_chars is None or max_chars <= 0:
            raise RuleConfigurationError(
                f"Rule {rule.rule_id} has no valid max_chars configured"
            )
        if len(text) <= max_chars:
            return []

        summary = rule.explanation.rstrip()
        if not summary.endswith("."):
            summary += "."
        return [
            FindingDraft(
                rule_id=rule.rule_id,
                matched_text="",
                start=None,
                end=None,
                category=rule.category,
                severity=rule.severity,
                explanation=(
                    f"{summary} The draft is {len(text)} characters long; "
                    f"the limit is {max_chars} characters."
                ),
                citation=rule.citation,
                suggested_fix=rule.suggested_fix,
                confidence=_clamp_confidence(rule.confidence),
                requires_human_review=rule.requires_human_review,
            )
        ]

    def _evaluate_facts(
        self, text: str, offset_map: _OffsetMap, today: date
    ) -> list[FindingDraft]:
        findings: list[FindingDraft] = []
        for fact in self.facts:
            if not fact.is_active or not fact.statement:
                continue
            if _fact_is_current(fact, today):
                continue

            spans = self._find_term_spans(
                text,
                fact.statement,
                case_sensitive=False,
                word_boundary=True,
            )
            for start, end in self._resolve_same_rule_overlaps(spans):
                validity = _validity_text(fact)
                findings.append(
                    FindingDraft(
                        rule_id=FACT_EXPIRY_RULE_ID,
                        matched_text=text[start:end],
                        start=offset_map.at(start),
                        end=offset_map.at(end),
                        category="fact_metadata",
                        severity="high",
                        explanation=(
                            f"The approved fact {fact.id!r} is not valid on "
                            f"{today.isoformat()} ({validity}). Remove or replace "
                            "this claim before publishing."
                        ),
                        citation=CitationDraft(
                            source_type="approved_fact",
                            source_id=fact.id,
                            source_version=fact.source_version,
                            source_label=fact.source_label,
                            quoted_text=fact.statement,
                            valid_until=fact.valid_until,
                        ),
                        suggested_fix=None,
                        confidence=1.0,
                        requires_human_review=True,
                    )
                )
        return findings

    def _text_finding(
        self,
        rule: RuleDefinition,
        text: str,
        offset_map: _OffsetMap,
        start: int,
        end: int,
    ) -> FindingDraft:
        return FindingDraft(
            rule_id=rule.rule_id,
            matched_text=text[start:end],
            start=offset_map.at(start),
            end=offset_map.at(end),
            category=rule.category,
            severity=rule.severity,
            explanation=rule.explanation,
            citation=rule.citation,
            suggested_fix=rule.suggested_fix,
            confidence=_clamp_confidence(rule.confidence),
            requires_human_review=rule.requires_human_review,
        )

    @staticmethod
    def _find_term_spans(
        text: str,
        term: str,
        *,
        case_sensitive: bool,
        word_boundary: bool,
    ) -> list[tuple[int, int]]:
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(term)
        if word_boundary:
            if term[0].isalnum() or term[0] == "_":
                pattern = rf"(?<!\w){pattern}"
            if term[-1].isalnum() or term[-1] == "_":
                pattern = rf"{pattern}(?!\w)"
        return [
            (match.start(), match.end()) for match in re.finditer(pattern, text, flags)
        ]

    @staticmethod
    def _resolve_same_rule_overlaps(
        spans: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        if not spans:
            return []
        ordered = sorted(set(spans), key=lambda span: (span[0], -(span[1] - span[0])))
        kept: list[tuple[int, int]] = []
        for start, end in ordered:
            if any(
                start < kept_end and end > kept_start for kept_start, kept_end in kept
            ):
                continue
            kept.append((start, end))
        return kept


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _fact_is_current(fact: FactDefinition, today: date) -> bool:
    return not (
        fact.superseded_by
        or (fact.valid_from and today < fact.valid_from)
        or (fact.valid_until and today > fact.valid_until)
    )


def _validity_text(fact: FactDefinition) -> str:
    parts: list[str] = []
    if fact.superseded_by:
        parts.append("superseded")
    if fact.valid_from:
        parts.append(f"valid from {fact.valid_from.isoformat()}")
    if fact.valid_until:
        parts.append(f"valid until {fact.valid_until.isoformat()}")
    return ", ".join(parts) if parts else "no validity window recorded"
