# Evaluation Matching

This note defines how a precise backend finding is compared with a human
annotation for evaluation. It does not report precision or recall; no evaluation
dataset has been scored yet.

## Coordinates

- Finding offsets are zero-based, end-exclusive UTF-16 code units. This matches
  the API and JavaScript `slice`.
- Annotations use the same coordinate system.
- Findings keep their exact word or pattern span. They are **not** widened to a
  sentence to make matching easier.

## Sentence-level annotations

A finding matches a sentence annotation when all of the following hold:

1. The `rule_id` values are equal.
2. The `category` values are equal.
3. The two spans have a positive overlap: `finding.start < annotation.end` and
   `finding.end > annotation.start`.

Exact, inside, and containing overlaps match. Adjacent, disjoint, zero-length,
or missing spans do not. The implementation is
`app.evaluation.finding_matches_annotated_sentence`.

## Missing-content and length findings

Missing-content and length findings have `matched_text: ""` and no offsets. They
are never assigned to an arbitrary sentence. Match them at draft/rule level
instead, using `app.evaluation.finding_matches_draft_level_annotation`: same
`rule_id`, same `category`, and both sides spanless.

## One-to-one assignment

When the same rule occurs multiple times in one draft, assign matches
one-to-one: one predicted finding may match at most one annotated finding, and
vice versa. Any scoring script must store the assignment it used so results are
reproducible.

## Citation validity

A citation is valid when it references a loaded source for the same brand and
quotes text present in that source. A null `source_version` is valid only when
the loaded source also has no recorded version. Missing or fabricated citations
remain critical defects.
