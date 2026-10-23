"""Citation validation.

Every finding citation is checked against rows that were actually loaded for
the requested brand. A citation is rejected when its source does not exist,
belongs to another brand, has the wrong version, or quotes text that is not in
the source. This is deliberately strict: an invalid citation is an engine bug,
not something to display to a user.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import ApprovedFact, Guideline
from .rule_engine.models import FindingDraft


class CitationValidationError(Exception):
    pass


def validate_finding_citations(
    findings: Iterable[FindingDraft],
    *,
    brand_id: str,
    guidelines: Mapping[str, Guideline],
    facts: Mapping[str, ApprovedFact],
) -> None:
    for finding in findings:
        citation = finding.citation
        if citation is None:
            continue

        if citation.source_type == "guideline":
            source = guidelines.get(citation.source_id)
            if source is None:
                raise CitationValidationError(
                    f"Finding {finding.rule_id} references unknown guideline "
                    f"{citation.source_id!r}"
                )
            if source.brand_id != brand_id:
                raise CitationValidationError(
                    f"Guideline {citation.source_id!r} belongs to another brand"
                )
            if source.rule_id != finding.rule_id:
                raise CitationValidationError(
                    f"Guideline {citation.source_id!r} does not define rule "
                    f"{finding.rule_id!r}"
                )
            _check_version_and_quote(
                source_version=source.version,
                source_content=source.content,
                quoted_version=citation.source_version,
                quoted_text=citation.quoted_text,
                label=f"guideline {citation.source_id!r}",
            )
            continue

        if citation.source_type == "approved_fact":
            fact = facts.get(citation.source_id)
            if fact is None:
                raise CitationValidationError(
                    f"Finding {finding.rule_id} references unknown approved fact "
                    f"{citation.source_id!r}"
                )
            if fact.brand_id != brand_id:
                raise CitationValidationError(
                    f"Approved fact {citation.source_id!r} belongs to another brand"
                )
            _check_version_and_quote(
                source_version=fact.source_version,
                source_content=fact.statement,
                quoted_version=citation.source_version,
                quoted_text=citation.quoted_text,
                label=f"approved fact {citation.source_id!r}",
            )
            continue

        raise CitationValidationError(
            f"Unsupported citation source_type {citation.source_type!r}"
        )


def _check_version_and_quote(
    *,
    source_version: str,
    source_content: str,
    quoted_version: str,
    quoted_text: str,
    label: str,
) -> None:
    if not source_version or quoted_version != source_version:
        raise CitationValidationError(
            f"Citation version {quoted_version!r} does not match {label} "
            f"version {source_version!r}"
        )
    if not quoted_text or quoted_text not in source_content:
        raise CitationValidationError(
            f"Citation quoted text is not contained in {label}"
        )
