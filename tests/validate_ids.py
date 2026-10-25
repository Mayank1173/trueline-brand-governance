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
import re

GUIDELINES = "data/northstar-brand-guidelines.json"
DRAFTS = "data/sample-drafts.json"
EVAL = "data/evaluation-dataset.json"


def _common_keys(records):
    """Return the keys present in every dict record of a homogeneous list."""
    records = [record for record in records if isinstance(record, dict)]
    if not records:
        return set()
    return set.intersection(*(set(record) for record in records))


def derive_required_fields(g, d, e):
    """Derive the real required fields from the current dataset.

    A field is required when it is present in every record of its type. The
    REQUIRED_* lists below are kept literal so that a field removed from the
    data is still reported as a failure instead of silently weakening the
    schema; this function is the audit that keeps those lists honest.
    """
    drafts = [record for record in d.get("drafts", []) or [] if isinstance(record, dict)]
    findings = []
    for draft in drafts:
        findings.extend(
            finding
            for finding in draft.get("expected_findings", []) or []
            if isinstance(finding, dict)
        )
        revised = draft.get("revised_draft")
        if isinstance(revised, dict):
            findings.extend(
                finding
                for finding in revised.get("expected_findings", []) or []
                if isinstance(finding, dict)
            )
    return {
        "rules": _common_keys(g.get("rules", []) or []),
        "facts": _common_keys(g.get("facts", []) or []),
        "drafts": _common_keys(drafts),
        "findings": _common_keys(findings),
        "snippets": _common_keys(e.get("snippets", []) or []),
        "test_cases": _common_keys(e.get("test_cases", []) or []),
    }



# Required fields per record type. These are literal lists on purpose: a field
# removed from the data is then reported as a failure instead of silently
# weakening the schema. test_required_field_lists_match_the_real_data in
# tests/test_northstar_validators.py compares them with
# derive_required_fields() (the keys present in EVERY real record).
REQUIRED_RULE_FIELDS = [
    "applies_to",
    "bad_example",
    "category",
    "check_method",
    "effective_date",
    "fix_guidance",
    "good_example",
    "id",
    "notes",
    "owner_role",
    "patterns",
    "required_phrase",
    "rule_text",
    "severity_default",
    "source",
    "status",
    "title",
    "trigger",
]
REQUIRED_FACT_FIELDS = [
    "days_until_expiry",
    "expires_on",
    "id",
    "notes",
    "owner_role",
    "source",
    "statement",
    "status_on_evaluation_date",
    "superseded_by",
    "topic",
    "valid_from",
]
REQUIRED_DRAFT_FIELDS = [
    "audience",
    "channel",
    "expected_findings",
    "expected_outcome",
    "headline",
    "human_review_required",
    "id",
    "notes",
    "purpose",
    "revised_text",
    "scenario_types",
    "text",
    "title",
]
REQUIRED_FINDING_FIELDS = [
    "acceptable_alternate_citation_ids",
    "category",
    "citation_id",
    "end",
    "expected_label",
    "explanation",
    "finding_type",
    "human_review_required",
    "id",
    "severity",
    "span_text",
    "start",
    "suggested_correction",
]
REQUIRED_SNIPPET_FIELDS = [
    "channel",
    "headline",
    "id",
    "text",
]
REQUIRED_TEST_CASE_FIELDS = [
    "case_type",
    "expected",
    "id",
    "input",
    "notes",
    "target_finding_id",
]

# The single lookup used by tests and reports: record type -> required fields.
REQUIRED_FIELDS = {
    "rules": REQUIRED_RULE_FIELDS,
    "facts": REQUIRED_FACT_FIELDS,
    "drafts": REQUIRED_DRAFT_FIELDS,
    "findings": REQUIRED_FINDING_FIELDS,
    "snippets": REQUIRED_SNIPPET_FIELDS,
    "test_cases": REQUIRED_TEST_CASE_FIELDS,
}


