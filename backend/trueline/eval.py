#!/usr/bin/env python3
"""
Northstar Evaluation Runner

Runs the Trueline AI Review Engine against the Northstar evaluation dataset
and computes the defined metrics.

Usage:
    python -m trueline.eval [--output-dir OUTPUT_DIR]
"""

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from trueline.adapters.fastapi_adapter import (
    convert_review_response,
)
from trueline.models import (
    ApprovedFact,
    Guideline,
)
from trueline.models import (
    ReviewRequest as AIReviewRequest,
)
from trueline.models import (
    ReviewResponse as AIReviewResponse,
)
from trueline.review.service import ReviewEngine


@dataclass
class ExpectedFinding:
    """Expected finding from Northstar dataset."""
    test_case_id: str
    finding_id: str  # target_finding_id or synthetic
    rule_or_fact_id: str
    acceptable_alternate_ids: list[str]
    finding_type: str
    span_text: str
    start: int
    end: int
    expected_finding: str
    citation: str
    severity: str
    label: str
    suggested_fix: str
    human_review_required: bool
    case_type: str  # positive, negative, edge, ambiguous

    # Alternative outcomes for ambiguous cases
    acceptable_alternative_outcomes: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PredictedFinding:
    """Predicted finding from the review engine."""
    test_case_id: str
    finding_id: str
    rule_id: str
    matched_text: str
    start: int | None
    end: int | None
    category: str
    severity: str
    explanation: str
    citation_rule_id: str | None
    citation_source_type: str | None
    suggested_fix: str | None
    confidence: float
    requires_human_review: bool


@dataclass
class MatchResult:
    """Result of matching predicted to expected."""
    predicted: PredictedFinding
    expected: ExpectedFinding
    matched: bool
    match_score: float  # 0.0 to 1.0


