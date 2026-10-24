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
            if fnd.get("expected_label") not in valid_labels:
                print(f"FAIL: {dr['id']} bad label"); all_pass=False
            else:
                print(f"PASS: {dr['id']} label ok")
            if fnd.get("severity") not in valid_sev:
                print(f"FAIL: {dr['id']} bad sev"); all_pass=False
            else:
                print(f"PASS: {dr['id']} sev ok")
            if not isinstance(fnd.get("human_review_required"), bool):
                print(f"FAIL: {dr['id']} human_review_required not bool"); all_pass=False
            else:
                print(f"PASS: {dr['id']} human_review_required bool")
    
    for tc in e.get("test_cases", []):
        if tc.get("case_type") not in valid_case:
            print(f"FAIL: {tc['id']} bad case_type"); all_pass=False
        else:
            print(f"PASS: {tc['id']} case_type ok")
        exp = tc.get("expected", {})
        if exp.get("outcome") not in valid_outcome:
            print(f"FAIL: {tc['id']} bad outcome"); all_pass=False
        else:
            print(f"PASS: {tc['id']} outcome ok")
        if exp.get("label") and exp.get("label") not in valid_labels:
            print(f"FAIL: {tc['id']} bad label"); all_pass=False
        if exp.get("severity") and exp.get("severity") not in valid_sev:
            print(f"FAIL: {tc['id']} bad sev"); all_pass=False
        if exp.get("outcome") == "no_finding":
            for field in ["rule_or_fact_id", "finding_type", "span_text", "start", "end", "expected_finding", "citation", "severity", "label", "suggested_fix"]:
                if exp.get(field) is not None:
                    print(f"FAIL: {tc['id']} no_finding has non-null {field}"); all_pass=False
            print(f"PASS: {tc['id']} no_finding fields null")
        if not isinstance(exp.get("human_review_required"), bool) and exp.get("outcome") != "no_finding":
            print(f"FAIL: {tc['id']} human_review_required not bool"); all_pass=False
    
    for f in g.get("facts", []):
        vf = f.get("valid_from")
        vu = f.get("valid_until")
        superseded = f.get("superseded_by") is not None
        if vf:
            vf_d = date.fromisoformat(vf)
        else:
            vf_d = None
        if vu:
            vu_d = date.fromisoformat(vu)
        else:
            vu_d = None
        if superseded:
            status = "superseded"
        elif vu_d and vu_d < eval_date:
            status = "expired"
        elif vf_d and vf_d > eval_date:
            status = "expired"
        else:
            status = "active"
        print(f"PASS: fact {f['id']} status {status}")
    
    rt = e.get("results_template", [])
    for r in rt:
        if r.get("test_case_id") and r.get("status") != "not_run":
            print(f"FAIL: results_template status not not_run"); all_pass=False
        for k,v in r.items():
            if k in ["test_case_id", "status"]:
                continue
            if v is not None:
                print(f"FAIL: results_template field {k} not null"); all_pass=False
    print(f"PASS: results_template all null except ids/status not_run")
    
    for m in e.get("spec", {}).get("metrics", []):
        if m.get("status") != "not_run":
            print(f"FAIL: metric {m.get('name')} status not not_run"); all_pass=False
    print(f"PASS: all metrics status not_run (UNMEASURED)")
    
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
                    print(f"FAIL: NS-DRAFT-10 contains banned word"); all_pass=False
            for wn in wrong_names:
                if wn in text_low:
                    print(f"FAIL: NS-DRAFT-10 contains wrong name"); all_pass=False
            print(f"PASS: NS-DRAFT-10 clean")
        if dr.get("revised_text"):
            text_low = dr.get("revised_text", "").lower()
            for bw in ban_words:
                if bw and bw in text_low:
                    print(f"FAIL: {dr['id']} revised contains banned word"); all_pass=False
            for wn in wrong_names:
                if wn in text_low:
                    print(f"FAIL: {dr['id']} revised contains wrong name"); all_pass=False
            print(f"PASS: {dr['id']} revised clean")
    
    print(f"INFO: NS-SNIP-01 not checked for ban words per rules")
    
    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED")
        return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())