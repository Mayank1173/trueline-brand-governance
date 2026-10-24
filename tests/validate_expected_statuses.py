#!/usr/bin/env python3
import sys
import os
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    else:
        try:
            import io
            if _stream is sys.stdout:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="backslashreplace")
            elif _stream is sys.stderr:
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
import json
from datetime import date

GUIDELINES = "data/northstar-brand-guidelines.json"
DRAFTS = "data/sample-drafts.json"
EVAL = "data/evaluation-dataset.json"


def _parse_date(value):
    """Return a date for an ISO string, or None when the value is empty."""
    if not value:
        return None
    return date.fromisoformat(value)


def compute_fact_status(fact, eval_date):
    """Recompute a fact's status on the evaluation date from the dataset fields.

    superseded: superseded_by is set.
    expired:    expires_on is before the evaluation date, or valid_from is after it.
    active:     otherwise.
    expires_on is treated as the last valid day (PROPOSED convention, see
    docs/dataset-mapping.md). The dataset has no valid_until key.
    """
    if fact.get("superseded_by") is not None:
        return "superseded"
    expires_on = _parse_date(fact.get("expires_on"))
    valid_from = _parse_date(fact.get("valid_from"))
    if expires_on and expires_on < eval_date:
        return "expired"
    if valid_from and valid_from > eval_date:
        return "expired"
    return "active"