def check_required_fields(g, d, e):
    errors = []
    for idx, r in enumerate(g.get("rules", [])):
        if not isinstance(r, dict):
            errors.append(f"FAIL: file={GUIDELINES} record_id=RULE-{idx} issue=missing required field id")
            continue
        for field in REQUIRED_RULE_FIELDS:
            if field not in r:
                rid = r.get("id") if "id" in r and r.get("id") is not None else f"RULE-{idx}"
                errors.append(f"FAIL: file={GUIDELINES} record_id={rid} issue=missing required field {field}")
    for idx, fct in enumerate(g.get("facts", [])):
        if not isinstance(fct, dict):
            errors.append(f"FAIL: file={GUIDELINES} record_id=FACT-{idx} issue=missing required field id")
            continue
        for field in REQUIRED_FACT_FIELDS:
            if field not in fct:
                fid = fct.get("id") if "id" in fct and fct.get("id") is not None else f"FACT-{idx}"
                errors.append(f"FAIL: file={GUIDELINES} record_id={fid} issue=missing required field {field}")
    for idx, dr in enumerate(d.get("drafts", [])):
        if not isinstance(dr, dict):
            errors.append(f"FAIL: file={DRAFTS} record_id=DRAFT-{idx} issue=missing required field id")
            continue
        for field in REQUIRED_DRAFT_FIELDS:
            if field not in dr:
                did = dr.get("id") if "id" in dr and dr.get("id") is not None else f"DRAFT-{idx}"
                errors.append(f"FAIL: file={DRAFTS} record_id={did} issue=missing required field {field}")
        for fidx, fnd in enumerate(dr.get("expected_findings", []) or []):
            if not isinstance(fnd, dict):
                errors.append(f"FAIL: file={DRAFTS} record_id={dr.get('id', f'DRAFT-{idx}')}-F{fidx} issue=missing required field id")
                continue
            for field in REQUIRED_FINDING_FIELDS:
                if field not in fnd:
                    fid = fnd.get("id") if "id" in fnd and fnd.get("id") is not None else f"{dr.get('id', f'DRAFT-{idx}')}-F{fidx}"
                    errors.append(f"FAIL: file={DRAFTS} record_id={fid} issue=missing required field {field}")
        if dr.get("revised_draft") and isinstance(dr["revised_draft"], dict):
            rd = dr["revised_draft"]
            for fidx, fnd in enumerate(rd.get("expected_findings", []) or []):
                if not isinstance(fnd, dict):
                    errors.append(f"FAIL: file={DRAFTS} record_id={dr.get('id', f'DRAFT-{idx}')}-RF{fidx} issue=missing required field id")
                    continue
                for field in REQUIRED_FINDING_FIELDS:
                    if field not in fnd:
                        fid = fnd.get("id") if "id" in fnd and fnd.get("id") is not None else f"{dr.get('id', f'DRAFT-{idx}')}-RF{fidx}"
                        errors.append(f"FAIL: file={DRAFTS} record_id={fid} issue=missing required field {field}")
    for idx, sn in enumerate(e.get("snippets", []) or []):
        if not isinstance(sn, dict):
            errors.append(f"FAIL: file={EVAL} record_id=SNIP-{idx} issue=missing required field id")
            continue
        for field in REQUIRED_SNIPPET_FIELDS:
            if field not in sn:
                sid = sn.get("id") if "id" in sn and sn.get("id") is not None else f"SNIP-{idx}"
                errors.append(f"FAIL: file={EVAL} record_id={sid} issue=missing required field {field}")
    for idx, tc in enumerate(e.get("test_cases", []) or []):
        if not isinstance(tc, dict):
            errors.append(f"FAIL: file={EVAL} record_id=TC-{idx} issue=missing required field id")
            continue
        for field in REQUIRED_TEST_CASE_FIELDS:
            if field not in tc:
                tid = tc.get("id") if "id" in tc and tc.get("id") is not None else f"TC-{idx}"
                errors.append(f"FAIL: file={EVAL} record_id={tid} issue=missing required field {field}")
    return errors