def load_northstar_data() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load all Northstar dataset files."""
    data_dir = Path("data")

    # Load evaluation dataset (UTF-16)
    with open(data_dir / "evaluation-dataset.json", encoding="utf-16") as f:
        eval_data: dict[str, Any] = json.load(f)

    # Load sample drafts (UTF-16)
    with open(data_dir / "sample-drafts.json", encoding="utf-16") as f:
        drafts_data: dict[str, Any] = json.load(f)

    # Load guidelines (UTF-16)
    with open(data_dir / "northstar-brand-guidelines.json", encoding="utf-16") as f:
        guidelines_data: dict[str, Any] = json.load(f)

    return eval_data, drafts_data, guidelines_data


def build_guidelines_and_facts(
    guidelines_data: dict[str, Any]
) -> tuple[list[Guideline], list[ApprovedFact]]:
    """Convert Northstar guidelines/facts to AI engine models."""
    guidelines: list[Guideline] = []
    for rule in guidelines_data.get("rules", []):
        # Map Northstar category to AI Category
        cat_mapping = {
            "tone": "tone",
            "naming": "naming",
            "terminology": "terminology",
            "banned_language": "banned_language",
            "required_wording": "required_wording",
            "formatting": "formatting",
            "claims": "claims",
        }
        ai_category = cat_mapping.get(rule.get("category", "").lower(), "banned_term")

        # Build guideline with patterns for deterministic checking.
        # The evaluation harness is deterministic-only, so every rule with
        # patterns is evaluated deterministically even when the dataset marks
        # it as hybrid.
        patterns = rule.get("patterns", [])
        check_method = "computed"

        # Northstar tone rules with \b[A-Z]{3,}\b patterns need case_sensitive=True
        # NS-TONE-001: has \b[A-Z]{3,}\b pattern -> case_sensitive=True
        # NS-TONE-002: phrase patterns -> case_sensitive=False
        # NS-TONE-003: word patterns + emoji -> case_sensitive=False for words
        # Also naming, terminology, banned_language rules should be case-sensitive
        rule_id = rule.get("id", "")
        if rule_id == "NS-TONE-001":
            case_sensitive = True
        elif rule_id in ("NS-TONE-002", "NS-TONE-003"):
            case_sensitive = False
        else:
            case_sensitive = rule.get("category", "").lower() in (
                "tone", "naming", "terminology", "banned_language"
            )

        source = rule.get("source", {})
        guideline = Guideline(
            id=rule["id"],
            title=rule.get("title", rule["id"]),
            text=rule.get("rule_text") or rule.get("title", rule["id"]),
            category=ai_category,
            source=source.get("document_id") or guidelines_data.get("pack_id", "Northstar"),
            document_id=source.get("document_id"),
            section=source.get("section"),
            patterns=patterns,
            check_method=check_method,
            match_type=rule.get("match_type"),
            severity_default=rule.get("severity_default", "medium"),
            required_phrase=rule.get("required_phrase"),
            trigger=rule.get("trigger"),
            case_sensitive=case_sensitive,
        )
        guidelines.append(guideline)

    # Convert facts
    facts = []
    for fact in guidelines_data.get("facts", []):
        ai_fact = ApprovedFact(
            id=fact["id"],
            claim=fact["statement"],
            evidence=fact.get("source", {}).get("document_id", ""),
            category=fact.get("topic", "general"),
            valid_from=fact.get("valid_from"),
            expires_on=fact.get("expires_on"),
            status_on_evaluation_date=fact.get("status_on_evaluation_date"),
            superseded_by=fact.get("superseded_by"),
        )
        facts.append(ai_fact)

    return guidelines, facts


def load_draft_text(drafts_data: dict[str, Any], draft_id: str) -> str:
    """Load draft text from sample-drafts.json."""
    for draft in drafts_data.get("drafts", []):
        if draft.get("id") == draft_id:
            text = draft.get("text")
            return str(text) if text is not None else ""
    return ""


def load_snippet_text(eval_data: dict[str, Any], snippet_id: str) -> str:
    """Load snippet text from evaluation dataset."""
    for snippet in eval_data.get("snippets", []):
        if snippet.get("id") == snippet_id:
            text = snippet.get("text")
            return str(text) if text is not None else ""
    return ""


def parse_test_cases(
    eval_data: dict[str, Any], drafts_data: dict[str, Any]
) -> list[ExpectedFinding]:
    """Parse test cases into ExpectedFinding objects."""
    expected_findings: list[ExpectedFinding] = []

    for tc in eval_data.get("test_cases", []):
        tc_id = tc["id"]
        case_type = tc["case_type"]
        expected = tc["expected"]

        # Load input text
        input_info = tc["input"]
        if input_info["type"] in ("draft", "revised_draft"):
            draft_id = input_info["id"]
            _ = load_draft_text(drafts_data, draft_id)
        elif input_info["type"] == "snippet":
            snippet_id = input_info["id"]
            _ = load_snippet_text(eval_data, snippet_id)
        else:
            pass

        if expected["outcome"] == "finding":
            # Create expected finding
            finding_id = tc.get("target_finding_id") or f"{tc_id}-F1"
            ef = ExpectedFinding(
                test_case_id=tc_id,
                finding_id=finding_id,
                rule_or_fact_id=expected["rule_or_fact_id"],
                acceptable_alternate_ids=expected.get("acceptable_alternate_ids", []),
                finding_type=expected["finding_type"],
                span_text=expected["span_text"] or "",
                start=expected["start"] or 0,
                end=expected["end"] or 0,
                expected_finding=expected["expected_finding"] or "",
                citation=expected["citation"] or "",
                severity=expected["severity"] or "medium",
                label=expected["label"] or "violation",
                suggested_fix=expected["suggested_fix"] or "",
                human_review_required=expected["human_review_required"] or False,
                case_type=case_type,
                acceptable_alternative_outcomes=expected.get("acceptable_alternative_outcomes", []),
            )
            expected_findings.append(ef)
        elif expected["outcome"] == "no_finding":
            # Negative/edge case - no expected finding
            pass
        elif expected["outcome"] == "needs_human_judgement":
            # Ambiguous case with alternative outcome
            pass

    return expected_findings


def run_review_engine(text: str, guidelines: list[Guideline], facts: list[ApprovedFact],
                      purpose: str = "general") -> AIReviewResponse:
    """Run the AI review engine (deterministic only for evaluation)."""
    engine = ReviewEngine(ai_provider=None)  # Deterministic only for evaluation

    request = AIReviewRequest(
        draft_text=text,
        brand_id="northstar",
        content_purpose=purpose,
        guidelines=guidelines,
        approved_facts=facts,
        evaluation_date=date(2026, 10, 23).isoformat(),  # Fixed evaluation date
    )

    import asyncio
    return asyncio.run(engine.review(request))


def convert_to_predicted(ai_response: AIReviewResponse, draft_text: str,
                         guidelines: list[Guideline], facts: list[ApprovedFact],
                         test_case_id: str) -> list[PredictedFinding]:
    """Convert AI engine response to PredictedFinding list."""
    fastapi_response = convert_review_response(
        ai_response, draft_text, guidelines, facts
    )

    predicted = []
    for i, f in enumerate(fastapi_response.findings):
        pf = PredictedFinding(
            test_case_id=test_case_id,
            finding_id=f.finding_id,
            rule_id=f.rule_id,
            matched_text=f.matched_text,
            start=f.start,
            end=f.end,
            category=f.category.value,
            severity=f.severity.value,
            explanation=f.explanation,
            citation_rule_id=f.citation.rule_id if f.citation else None,
            citation_source_type=f.citation.source_type.value if f.citation else None,
            suggested_fix=f.suggested_fix,
            confidence=f.confidence,
            requires_human_review=f.requires_human_review,
        )
        predicted.append(pf)

    return predicted


def compute_span_overlap(pred_start: int | None, pred_end: int | None,
                         exp_start: int, exp_end: int) -> float:
    """Compute span overlap ratio (0.0 to 1.0)."""
    if pred_start is None or pred_end is None:
        return 0.0

    overlap = max(0, min(pred_end, exp_end) - max(pred_start, exp_start))
    expected_len = exp_end - exp_start
    if expected_len <= 0:
        return 0.0
    return overlap / expected_len


def match_findings(
    predicted: list[PredictedFinding],
    expected: list[ExpectedFinding],
) -> tuple[list[MatchResult], list[PredictedFinding], list[ExpectedFinding]]:
    """
    Match predicted findings to expected findings using Northstar matching rules.

    Rules:
    1. Cited ID matches expected.rule_or_fact_id or acceptable_alternate_ids
    2. Span overlaps by at least 50% of expected span
    3. One-to-one matching (maximize valid matches)
    4. Unmatched predicted = false positives

    Returns: (matches, false_positives, false_negatives)
    """
    matches = []
    used_predicted = set()
    used_expected = set()

    # Build match candidates
    candidates = []
    for i, pred in enumerate(predicted):
        for j, exp in enumerate(expected):
            # Check ID match
            id_match = (
                pred.rule_id == exp.rule_or_fact_id or
                pred.rule_id in exp.acceptable_alternate_ids or
                pred.citation_rule_id == exp.rule_or_fact_id or
                pred.citation_rule_id in exp.acceptable_alternate_ids
            )

            # Check span overlap (50% threshold)
            span_overlap = compute_span_overlap(pred.start, pred.end, exp.start, exp.end)
            span_match = span_overlap >= 0.5

            if id_match and span_match:
                candidates.append((i, j, span_overlap))

    # Greedy matching: sort by overlap score descending, take best unique matches
    candidates.sort(key=lambda x: x[2], reverse=True)

    for i, j, score in candidates:
        if i not in used_predicted and j not in used_expected:
            pred = predicted[i]
            exp = expected[j]
            matches.append(MatchResult(pred, exp, True, score))
            used_predicted.add(i)
            used_expected.add(j)

    # False positives: predicted but not matched
    false_positives = [predicted[i] for i in range(len(predicted)) if i not in used_predicted]

    # False negatives: expected but not matched
    false_negatives = [expected[j] for j in range(len(expected)) if j not in used_expected]

    return matches, false_positives, false_negatives


def compute_metrics(matches: list[MatchResult],
                    false_positives: list[PredictedFinding],
                    false_negatives: list[ExpectedFinding],
                    all_predicted: list[PredictedFinding],
                    all_expected: list[ExpectedFinding],
                    compliant_inputs: set[tuple[str, str]],
                    compliant_inputs_with_findings: int) -> dict[str, Any]:
    """Compute all evaluation metrics."""

    tp = len(matches)
    fp = len(false_positives)
    fn = len(false_negatives)

    # Precision, Recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Citation validity rate (automated ID-exists check)
    citation_id_exists = sum(1 for m in matches if m.predicted.citation_rule_id is not None)
    citation_validity_auto = citation_id_exists / tp if tp > 0 else 0.0

    # Correct severity rate
    severity_exact = sum(1 for m in matches if m.predicted.severity == m.expected.severity)
    severity_rate = severity_exact / tp if tp > 0 else 0.0

    # Severity within one level
    severity_order = {"low": 0, "medium": 1, "high": 2}
    severity_within_one = sum(
        1
        for m in matches
        if abs(
            severity_order.get(m.predicted.severity, 1)
            - severity_order.get(m.expected.severity, 1)
        )
        <= 1
    )
    severity_within_one_rate = severity_within_one / tp if tp > 0 else 0.0

    # Suggested-fix usefulness (automated: fix re-check pass rate)
    # For now, we can't auto-check fix usefulness without re-running
    # Mark as requires human judgement
    _ = None  # Requires human review

    # False positive rate on compliant inputs
    n_compliant = len(compliant_inputs)
    if n_compliant > 0:
        fp_rate_compliant = compliant_inputs_with_findings / n_compliant
        # Convert test_case_id like "draft:NS-DRAFT-10" to tuple ("draft", "NS-DRAFT-10")
        def _input_key(tc_id: str) -> tuple[str, str]:
            if ":" in tc_id:
                parts = tc_id.split(":", 1)
                return (parts[0], parts[1])
            return ("unknown", tc_id)

        fp_per_compliant = (
            sum(1 for p in all_predicted if _input_key(p.test_case_id) in compliant_inputs)
            / n_compliant
        )
    else:
        fp_rate_compliant = 0.0
        fp_per_compliant = 0.0

    return {
        "finding_precision": round(precision, 4),
        "finding_recall": round(recall, 4),
        "finding_f1": round(f1, 4),
        "citation_validity_rate_auto": round(citation_validity_auto, 4),
        "citation_validity_rate_human": None,  # Requires human review
        "correct_severity_rate": round(severity_rate, 4),
        "severity_within_one_level_rate": round(severity_within_one_rate, 4),
        "suggested_fix_usefulness": None,  # Requires human review
        "fix_recheck_pass_rate": None,  # Requires running fixes
        "false_positive_rate_compliant": round(fp_rate_compliant, 4),
        "false_positives_per_compliant_input": round(fp_per_compliant, 4),
        "counts": {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "total_predicted": len(all_predicted),
            "total_expected": len(all_expected),
        }
    }


def run_evaluation(output_dir: Path | None = None) -> dict[str, Any]:
    """Run the full Northstar evaluation."""
    if output_dir is None:
        output_dir = Path("eval_results")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading Northstar dataset...")
    eval_data, drafts_data, guidelines_data = load_northstar_data()

    print("Building guidelines and facts...")
    guidelines, facts = build_guidelines_and_facts(guidelines_data)
    print(f"  Guidelines: {len(guidelines)}")
    print(f"  Facts: {len(facts)}")

    print("Parsing test cases...")
    expected_findings = parse_test_cases(eval_data, drafts_data)
    print(f"  Expected findings: {len(expected_findings)}")

    # Group expected findings by input text (draft_id + type for drafts, snippet_id for snippets)
    # Key: (input_type, input_id) where input_type is "draft", "revised_draft", or "snippet"
    expected_by_input: dict[tuple[str, str], list[ExpectedFinding]] = {}
    compliant_inputs: set[tuple[str, str]] = set()  # (input_type, input_id) for negative/edge
    input_case_types: dict[tuple[str, str], str] = {}  # Track case_type for reporting

    for tc in eval_data.get("test_cases", []):
        tc_id = tc["id"]
        case_type = tc["case_type"]
        input_info = tc["input"]
        input_type = input_info["type"]

        if input_type in ("draft", "revised_draft"):
            input_id = input_info["id"]
        elif input_type == "snippet":
            input_id = input_info["id"]
        else:
            continue

        input_key = (input_type, input_id)
        ef = ExpectedFinding(
            test_case_id=tc_id,
            finding_id=tc.get("target_finding_id") or f"{tc_id}-F1",
            rule_or_fact_id=tc["expected"]["rule_or_fact_id"] or "",
            acceptable_alternate_ids=tc["expected"].get("acceptable_alternate_ids", []),
            finding_type=tc["expected"]["finding_type"] or "",
            span_text=tc["expected"]["span_text"] or "",
            start=tc["expected"]["start"] or 0,
            end=tc["expected"]["end"] or 0,
            expected_finding=tc["expected"]["expected_finding"] or "",
            citation=tc["expected"]["citation"] or "",
            severity=tc["expected"]["severity"] or "medium",
            label=tc["expected"]["label"] or "violation",
            suggested_fix=tc["expected"]["suggested_fix"] or "",
            human_review_required=tc["expected"]["human_review_required"] or False,
            case_type=case_type,
            acceptable_alternative_outcomes=tc["expected"].get(
                "acceptable_alternative_outcomes", []
            ),
        )
        expected_by_input.setdefault(input_key, []).append(ef)
        input_case_types[input_key] = case_type
        if case_type in ("negative", "edge"):
            compliant_inputs.add(input_key)

    print("Running review engine on unique inputs...")
    all_predicted: list[PredictedFinding] = []
    all_expected: list[ExpectedFinding] = []
    all_matches: list[MatchResult] = []
    all_false_positives: list[PredictedFinding] = []
    all_false_negatives: list[ExpectedFinding] = []

    compliant_inputs_with_findings = 0
    per_input_results = []

    # Run engine once per unique input
    for input_key, expected in expected_by_input.items():
        input_type, input_id = input_key
        case_type = input_case_types[input_key]

        # Load input text
        if input_type in ("draft", "revised_draft"):
            if input_type == "draft":
                text = load_draft_text(drafts_data, input_id)
            else:  # revised_draft
                # Find the draft and get its revised_text
                for draft in drafts_data.get("drafts", []):
                    if draft.get("id") == input_id:
                        text = draft.get("revised_text", "")
                        break
                else:
                    text = ""
        elif input_type == "snippet":
            text = load_snippet_text(eval_data, input_id)
        else:
            text = ""

        if not text:
            print(f"  {input_type}/{input_id}: No text found, skipping")
            continue

        # Run review engine
        try:
            ai_response = run_review_engine(text, guidelines, facts)
        except Exception as e:
            print(f"  {input_type}/{input_id}: ERROR - {e}")
            continue

        # Convert to predicted findings
        tc_id = f"{input_type}:{input_id}"
        predicted = convert_to_predicted(ai_response, text, guidelines, facts, tc_id)
        all_predicted.extend(predicted)
        all_expected.extend(expected)

        # Match findings (all predicted vs all expected for this input)
        matches, false_positives, false_negatives = match_findings(predicted, expected)
        all_matches.extend(matches)
        all_false_positives.extend(false_positives)
        all_false_negatives.extend(false_negatives)

        # Track compliant input findings
        if input_key in compliant_inputs and len(predicted) > 0:
            compliant_inputs_with_findings += 1

        per_input_results.append({
            "input_id": f"{input_type}:{input_id}",
            "case_type": case_type,
            "text_length": len(text),
            "expected_count": len(expected),
            "predicted_count": len(predicted),
            "tp": len(matches),
            "fp": len(false_positives),
            "fn": len(false_negatives),
            "matches": [
                {
                    "expected_rule": m.expected.rule_or_fact_id,
                    "predicted_rule": m.predicted.rule_id,
                    "span_overlap": round(m.match_score, 4),
                    "severity_match": m.predicted.severity == m.expected.severity,
                }
                for m in matches
            ],
            "false_positives": [
                {
                    "rule_id": fp.rule_id,
                    "matched_text": fp.matched_text,
                    "category": fp.category,
                    "span": f"[{fp.start}:{fp.end}]",
                }
                for fp in false_positives
            ],
            "false_negatives": [
                {
                    "rule_id": fn.rule_or_fact_id,
                    "span_text": fn.span_text,
                    "case_type": fn.case_type,
                }
                for fn in false_negatives
            ],
        })

        status = "PASS" if len(false_positives) == 0 and len(false_negatives) == 0 else "FAIL"
        print(
            f"  {input_type}:{input_id} ({case_type}): "
            f"{len(predicted)} predicted, {len(expected)} expected -> "
            f"TP={len(matches)}, FP={len(false_positives)}, FN={len(false_negatives)} [{status}]"
        )

    # Compute overall metrics
    metrics = compute_metrics(
        all_matches,
        all_false_positives,
        all_false_negatives,
        all_predicted,
        all_expected,
        compliant_inputs,
        compliant_inputs_with_findings,
    )

    # Generate report
    report = {
        "run_date": datetime.now().isoformat(),
        "dataset_id": eval_data.get("dataset_id", "northstar-eval-v0.1"),
        "evaluation_as_of_date": eval_data.get("evaluation_as_of_date", "2026-10-23"),
        "guidelines_pack": guidelines_data.get("pack_id", "northstar-brand-guidelines"),
        "total_test_cases": len(eval_data.get("test_cases", [])),
        "unique_inputs_evaluated": len(expected_by_input),
        "metrics": metrics,
        "per_input_results": per_input_results,
        "details": {
            "matches": [
                {
                    "input_id": m.predicted.test_case_id,
                    "predicted_rule_id": m.predicted.rule_id,
                    "expected_rule_id": m.expected.rule_or_fact_id,
                    "span_overlap": round(m.match_score, 4),
                    "severity_match": m.predicted.severity == m.expected.severity,
                }
                for m in all_matches
            ],
            "false_positives": [
                {
                    "test_case_id": fp.test_case_id,
                    "rule_id": fp.rule_id,
                    "matched_text": fp.matched_text,
                    "category": fp.category,
                }
                for fp in all_false_positives
            ],
            "false_negatives": [
                {
                    "test_case_id": fn.test_case_id,
                    "rule_id": fn.rule_or_fact_id,
                    "span_text": fn.span_text,
                    "case_type": fn.case_type,
                }
                for fn in all_false_negatives
            ],
        },
        "limitations": [
            "Citation validity human-judged rate not computed (requires human review)",
            "Suggested-fix usefulness not computed (requires human review)",
            "Fix re-check pass rate not computed (requires applying fixes)",
            "Deterministic engine only used (AI provider not invoked for evaluation)",
            (
                "Fact expiry checking requires deterministic engine support "
                "(not yet implemented in AI engine)"
            ),
        ],
    }

    # Save report
    report_file = output_dir / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to: {report_file}")
    print("\n=== METRICS SUMMARY ===")
    for key, value in metrics.items():
        if key != "counts":
            print(f"  {key}: {value}")
    print(f"  counts: {metrics['counts']}")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Northstar evaluation")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval_results"),
        help="Output directory for evaluation report",
    )
    args = parser.parse_args()

    run_evaluation(args.output_dir)