def main():
    all_pass = True
    with open(GUIDELINES, "r", encoding="utf-8") as f:
        g = json.load(f)
    with open(DRAFTS, "r", encoding="utf-8") as f:
        d = json.load(f)
    with open(EVAL, "r", encoding="utf-8") as f:
        e = json.load(f)

    eval_date = date.fromisoformat(g["evaluation_as_of_date"])

    valid_labels = {"violation", "needs_human_judgement", "unsupported", "contradicted", "outdated"}
    valid_sev = {"low", "medium", "high"}
    valid_outcome = {"finding", "no_finding", "needs_human_judgement"}
    valid_case = {"positive", "negative", "edge", "ambiguous"}

    for dr in d.get("drafts", []):
        for fnd in dr.get("expected_findings", []):
            fid = fnd.get("id", dr["id"])
            if fnd.get("expected_label") not in valid_labels:
                print(f"FAIL: file={DRAFTS} record_id={fid} issue=bad label"); all_pass = False
            else:
                print(f"PASS: {dr['id']} label ok")
            if fnd.get("severity") not in valid_sev:
                print(f"FAIL: file={DRAFTS} record_id={fid} issue=bad sev"); all_pass = False
            else:
                print(f"PASS: {dr['id']} sev ok")
            if not isinstance(fnd.get("human_review_required"), bool):
                print(f"FAIL: file={DRAFTS} record_id={fid} issue=human_review_required not bool"); all_pass = False
            else:
                print(f"PASS: {dr['id']} human_review_required bool")

    for tc in e.get("test_cases", []):
        if tc.get("case_type") not in valid_case:
            print(f"FAIL: file={EVAL} record_id={tc['id']} issue=bad case_type"); all_pass = False
        else:
            print(f"PASS: {tc['id']} case_type ok")
        exp = tc.get("expected", {})
        if exp.get("outcome") not in valid_outcome:
            print(f"FAIL: file={EVAL} record_id={tc['id']} issue=bad outcome"); all_pass = False
        else:
            print(f"PASS: {tc['id']} outcome ok")
        if exp.get("label") and exp.get("label") not in valid_labels:
            print(f"FAIL: file={EVAL} record_id={tc['id']} issue=bad label"); all_pass = False
        if exp.get("severity") and exp.get("severity") not in valid_sev:
            print(f"FAIL: file={EVAL} record_id={tc['id']} issue=bad sev"); all_pass = False
        if exp.get("outcome") == "no_finding":
            for field in ["rule_or_fact_id", "finding_type", "span_text", "start", "end", "expected_finding", "citation", "severity", "label", "suggested_fix"]:
                if exp.get(field) is not None:
                    print(f"FAIL: file={EVAL} record_id={tc['id']} issue=no_finding has non-null {field}"); all_pass = False
            print(f"PASS: {tc['id']} no_finding fields null")
        if not isinstance(exp.get("human_review_required"), bool) and exp.get("outcome") != "no_finding":
            print(f"FAIL: file={EVAL} record_id={tc['id']} issue=human_review_required not bool"); all_pass = False

    # Fact status: recompute from the dataset fields and compare with the stored value.
    for f in g.get("facts", []):
        fid = f.get("id")
        stored = f.get("status_on_evaluation_date")
        try:
            computed = compute_fact_status(f, eval_date)
        except ValueError as exc:
            print(f"FAIL: file={GUIDELINES} record_id={fid} issue=bad date in valid_from or expires_on ({exc})"); all_pass = False
            continue
        if stored != computed:
            print(f"FAIL: file={GUIDELINES} record_id={fid} issue=status_on_evaluation_date is {stored} but computed {computed}"); all_pass = False
        else:
            print(f"PASS: fact {fid} status {computed} matches status_on_evaluation_date")
        # days_until_expiry is informational only: its exact meaning is not agreed yet.
        stored_days = f.get("days_until_expiry")
        expires_on = _parse_date(f.get("expires_on"))
        if isinstance(stored_days, int) and not isinstance(stored_days, bool) and expires_on:
            expected_days = (expires_on - eval_date).days
            if stored_days != expected_days:
                print(f"INFO: fact {fid} days_until_expiry is {stored_days}; expires_on minus evaluation date is {expected_days}")

    rt = e.get("results_template", [])
    for r in rt:
        rid = r.get("test_case_id") or "results_template"
        if r.get("test_case_id") and r.get("status") != "not_run":
            print(f"FAIL: file={EVAL} record_id={rid} issue=results_template status not not_run"); all_pass = False
        for k, v in r.items():
            if k in ["test_case_id", "status"]:
                continue
            if v is not None:
                print(f"FAIL: file={EVAL} record_id={rid} issue=results_template field {k} not null"); all_pass = False
    print("PASS: results_template all null except ids/status not_run")

    for m in e.get("spec", {}).get("metrics", []):
        if m.get("status") != "not_run":
            print(f"FAIL: file={EVAL} record_id={m.get('name')} issue=metric status not not_run"); all_pass = False
    print("PASS: all metrics status not_run (UNMEASURED)")

    ban_words = []
    for r in g.get("rules", []):
        if r.get("id") == "NS-BAN-001":
            ban_words = [p.lower() for p in r.get("patterns", [])]
            break
    wrong_names = ["north start", "north-star", "northstarplanner", "north star planner"]
    for dr in d.get("drafts", []):
        if dr.get("id") == "NS-DRAFT-10":
            text_low = dr.get("text", "").lower()
            for bw in ban_words:
                if bw and bw in text_low:
                    print(f"FAIL: file={DRAFTS} record_id=NS-DRAFT-10 issue=contains banned word"); all_pass = False
            for wn in wrong_names:
                if wn in text_low:
                    print(f"FAIL: file={DRAFTS} record_id=NS-DRAFT-10 issue=contains wrong name"); all_pass = False
            print("PASS: NS-DRAFT-10 clean")
        if dr.get("revised_text"):
            text_low = dr.get("revised_text", "").lower()
            for bw in ban_words:
                if bw and bw in text_low:
                    print(f"FAIL: file={DRAFTS} record_id={dr['id']} issue=revised contains banned word"); all_pass = False
            for wn in wrong_names:
                if wn in text_low:
                    print(f"FAIL: file={DRAFTS} record_id={dr['id']} issue=revised contains wrong name"); all_pass = False
            print(f"PASS: {dr['id']} revised clean")

    print("INFO: NS-SNIP-01 not checked for ban words per rules")

    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED")
        return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
