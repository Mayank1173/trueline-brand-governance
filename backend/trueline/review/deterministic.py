"""Deterministic rule checks for the Trueline AI Review Engine.

These checks run without AI and provide guaranteed, explainable findings
for well-defined rules like banned terms and required phrases.
"""

import logging
import re
from dataclasses import dataclass

from trueline.models import Category, Citation, Finding, Guideline, Severity

logger = logging.getLogger(__name__)


@dataclass
class DeterministicRule:
    """A deterministic rule that can be checked without AI."""
    guideline_id: str
    guideline_source: str
    guideline_text: str
    category: Category
    severity: Severity
    pattern: re.Pattern[str]
    is_banned: bool = True  # True = banned term, False = required phrase
    suggested_fix: str | None = None
    requires_human_review: bool = False


def _compile_rules(guidelines: list[Guideline]) -> list[DeterministicRule]:
    """Compile guidelines into deterministic rules."""
    rules = []

    for g in guidelines:
        # Skip guidelines without clear patterns
        if not g.text or not g.text.strip():
            continue

        text = g.text.strip()

        # Detect banned term patterns: "Do not use X", "Avoid X", "Never use X"
        banned_patterns = [
            r"do not use\s+[\"']([^\"']+)[\"']",
            r"avoid\s+[\"']([^\"']+)[\"']",
            r"never use\s+[\"']([^\"']+)[\"']",
            r"banned[:\s]+[\"']([^\"']+)[\"']",
            r"prohibited[:\s]+[\"']([^\"']+)[\"']",
            r"must not use\s+[\"']([^\"']+)[\"']",
        ]

        # Detect required phrase patterns: "Must include X", "Required: X", "Always use X"
        required_patterns = [
            r"must include\s+[\"']([^\"']+)[\"']",
            r"required[:\s]+[\"']([^\"']+)[\"']",
            r"always use\s+[\"']([^\"']+)[\"']",
            r"must contain\s+[\"']([^\"']+)[\"']",
        ]

        matched = False

        # Check banned term patterns
        for pattern in banned_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                term = match.group(1)
                # Escape for regex and match word boundaries
                regex = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                rules.append(DeterministicRule(
                    guideline_id=g.id,
                    guideline_source=g.source,
                    guideline_text=g.text,
                    category=Category.BANNED_TERM,
                    severity=Severity.HIGH,
                    pattern=regex,
                    is_banned=True,
                    suggested_fix=f"Remove or replace '{term}'",
                    requires_human_review=True,
                ))
                matched = True
                break

        # Check required phrase patterns
        if not matched:
            for pattern in required_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    phrase = match.group(1)
                    # For required phrases, we check if they're missing
                    # This is a negative check - we'll handle in the checker
                    rules.append(DeterministicRule(
                        guideline_id=g.id,
                        guideline_source=g.source,
                        guideline_text=g.text,
                        category=Category.REQUIRED_PHRASE,
                        severity=Severity.MEDIUM,
                        pattern=re.compile(rf"{re.escape(phrase)}", re.IGNORECASE),
                        is_banned=False,
                        suggested_fix=f"Include required phrase: '{phrase}'",
                        requires_human_review=True,
                    ))
                    matched = True
                    break

        # If no pattern matched but guideline has clear keywords, create a simple check
        if not matched and len(text) < 200:
            # Check for explicit term lists like "banned terms: X, Y, Z"
            if "banned" in text.lower() or "prohibited" in text.lower():
                # Try to extract terms after colon
                colon_match = re.search(r":\s*(.+)$", text)
                if colon_match:
                    terms = [t.strip().strip("\"'") for t in colon_match.group(1).split(",")]
                    for term in terms:
                        if term:
                            regex = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                            rules.append(DeterministicRule(
                                guideline_id=g.id,
                                guideline_source=g.source,
                                guideline_text=g.text,
                                category=Category.BANNED_TERM,
                                severity=Severity.HIGH,
                                pattern=regex,
                                is_banned=True,
                                suggested_fix=f"Remove or replace '{term}'",
                                requires_human_review=True,
                            ))

    return rules


def check_banned_terms(draft_text: str, rules: list[DeterministicRule]) -> list[Finding]:
    """Check for banned terms in draft text."""
    findings = []

    for rule in rules:
        if not rule.is_banned:
            continue

        for match in rule.pattern.finditer(draft_text):
            finding = Finding(
                id=f"det-{rule.guideline_id}-{match.start()}",
                matched_text=match.group(0),
                start=match.start(),
                end=match.end(),
                category=rule.category,
                severity=rule.severity,
                explanation=(
                f"Text contains banned term per guideline {rule.guideline_id}: "
                f"{rule.guideline_text}"
            ),
                citation=Citation(
                    rule_id=rule.guideline_id,
                    source=rule.guideline_source,
                    excerpt=rule.guideline_text[:200],
                ),
                suggested_fix=rule.suggested_fix,
                confidence=0.95,
                requires_human_review=rule.requires_human_review,
            )
            findings.append(finding)

    return findings


def check_required_phrases(draft_text: str, rules: list[DeterministicRule]) -> list[Finding]:
    """Check for missing required phrases in draft text."""
    findings = []

    for rule in rules:
        if rule.is_banned:
            continue

        # For required phrases, check if NOT present
        if not rule.pattern.search(draft_text):
            # Create a finding for the missing phrase
            # Use position 0 with empty matched_text to indicate missing content
            finding = Finding(
                id=f"det-{rule.guideline_id}-missing",
                matched_text="",  # Empty for missing content
                start=0,
                end=0,
                category=rule.category,
                severity=rule.severity,
                explanation=(
                f"Required phrase missing per guideline {rule.guideline_id}: "
                f"{rule.guideline_text}"
            ),
                citation=Citation(
                    rule_id=rule.guideline_id,
                    source=rule.guideline_source,
                    excerpt=rule.guideline_text[:200],
                ),
                suggested_fix=rule.suggested_fix,
                confidence=0.9,
                requires_human_review=rule.requires_human_review,
            )
            findings.append(finding)

    return findings


def run_deterministic_checks(draft_text: str, guidelines: list[Guideline]) -> list[Finding]:
    """Run all deterministic checks on the draft text."""
    if not guidelines:
        return []

    rules = _compile_rules(guidelines)
    if not rules:
        return []

    findings = []
    findings.extend(check_banned_terms(draft_text, rules))
    findings.extend(check_required_phrases(draft_text, rules))

    logger.info(f"Deterministic checks found {len(findings)} issues")
    return findings
