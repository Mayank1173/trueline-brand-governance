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
    draft_ids = set(dr["id"] for dr in d.get("drafts", []))
    finding_ids = set()
    for dr in d.get("drafts", []):
        for fnd in dr.get("expected_findings", []):
            if fnd.get("id"): finding_ids.add(fnd["id"])
        if dr.get("revised_draft") and dr["revised_draft"].get("expected_findings"):
            for fnd in dr["revised_draft"]["expected_findings"]:
                if fnd.get("id"): finding_ids.add(fnd["id"])
    snippet_ids = set(s["id"] for s in e.get("snippets", []))
    tc_ids = set(tc["id"] for tc in e.get("test_cases", []))
    
    print(f"PASS: collected {len(rule_ids)} rule IDs, {len(fact_ids)} fact IDs, {len(draft_ids)} drafts, {len(finding_ids)} findings, {len(snippet_ids)} snippets, {len(tc_ids)} test cases")
    
    rule_re = re.compile(r"^NS-[A-Z]+-\d{3}$")
    fact_re = re.compile(r"^NS-FACT-\d{3}$")
    draft_re = re.compile(r"^NS-DRAFT-\d{2}$")
    finding_re = re.compile(r"^NS-DRAFT-\d{2}-F\d+$")
    snippet_re = re.compile(r"^NS-SNIP-\d{2}$")
    tc_re = re.compile(r"^NS-TC-\d{3}$")
    
    for rid in rule_ids:
        if rule_re.match(rid): print(f"PASS: rule ID format {rid}")
        else: print(f"FAIL: rule ID format {rid}"); all_pass=False
    for fid in fact_ids:
        if fact_re.match(fid): print(f"PASS: fact ID format {fid}")
        else: print(f"FAIL: fact ID format {fid}"); all_pass=False
    for did in draft_ids:
        if draft_re.match(did): print(f"PASS: draft ID format {did}")
        else: print(f"FAIL: draft ID format {did}"); all_pass=False
    for fid in finding_ids:
        if finding_re.match(fid): print(f"PASS: finding ID format {fid}")
        else: print(f"FAIL: finding ID format {fid}"); all_pass=False
    for sid in snippet_ids:
        if snippet_re.match(sid): print(f"PASS: snippet ID format {sid}")
        else: print(f"FAIL: snippet ID format {sid}"); all_pass=False
    for tid in tc_ids:
        if tc_re.match(tid): print(f"PASS: test case ID format {tid}")
        else: print(f"FAIL: test case ID format {tid}"); all_pass=False
    
    md_files = ["data/northstar-brand-guidelines.md", "data/sample-drafts.md"]
    for md in md_files:
        if not os.path.exists(md):
            print(f"FAIL: {md} does not exist"); all_pass=False; continue
        with open(md, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"PASS: {md} exists")
        mentioned = 0
        for rid in list(rule_ids)[:3]:
            if rid in content: mentioned += 1
        if mentioned >= 1: print(f"PASS: {md} mentions rule IDs")
        else: print(f"FAIL: {md} does not mention rule IDs"); all_pass=False
    if os.path.exists("data/evaluation-dataset.md"):
        print("PASS: data/evaluation-dataset.md exists")
    else:
        print("INFO: data/evaluation-dataset.md not present (not required)")
    
    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED"); return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED"); return 1

if __name__ == "__main__":
    sys.exit(main())