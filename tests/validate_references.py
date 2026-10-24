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
    
    rule_ids = set(r["id"] for r in g.get("rules", []))
    fact_ids = set(f["id"] for f in g.get("facts", []))
    all_rule_fact = rule_ids | fact_ids
    draft_ids = set(dr["id"] for dr in d.get("drafts", []))
    finding_ids = set()
    for dr in d.get("drafts", []):
        for fnd in dr.get("expected_findings", []):
            if fnd.get("id"): finding_ids.add(fnd["id"])
    snippet_ids = set(s["id"] for s in e.get("snippets", []))
    
    for tc in e.get("test_cases", []):
        exp = tc.get("expected", {})
        rid = exp.get("rule_or_fact_id")
        if exp.get("outcome") == "no_finding":
            if rid is not None:
                print(f"FAIL: {tc['id']} no_finding but has rule_or_fact_id"); all_pass = False
            continue
        if rid is None:
            print(f"FAIL: {tc['id']} finding but no rule_or_fact_id"); all_pass = False; continue
        if rid not in all_rule_fact:
            print(f"FAIL: {tc['id']} rule_or_fact_id {rid} not in guidelines"); all_pass = False
        else:
            print(f"PASS: {tc['id']} rule_or_fact_id {rid} exists")
        for alt in exp.get("acceptable_alternate_ids", []):
            if alt not in all_rule_fact:
                print(f"FAIL: {tc['id']} alternate {alt} not in guidelines"); all_pass = False
            else:
                print(f"PASS: {tc['id']} alternate {alt} exists")
        cit = exp.get("citation")
        if cit and isinstance(cit, str):
            parts = cit.split(" section ")
            if parts:
                doc_id = parts[0].strip()
                doc_ids = set(doc["id"] for doc in g.get("documents", []))
                if doc_id not in doc_ids:
                    print(f"FAIL: {tc['id']} citation document {doc_id} not found"); all_pass = False
                else:
                    print(f"PASS: {tc['id']} citation document {doc_id} exists")
    
    for tc in e.get("test_cases", []):
        inp = tc.get("input", {})
        itype = inp.get("type")
        iid = inp.get("id")
        if itype == "draft":
            if iid not in draft_ids:
                print(f"FAIL: {tc['id']} draft {iid} not found"); all_pass = False
            else:
                print(f"PASS: {tc['id']} draft {iid} resolves")
        elif itype == "revised_draft":
            if iid not in draft_ids:
                print(f"FAIL: {tc['id']} revised_draft {iid} not found"); all_pass = False
            else:
                print(f"PASS: {tc['id']} revised_draft {iid} resolves")
        elif itype == "snippet":
            if iid not in snippet_ids:
                print(f"FAIL: {tc['id']} snippet {iid} not found"); all_pass = False
            else:
                print(f"PASS: {tc['id']} snippet {iid} resolves")
    
    for tc in e.get("test_cases", []):
        inp = tc.get("input", {})
        if inp.get("type") in ["draft", "revised_draft"]:
            tfi = tc.get("target_finding_id")
            if tfi and tfi not in finding_ids:
                print(f"FAIL: {tc['id']} target_finding_id {tfi} not found"); all_pass = False
            elif tfi:
                print(f"PASS: {tc['id']} target_finding_id {tfi} exists")
    
    for gf in [e.get("guidelines_file"), e.get("drafts_file")]:
        if gf and not os.path.exists(gf):
            print(f"FAIL: referenced file {gf} does not exist"); all_pass = False
        elif gf:
            print(f"PASS: referenced file {gf} exists")
    
    for f in g.get("facts", []):
        sb = f.get("superseded_by")
        if sb and sb not in fact_ids:
            print(f"FAIL: fact {f['id']} superseded_by {sb} not found"); all_pass = False
        elif sb:
            print(f"PASS: fact {f['id']} superseded_by {sb} exists")
    
    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED"); return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED"); return 1

if __name__ == "__main__":
    sys.exit(main())