"""Type definitions shared by the deterministic engine and its adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..ai_labels import AILabel


@dataclass(frozen=True)
class CitationDraft:
    source_type: str
    source_id: str
    source_version: str | None
    source_label: str
    quoted_text: str
    valid_until: date | None = None


@dataclass(frozen=True)
class RuleDefinition:
    """A rule plus the approved source text used to explain it.

    ``match_type`` values:
    ``term``, ``preferred_term``, ``required_phrase``, ``regex``,
    ``length_limit``. Term-like categories still use ``term`` matching with
    their own category/severity.
    """

    rule_id: str
    source_id: str
    source_version: str | None
    source_label: str
    quoted_text: str
    category: str
    severity: str
    match_type: str
    explanation: str
    patterns: tuple[str, ...] = field(default_factory=tuple)
    suggested_fix: str | None = None
    confidence: float = 1.0
    requires_human_review: bool = False
    case_sensitive: bool = False
    word_boundary: bool = True
    max_chars: int | None = None
    applies_to_purposes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def citation(self) -> CitationDraft:
        return CitationDraft(
            source_type="guideline",
            source_id=self.source_id,
            source_version=self.source_version,
            source_label=self.source_label,
            quoted_text=self.quoted_text,
        )


@dataclass(frozen=True)
class FactDefinition:
    id: str
    statement: str
    source_label: str
    source_version: str | None
    valid_from: date | None = None
    valid_until: date | None = None
    is_active: bool = True


@dataclass(frozen=True)
class FindingDraft:
    rule_id: str
    matched_text: str
    start: int | None
    end: int | None
    category: str
    severity: str
    explanation: str
    citation: CitationDraft | None
    suggested_fix: str | None
    confidence: float
    requires_human_review: bool
    ai_label: AILabel | None = None
