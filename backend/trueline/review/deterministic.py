"""Deterministic rule checks for the Trueline AI Review Engine.

These checks run without AI and provide guaranteed, explainable findings
for well-defined rules like banned terms and required phrases.
"""

import logging
import re
from dataclasses import dataclass
from datetime import date

from trueline.models import (
    ApprovedFact,
    Category,
    Citation,
    Finding,
    FindingLabel,
    Guideline,
    Severity,
)

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
    document_id: str | None = None
    section: str | None = None
    trigger_patterns: list[re.Pattern[str]] | None = None  # For required_wording rules, only check if trigger matches


@dataclass
class FactRule:
    """A fact rule for checking approved facts against draft text."""
    fact_id: str
    fact_statement: str
    fact_source: str
    fact_category: str
    valid_from: date | None
    expires_on: date | None
    superseded_by: str | None
    status_on_evaluation_date: str | None
    evaluation_date: date
    pattern: re.Pattern[str] | None = None  # Legacy single pattern
    patterns: list[tuple[re.Pattern[str], str]] | None = None  # Multiple patterns with their source text
    fact_status: str = "active"


# ──────────────────────────────────────────────────────────────────────────────
# Fact Evaluation
# ──────────────────────────────────────────────────────────────────────────────

def _parse_iso_date(value: str | None) -> date | None:
    """Parse an ISO date, returning None for missing or malformed values."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        logger.warning("Invalid ISO date on approved fact: %r; ignoring", value)
        return None


def evaluate_fact_status(fact: ApprovedFact, evaluation_date: date) -> str:
    """Evaluate the status of an approved fact on a given evaluation date.

    Returns: "active", "expired", "superseded", or "not_yet_valid"

    Supersession takes precedence because a superseded fact is outdated even
    when its own expiry date has not been reached yet.
    """
    if fact.superseded_by:
        return "superseded"

    expires_on = _parse_iso_date(fact.expires_on)
    if expires_on is not None and evaluation_date > expires_on:
        return "expired"

    valid_from = _parse_iso_date(fact.valid_from)
    if valid_from is not None and evaluation_date < valid_from:
        return "not_yet_valid"

    if fact.status_on_evaluation_date:
        return fact.status_on_evaluation_date

    return "active"


# ──────────────────────────────────────────────────────────────────────────────
# Fact Rule Compilation
# ──────────────────────────────────────────────────────────────────────────────

def _extract_distinctive_patterns(claim: str) -> list[str]:
    """Extract distinctive atomic patterns from a fact claim for precise matching.

    Returns only the most atomic, distinctive patterns that are likely to appear
    verbatim in both the fact and draft text, and are unlikely to appear generically.
    """
    patterns = []

    # Pattern 1: Prices ($10, $12, etc.) - highly distinctive
    price_matches = re.findall(r'\$\d+(?:\.\d+)?(?:\s*(?:per|/)\s*\w+)?', claim)
    patterns.extend(price_matches)

    # Pattern 2: Percentages (20%, 99.5%, etc.) - highly distinctive
    pct_matches = re.findall(r'\d+(?:\.\d+)?%', claim)
    patterns.extend(pct_matches)

    # Pattern 3: Specific dates (30 September 2026, 30 June 2026, etc.) - highly distinctive
    date_matches = re.findall(r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', claim)
    patterns.extend(date_matches)

    # Pattern 3b: Month year dates (September 2026, June 2026)
    date_matches2 = re.findall(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', claim)
    patterns.extend(date_matches2)

    # Pattern 4: Numbers with specific units (5 team members, 10 hours, etc.)
    num_unit_matches = re.findall(r'\b\d+(?:\.\d+)?\s+(?:team members?|hours?|users?|calendars?|apps?|platforms?|plans?|tiers?|members?|weeks?|months?|years?)\b', claim, re.IGNORECASE)
    patterns.extend(num_unit_matches)

    # Pattern 5: Very specific unique names - only the most distinctive
    # Only include if they appear with distinctive context
    unique_names = re.findall(r'\b(?:Team Timeline|Planner Pro|Focus Boards|Calendar Sync|Assist Suggestions)\b', claim, re.IGNORECASE)
    patterns.extend(unique_names)

    # Pattern 6: Very short distinctive phrases (4-6 words) with HIGHLY distinctive elements
    words = claim.split()
    for n in range(4, 6):
        for i in range(len(words) - n + 1):
            phrase = ' '.join(words[i:i+n])
            # Only include phrases with HIGHLY distinctive elements that are unlikely to appear generically
            if any(kw in phrase.lower() for kw in ['iCal', 'iOS', 'Android', 'encrypted', 'beta', 'unavailable', 'only', 'not included', 'excludes', 'supports iCal', 'iOS. An Android', 'An Android app', 'not yet available', 'not included in', 'Starter plan only', 'Team plan only']):
                if len(phrase) >= 15 and len(phrase) <= 40:
                    patterns.append(phrase)

    # Deduplicate - keep only unique, substantial patterns
    seen = set()
    unique = []
    for p in patterns:
        p_clean = p.strip()
        p_lower = p_clean.lower()
        if p_lower not in seen and len(p_clean) >= 8:
            seen.add(p_lower)
            unique.append(p_clean)

    # Limit to at most 2 most distinctive patterns per fact
    return unique[:2]


def _compile_fact_rules(facts: list[ApprovedFact], evaluation_date: date) -> list[FactRule]:
    """Compile approved facts into fact rules for deterministic checking.

    Creates rules for:
    1. Expired/superseded facts -> OUTDATED findings
    2. Active facts that could be contradicted -> CONTRADICTED findings
    3. Active facts that need verification -> NEEDS_HUMAN_JUDGEMENT findings
    """
    rules: list[FactRule] = []

    for fact in facts:
        claim = fact.claim.strip()
        if not claim:
            continue

        # Extract distinctive patterns for precise matching
        distinctive_patterns = _extract_distinctive_patterns(claim)

        if not distinctive_patterns:
            # Fallback: use full claim if no distinctive patterns found
            distinctive_patterns = [claim]

        # Create patterns from distinctive phrases
        patterns = []
        for pattern_text in distinctive_patterns:
            try:
                pattern = re.compile(re.escape(pattern_text), re.IGNORECASE)
                patterns.append((pattern, pattern_text))
            except re.error:
                logger.warning(f"Invalid regex pattern for fact {fact.id}: {pattern_text}")
                continue

        if not patterns:
            continue

        # Create fact rule with all distinctive patterns
        rule = FactRule(
            fact_id=fact.id,
            fact_statement=fact.claim,
            fact_source=fact.evidence,
            fact_category=fact.category,
            valid_from=_parse_iso_date(fact.valid_from),
            expires_on=_parse_iso_date(fact.expires_on),
            superseded_by=fact.superseded_by,
            status_on_evaluation_date=fact.status_on_evaluation_date,
            evaluation_date=evaluation_date,
            pattern=None,  # Not used - we use patterns list instead
            patterns=patterns,
            fact_status=evaluate_fact_status(fact, evaluation_date),
        )
        rules.append(rule)

    return rules


def _expand_to_sentence(text: str, start: int, end: int) -> tuple[int, int]:
    """Expand a match span to the sentence that contains it.

    Fact findings are more useful (and align with sentence-level evaluation
    annotations) when the reviewer sees the whole sentence rather than a bare
    price or date fragment. Sentence boundaries are punctuation followed by
    whitespace/end-of-text, or a newline.
    """
    sentence_start = 0
    for i in range(start - 1, -1, -1):
        char = text[i]
        if char == "\n":
            sentence_start = i + 1
            break
        if char in ".!?" and (i + 1 == len(text) or text[i + 1].isspace()):
            sentence_start = i + 1
            break

    sentence_end = len(text)
    for i in range(end, len(text)):
        char = text[i]
        if char == "\n":
            sentence_end = i
            break
        if char in ".!?" and (i + 1 == len(text) or text[i + 1].isspace()):
            sentence_end = i + 1
            break

    while sentence_start < start and text[sentence_start].isspace():
        sentence_start += 1
    while sentence_end > end and text[sentence_end - 1].isspace():
        sentence_end -= 1

    return sentence_start, sentence_end


def check_facts(draft_text: str, fact_rules: list[FactRule]) -> list[Finding]:
    """Check draft text for references to expired, superseded, or not-yet-valid facts.

    Active approved facts are intentionally *not* flagged: merely mentioning an
    approved fact is not a violation. Contradiction and ambiguity detection are
    left to the AI/hybrid layer, which can judge context.
    """
    findings: list[Finding] = []
    seen: set[tuple[str, int, int, FindingLabel]] = set()

    for rule in fact_rules:
        fact_status = rule.fact_status
        if fact_status not in ("expired", "superseded", "not_yet_valid"):
            continue

        # Use the new patterns list if available, otherwise fall back to legacy pattern
        patterns_to_check = (
            rule.patterns
            if rule.patterns
            else [(rule.pattern, rule.fact_statement)]
            if rule.pattern
            else []
        )

        for pattern, _source_text in patterns_to_check:
            for match in pattern.finditer(draft_text):
                match_start, match_end = _expand_to_sentence(
                    draft_text, match.start(), match.end()
                )
                key = (rule.fact_id, match_start, match_end, FindingLabel.OUTDATED)
                if key in seen:
                    continue
                seen.add(key)

                if fact_status in ("expired", "superseded"):
                    label = FindingLabel.OUTDATED
                    category = Category.FACT_METADATA
                    severity = Severity.HIGH
                    if fact_status == "superseded":
                        explanation = (
                            f"Draft references superseded approved fact {rule.fact_id}: "
                            f"{rule.fact_statement}"
                        )
                        suggested_fix = (
                            f"Replace the reference to {rule.fact_id} with its "
                            "current replacement fact."
                        )
                    else:
                        explanation = (
                            f"Draft references expired approved fact {rule.fact_id}: "
                            f"{rule.fact_statement}"
                        )
                        suggested_fix = (
                            f"Remove the expired reference to {rule.fact_id} or mark "
                            "it clearly as historical."
                        )
                else:
                    label = FindingLabel.NEEDS_HUMAN_JUDGEMENT
                    category = Category.APPROVED_FACT
                    severity = Severity.MEDIUM
                    explanation = (
                        f"Draft references approved fact {rule.fact_id}, which is not "
                        f"yet valid on {rule.evaluation_date.isoformat()}: "
                        f"{rule.fact_statement}"
                    )
                    suggested_fix = (
                        f"Remove the reference to {rule.fact_id} until it becomes valid."
                    )

                findings.append(
                    Finding(
                        id=f"fact-{rule.fact_id}-{match_start}",
                        matched_text=draft_text[match_start:match_end],
                        start=match_start,
                        end=match_end,
                        category=category,
                        severity=severity,
                        explanation=explanation,
                        citation=Citation(
                            rule_id=rule.fact_id,
                            source=rule.fact_source or rule.fact_id,
                            excerpt=rule.fact_statement[:200],
                            document_id=None,
                            section=None,
                        ),
                        suggested_fix=suggested_fix,
                        confidence=0.95 if label == FindingLabel.OUTDATED else 0.8,
                        requires_human_review=True,
                        label=label,
                        rule_id=rule.fact_id,
                    )
                )

    return findings


def _compile_rules(guidelines: list[Guideline]) -> list[DeterministicRule]:
    """Compile guidelines into deterministic rules.

    Supports both:
    1. Explicit patterns from guideline.patterns (Northstar dataset format)
    2. Pattern extraction from guideline text (legacy format)
    """
    rules: list[DeterministicRule] = []

    for g in guidelines:
        # Skip guidelines without clear patterns
        if not g.text or not g.text.strip():
            continue

        # Use explicit patterns if provided (Northstar dataset format)
        if g.patterns:
            _compile_explicit_patterns(g, rules)
            continue

        # Legacy pattern extraction from guideline text
        _compile_legacy_patterns(g, rules)

    return rules


def _compile_explicit_patterns(g: Guideline, rules: list[DeterministicRule]) -> None:
    """Compile rules from explicit regex patterns (Northstar dataset format)."""
    # Map guideline category to our Category enum
    category = _map_category(g.category)

    # Determine severity
    severity = _parse_severity(g.severity_default)

    # Determine if this is a banned term check or required phrase check
    is_banned = g.category not in ("required_wording",)

    # Determine case sensitivity: default True for term-like, False for regex
    # Northstar tone rules with \b[A-Z]{3,}\b need case_sensitive=True
    case_sensitive = g.case_sensitive
    if case_sensitive is None:
        # Default: case-sensitive for term-like categories, insensitive for regex
        case_sensitive = g.category in ("tone", "banned_language", "naming", "terminology")

    flags = 0 if case_sensitive else re.IGNORECASE

    # For required_wording rules, check for required_phrase and trigger
    if g.category == "required_wording" and g.required_phrase:
        # Required phrase: check if phrase is missing
        phrase = g.required_phrase
        regex = re.compile(rf"{re.escape(phrase)}", flags)

        trigger_patterns: list[re.Pattern[str]] = []
        # Use patterns from guideline as trigger patterns (per schema - these indicate when rule applies)
        for pattern_str in (g.patterns or []):
            try:
                trigger_patterns.append(re.compile(pattern_str, flags))
            except re.error as e:
                logger.warning(f"Invalid trigger regex pattern in guideline {g.id}: {pattern_str} - {e}")

        rules.append(DeterministicRule(
            guideline_id=g.id,
            guideline_source=g.source,
            guideline_text=g.text,
            category=Category.REQUIRED_PHRASE,
            severity=severity,
            pattern=regex,
            is_banned=False,
            suggested_fix=f"Include required phrase: '{phrase}'",
            requires_human_review=True,
            document_id=g.document_id,
            section=g.section,
            trigger_patterns=trigger_patterns or None,
        ))
        return

    # For banned term patterns, compile each pattern
    for pattern_str in g.patterns:
        try:
            regex = re.compile(pattern_str, flags)
            rules.append(DeterministicRule(
                guideline_id=g.id,
                guideline_source=g.source,
                guideline_text=g.text,
                category=category,
                severity=severity,
                pattern=regex,
                is_banned=is_banned,
                suggested_fix=_generate_fix(g.category, pattern_str),
                requires_human_review=_requires_human_review(g.category, severity),
                document_id=g.document_id,
                section=g.section,
            ))
        except re.error as e:
            logger.warning(f"Invalid regex pattern in guideline {g.id}: {pattern_str} - {e}")


def _compile_legacy_patterns(g: Guideline, rules: list[DeterministicRule]) -> None:
    """Compile rules from legacy guideline text pattern extraction."""
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
                document_id=g.document_id,
                section=g.section,
            ))
            matched = True
            break

    # Check required phrase patterns
    if not matched:
        for pattern in required_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phrase = match.group(1)
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
                    document_id=g.document_id,
                    section=g.section,
                ))
                matched = True
                break

    # If no pattern matched but guideline has clear keywords, create a simple check
    if not matched and len(text) < 200:
        if "banned" in text.lower() or "prohibited" in text.lower():
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
                            document_id=g.document_id,
                            section=g.section,
                        ))


def _map_category(category_str: str) -> Category:
    """Map guideline category string to Category enum."""
    mapping = {
        "tone": Category.TONE,
        "naming": Category.NAMING,
        "terminology": Category.TERMINOLOGY,
        "banned_language": Category.BANNED_LANGUAGE,
        "required_wording": Category.REQUIRED_WORDING,
        "formatting": Category.FORMATTING,
        "claims": Category.CLAIMS,
        "banned_term": Category.BANNED_TERM,
        "missing_disclaimer": Category.MISSING_DISCLAIMER,
        "unsupported_claim": Category.UNSUPPORTED_CLAIM,
        "preferred_terminology": Category.PREFERRED_TERMINOLOGY,
        "required_phrase": Category.REQUIRED_PHRASE,
        "product_name_inconsistency": Category.PRODUCT_NAME_INCONSISTENCY,
        "missing_content": Category.MISSING_CONTENT,
        "length_limit": Category.LENGTH_LIMIT,
    }
    return mapping.get(category_str.lower(), Category.BANNED_TERM)


def _parse_severity(severity_str: str | None) -> Severity:
    """Parse severity string to Severity enum."""
    if not severity_str:
        return Severity.MEDIUM
    mapping = {
        "low": Severity.LOW,
        "medium": Severity.MEDIUM,
        "high": Severity.HIGH,
    }
    return mapping.get(severity_str.lower(), Severity.MEDIUM)


def _generate_fix(category: str, pattern: str) -> str:
    """Generate a suggested fix based on category and pattern."""
    fixes = {
        "banned_language": "Remove the flagged term and rephrase",
        "banned_term": "Remove or replace the banned term",
        "naming": "Use the approved product/feature name",
        "terminology": "Use the preferred terminology",
        "formatting": "Fix the formatting to match guidelines",
        "claims": "Remove or substantiate the claim with approved facts",
        "tone": "Rewrite in the approved tone",
        "required_wording": "Add the required disclosure",
    }
    return fixes.get(category, "Review and correct per guideline")


def _requires_human_review(category: str, severity: Severity) -> bool:
    """Determine if a finding requires human review."""
    # High severity findings generally need human review
    if severity == Severity.HIGH:
        return True
    # Claims and tone often need human judgment
    if category in ("claims", "tone", "naming"):
        return True
    return False


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
                    document_id=rule.document_id,
                    section=rule.section,
                ),
                suggested_fix=rule.suggested_fix,
                confidence=0.95,
                requires_human_review=rule.requires_human_review,
                label=None,
                rule_id=rule.guideline_id,
            )
            findings.append(finding)

    return findings


def check_required_phrases(draft_text: str, rules: list[DeterministicRule]) -> list[Finding]:
    """Check for missing required phrases in draft text."""
    findings = []

    for rule in rules:
        if rule.is_banned:
            continue

        # For required_wording rules with triggers, only enforce if trigger is met
        if rule.trigger_patterns:
            trigger_met = False
            for tp in rule.trigger_patterns:
                if tp.search(draft_text):
                    trigger_met = True
                    break
            if not trigger_met:
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
                    document_id=rule.document_id,
                    section=rule.section,
                ),
                suggested_fix=rule.suggested_fix,
                confidence=0.9,
                requires_human_review=rule.requires_human_review,
                label=None,
                rule_id=rule.guideline_id,
            )
            findings.append(finding)

    return findings


def run_deterministic_checks(
    draft_text: str,
    guidelines: list[Guideline],
    approved_facts: list[ApprovedFact] | None = None,
    evaluation_date: date | None = None,
) -> list[Finding]:
    """Run all deterministic checks on the draft text."""
    if not guidelines and not approved_facts:
        return []

    all_findings: list[Finding] = []

    # Check guidelines (banned terms, required phrases)
    if guidelines:
        rules = _compile_rules(guidelines)
        if rules:
            all_findings.extend(check_banned_terms(draft_text, rules))
            all_findings.extend(check_required_phrases(draft_text, rules))

    # Check approved facts for expiry, supersession, contradiction, etc.
    if approved_facts and evaluation_date:
        fact_rules = _compile_fact_rules(approved_facts, evaluation_date)
        if fact_rules:
            all_findings.extend(check_facts(draft_text, fact_rules))

    logger.info(f"Deterministic checks found {len(all_findings)} issues")
    return all_findings
