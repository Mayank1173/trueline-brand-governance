from __future__ import annotations

from app.evaluation import (
    finding_matches_annotated_sentence,
    finding_matches_draft_level_annotation,
    spans_overlap,
)


def sentence_match(
    *,
    finding_start: int | None,
    finding_end: int | None,
    annotation_start: int | None,
    annotation_end: int | None,
    finding_rule_id: str = "BR-1",
    finding_category: str = "banned_term",
    annotation_rule_id: str = "BR-1",
    annotation_category: str = "banned_term",
) -> bool:
    return finding_matches_annotated_sentence(
        finding_rule_id=finding_rule_id,
        finding_category=finding_category,
        finding_start=finding_start,
        finding_end=finding_end,
        annotation_rule_id=annotation_rule_id,
        annotation_category=annotation_category,
        annotation_start=annotation_start,
        annotation_end=annotation_end,
    )


def test_exact_inside_and_containing_spans_match():
    assert sentence_match(
        finding_start=10, finding_end=20, annotation_start=10, annotation_end=20
    )
    assert sentence_match(
        finding_start=12, finding_end=16, annotation_start=10, annotation_end=20
    )
    assert sentence_match(
        finding_start=5, finding_end=25, annotation_start=10, annotation_end=20
    )


def test_adjacent_disjoint_and_zero_length_spans_do_not_match():
    assert not sentence_match(
        finding_start=0, finding_end=10, annotation_start=10, annotation_end=20
    )
    assert not sentence_match(
        finding_start=21, finding_end=25, annotation_start=10, annotation_end=20
    )
    assert not sentence_match(
        finding_start=15, finding_end=15, annotation_start=10, annotation_end=20
    )


def test_missing_spans_do_not_match_a_sentence():
    assert not sentence_match(
        finding_start=None, finding_end=None, annotation_start=10, annotation_end=20
    )
    assert not sentence_match(
        finding_start=10, finding_end=20, annotation_start=None, annotation_end=None
    )


def test_rule_and_category_must_match():
    assert not sentence_match(
        finding_start=10,
        finding_end=20,
        annotation_start=10,
        annotation_end=20,
        finding_rule_id="BR-2",
    )
    assert not sentence_match(
        finding_start=10,
        finding_end=20,
        annotation_start=10,
        annotation_end=20,
        finding_category="tone",
    )


def test_utf16_offsets_still_use_positive_overlap():
    encoded = "😀 risky claim.".encode("utf-16-le")
    assert encoded[3 * 2 : 8 * 2].decode("utf-16-le") == "risky"
    assert sentence_match(
        finding_start=3, finding_end=8, annotation_start=3, annotation_end=14
    )


def test_draft_level_matching_requires_both_sides_to_be_spanless():
    def draft_match(
        *,
        finding_start: int | None,
        finding_end: int | None,
        annotation_start: int | None,
        annotation_end: int | None,
    ) -> bool:
        return finding_matches_draft_level_annotation(
            finding_rule_id="BR-LEGAL",
            finding_category="required_phrase",
            finding_start=finding_start,
            finding_end=finding_end,
            annotation_rule_id="BR-LEGAL",
            annotation_category="required_phrase",
            annotation_start=annotation_start,
            annotation_end=annotation_end,
        )

    assert draft_match(
        finding_start=None, finding_end=None, annotation_start=None, annotation_end=None
    )
    assert not draft_match(
        finding_start=0, finding_end=5, annotation_start=None, annotation_end=None
    )
    assert not draft_match(
        finding_start=None, finding_end=None, annotation_start=0, annotation_end=5
    )


def test_spans_overlap_handles_invalid_and_missing_bounds():
    assert not spans_overlap(None, None, 0, 1)
    assert not spans_overlap(1, 0, 0, 2)
    assert not spans_overlap(0, 1, 1, 1)