def check_ids(g, d, e):
    errors = []
    errors.extend(check_required_fields(g, d, e))
    rule_ids = []
    for r in g.get("rules", []) or []:
        if isinstance(r, dict) and "id" in r and r["id"] is not None:
            rule_ids.append(r["id"])
    fact_ids = []
    for fct in g.get("facts", []) or []:
        if isinstance(fct, dict) and "id" in fct and fct["id"] is not None:
            fact_ids.append(fct["id"])
    draft_ids = []
    for dr in d.get("drafts", []) or []:
        if isinstance(dr, dict) and "id" in dr and dr["id"] is not None:
            draft_ids.append(dr["id"])
    finding_ids = []
    for dr in d.get("drafts", []) or []:
        if not isinstance(dr, dict):
            continue
        for fnd in dr.get("expected_findings", []) or []:
            if isinstance(fnd, dict) and fnd.get("id"):
                finding_ids.append(fnd["id"])
        if dr.get("revised_draft") and isinstance(dr["revised_draft"], dict):
            for fnd in dr["revised_draft"].get("expected_findings", []) or []:
                if isinstance(fnd, dict) and fnd.get("id"):
                    finding_ids.append(fnd["id"])
    snippet_ids = []
    for s in e.get("snippets", []) or []:
        if isinstance(s, dict) and s.get("id") is not None:
            snippet_ids.append(s["id"])
    tc_ids = []
    for tc in e.get("test_cases", []) or []:
        if isinstance(tc, dict) and tc.get("id") is not None:
            tc_ids.append(tc["id"])
    rule_re = re.compile(r"^NS-[A-Z]+-\d{3}$")
    fact_re = re.compile(r"^NS-FACT-\d{3}$")
    draft_re = re.compile(r"^NS-DRAFT-\d{2}$")
    finding_re = re.compile(r"^NS-DRAFT-\d{2}-F\d+$")
    snippet_re = re.compile(r"^NS-SNIP-\d{2}$")
    tc_re = re.compile(r"^NS-TC-\d{3}$")
    for rid in rule_ids:
        if not rule_re.match(str(rid)):
            errors.append(f"FAIL: file={GUIDELINES} record_id={rid} issue=bad rule ID format")
    for fid in fact_ids:
        if not fact_re.match(str(fid)):
            errors.append(f"FAIL: file={GUIDELINES} record_id={fid} issue=bad fact ID format")
    for did in draft_ids:
        if not draft_re.match(str(did)):
            errors.append(f"FAIL: file={DRAFTS} record_id={did} issue=bad draft ID format")
    for fid in finding_ids:
        if not finding_re.match(str(fid)):
            errors.append(f"FAIL: file={DRAFTS} record_id={fid} issue=bad finding ID format")
    for sid in snippet_ids:
        if not snippet_re.match(str(sid)):
            errors.append(f"FAIL: file={EVAL} record_id={sid} issue=bad snippet ID format")
    for tid in tc_ids:
        if not tc_re.match(str(tid)):
            errors.append(f"FAIL: file={EVAL} record_id={tid} issue=bad test case ID format")

    def find_duplicates(lst):
        seen = set()
        dups = set()
        for x in lst:
            if x in seen:
                dups.add(x)
            else:
                seen.add(x)
        return sorted(list(dups))

    dup_rules = find_duplicates(rule_ids)
    if dup_rules:
        for drid in dup_rules:
            errors.append(f"FAIL: file={GUIDELINES} record_id={drid} issue=duplicate rule ID")

    dup_facts = find_duplicates(fact_ids)
    if dup_facts:
        for dfid in dup_facts:
            errors.append(f"FAIL: file={GUIDELINES} record_id={dfid} issue=duplicate fact ID")

    dup_drafts = find_duplicates(draft_ids)
    if dup_drafts:
        for ddid in dup_drafts:
            errors.append(f"FAIL: file={DRAFTS} record_id={ddid} issue=duplicate draft ID")

    dup_findings = find_duplicates(finding_ids)
    if dup_findings:
        for dfid in dup_findings:
            errors.append(f"FAIL: file={DRAFTS} record_id={dfid} issue=duplicate finding ID")

    dup_snippets = find_duplicates(snippet_ids)
    if dup_snippets:
        for dsid in dup_snippets:
            errors.append(f"FAIL: file={EVAL} record_id={dsid} issue=duplicate snippet ID")

    dup_tcs = find_duplicates(tc_ids)
    if dup_tcs:
        for dtid in dup_tcs:
            errors.append(f"FAIL: file={EVAL} record_id={dtid} issue=duplicate test case ID")
    return errors


