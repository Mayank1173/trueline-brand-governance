"""Deterministic matching helpers for evaluating findings against annotations.

Findings keep their precise word/pattern spans. Human annotations may mark a
whole sentence, so scoring compares the two with a positive-overlap rule rather
than widening or rewriting the finding itself.

All offsets are zero-based, end-exclusive UTF-16 code units, matching the API
and JavaScript ``slice``.
"""

from __future__ import annotations


def spans_overlap(
    finding_start: int | None,
    finding_end: int | None,
    annotation_start: int | None,
    annotation_end: int | None,
) -> bool:
    """Return true only for a non-empty, positive overlap between two spans.

    Missing, zero-length, adjacent, and disjoint spans do not overlap.
    """

    if (
        finding_start is None
        or finding_end is None
        or annotation_start is None
        or annotation_end is None
    ):
        return False
    if finding_start >= finding_end or annotation_start >= annotation_end:
        return False
    return finding_start < annotation_end and finding_end > annotation_start


def finding_matches_annotated_sentence(
    *,
    finding_rule_id: str,
    finding_category: str,
    finding_start: int | None,
    finding_end: int | None,
    annotation_rule_id: str,
    annotation_category: str,
    annotation_start: int | None,
    annotation_end: int | None,
) -> bool:
    """Return true when a precise finding matches a sentence-level annotation."""

    if finding_rule_id != annotation_rule_id:
        return False
    if finding_category != annotation_category:
        return False
    return spans_overlap(
        finding_start,
        finding_end,
        annotation_start,
        annotation_end,
    )


def finding_matches_draft_level_annotation(
    *,
    finding_rule_id: str,
    finding_category: str,
    finding_start: int | None,
    finding_end: int | None,
    annotation_rule_id: str,
    annotation_category: str,
    annotation_start: int | None,
    annotation_end: int | None,
) -> bool:
    """Match a no-span finding at draft/rule level, never to a sentence.

    Missing-content and length findings have no text location. They are aligned
    by rule/category and the absence of a span on both sides, without pretending
    they belong to an arbitrary sentence.
    """

    if finding_rule_id != annotation_rule_id:
        return False
    if finding_category != annotation_category:
        return False
    finding_is_spanless = finding_start is None and finding_end is None
    annotation_is_spanless = annotation_start is None and annotation_end is None
    return finding_is_spanless and annotation_is_spanless