def check_markdown_mentions_all_ids(g=None, d=None, e=None, guidelines_md="data/northstar-brand-guidelines.md",
                                     drafts_md="data/sample-drafts.md",
                                     eval_md="tests/evaluation-matrix.md",
                                     guidelines_text=None, drafts_text=None, eval_text=None):
    errors = []
    rule_ids = []
    if g is not None:
        for r in g.get("rules", []) or []:
            if isinstance(r, dict) and r.get("id"):
                rule_ids.append(str(r["id"]))
    fact_ids = []
    if g is not None:
        for fct in g.get("facts", []) or []:
            if isinstance(fct, dict) and fct.get("id"):
                fact_ids.append(str(fct["id"]))
    draft_ids = []
    if d is not None:
        for dr in d.get("drafts", []) or []:
            if isinstance(dr, dict) and dr.get("id"):
                draft_ids.append(str(dr["id"]))
    finding_ids = []
    if d is not None:
        for dr in d.get("drafts", []) or []:
            if not isinstance(dr, dict):
                continue
            for fnd in dr.get("expected_findings", []) or []:
                if isinstance(fnd, dict) and fnd.get("id"):
                    finding_ids.append(str(fnd["id"]))
            if dr.get("revised_draft") and isinstance(dr["revised_draft"], dict):
                for fnd in dr["revised_draft"].get("expected_findings", []) or []:
                    if isinstance(fnd, dict) and fnd.get("id"):
                        finding_ids.append(str(fnd["id"]))
    tc_ids = []
    if e is not None:
        for tc in e.get("test_cases", []) or []:
            if isinstance(tc, dict) and tc.get("id"):
                tc_ids.append(str(tc["id"]))

    # guidelines.md must contain every rule ID and fact ID
    if guidelines_text is not None:
        content_g = guidelines_text
    elif os.path.exists(guidelines_md):
        with open(guidelines_md, "r", encoding="utf-8") as f:
            content_g = f.read()
    else:
        content_g = ""
        for rid in rule_ids:
            errors.append(f"FAIL: file={guidelines_md} record_id={rid} issue=missing ID in markdown")
        for fid in fact_ids:
            errors.append(f"FAIL: file={guidelines_md} record_id={fid} issue=missing ID in markdown")
    if guidelines_text is not None or os.path.exists(guidelines_md) or content_g != "":
        for rid in rule_ids:
            if rid not in content_g:
                errors.append(f"FAIL: file={guidelines_md} record_id={rid} issue=missing ID in markdown")
        for fid in fact_ids:
            if fid not in content_g:
                errors.append(f"FAIL: file={guidelines_md} record_id={fid} issue=missing ID in markdown")

    # drafts.md must contain every draft ID and finding ID
    if drafts_text is not None:
        content_d = drafts_text
    elif os.path.exists(drafts_md):
        with open(drafts_md, "r", encoding="utf-8") as f:
            content_d = f.read()
    else:
        content_d = ""
        for did in draft_ids:
            errors.append(f"FAIL: file={drafts_md} record_id={did} issue=missing ID in markdown")
        for fid in finding_ids:
            errors.append(f"FAIL: file={drafts_md} record_id={fid} issue=missing ID in markdown")
    if drafts_text is not None or os.path.exists(drafts_md) or content_d != "":
        for did in draft_ids:
            if did not in content_d:
                errors.append(f"FAIL: file={drafts_md} record_id={did} issue=missing ID in markdown")
        for fid in finding_ids:
            if fid not in content_d:
                errors.append(f"FAIL: file={drafts_md} record_id={fid} issue=missing ID in markdown")

    # evaluation-matrix.md must contain every test case ID
    if eval_text is not None:
        content_e = eval_text
    elif os.path.exists(eval_md):
        with open(eval_md, "r", encoding="utf-8") as f:
            content_e = f.read()
    else:
        content_e = ""
        for tid in tc_ids:
            errors.append(f"FAIL: file={eval_md} record_id={tid} issue=missing ID in markdown")
    if eval_text is not None or os.path.exists(eval_md) or content_e != "":
        for tid in tc_ids:
            if tid not in content_e:
                errors.append(f"FAIL: file={eval_md} record_id={tid} issue=missing ID in markdown")

    return errors


# Alias for flexibility
check_markdown_mentions = check_markdown_mentions_all_ids
check_ids_in_markdown = check_markdown_mentions_all_ids



def main():
    all_pass = True
    with open(GUIDELINES, "r", encoding="utf-8") as f:
        g = json.load(f)
    with open(DRAFTS, "r", encoding="utf-8") as f:
        d = json.load(f)
    with open(EVAL, "r", encoding="utf-8") as f:
        e = json.load(f)
    rule_ids = set(r["id"] for r in g.get("rules", []) if isinstance(r, dict) and r.get("id"))
    fact_ids = set(f["id"] for f in g.get("facts", []) if isinstance(f, dict) and f.get("id"))
    draft_ids = set(dr["id"] for dr in d.get("drafts", []) if isinstance(dr, dict) and dr.get("id"))
    finding_ids = set()
    for dr in d.get("drafts", []):
        if not isinstance(dr, dict):
            continue
        for fnd in dr.get("expected_findings", []) or []:
            if isinstance(fnd, dict) and fnd.get("id"):
                finding_ids.add(fnd["id"])
        if dr.get("revised_draft") and isinstance(dr["revised_draft"], dict):
            for fnd in dr["revised_draft"].get("expected_findings", []) or []:
                if isinstance(fnd, dict) and fnd.get("id"):
                    finding_ids.add(fnd["id"])
    snippet_ids = set(s["id"] for s in e.get("snippets", []) if isinstance(s, dict) and s.get("id"))
    tc_ids = set(tc["id"] for tc in e.get("test_cases", []) if isinstance(tc, dict) and tc.get("id"))
    print(f"PASS: collected {len(rule_ids)} rule IDs, {len(fact_ids)} fact IDs, {len(draft_ids)} drafts, {len(finding_ids)} findings, {len(snippet_ids)} snippets, {len(tc_ids)} test cases")
    md_errors = check_markdown_mentions_all_ids(g, d, e)
    for er in md_errors:
        print(er)
        all_pass = False
    errs = check_ids(g, d, e)
    for er in errs:
        print(er)
        all_pass = False
    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED")
        return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
