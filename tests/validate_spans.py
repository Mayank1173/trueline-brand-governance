#!/usr/bin/env python3
import sys
import os

# Make stdout/stderr safe
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

def get_code_points(s):
    return list(s)

def utf16_units(s):
    return len(s.encode("utf-16-le")) // 2

def main():
    all_pass = True
    with open(GUIDELINES, "r", encoding="utf-8") as f:
        g = json.load(f)
    with open(DRAFTS, "r", encoding="utf-8") as f:
        d = json.load(f)
    with open(EVAL, "r", encoding="utf-8") as f:
        e = json.load(f)
    
    # Check draft findings
    for dr in d.get("drafts", []):
        text = dr.get("text", "")
        cps = get_code_points(text)
        for fnd in dr.get("expected_findings", []):
            start = fnd.get("start")
            end = fnd.get("end")
            span = fnd.get("span_text", "")
            if start is None or end is None:
                print(f"FAIL: {dr['id']} finding {fnd.get('id')} has null span")
                all_pass = False
                continue
            if end <= start:
                print(f"FAIL: {dr['id']} finding {fnd.get('id')} end <= start")
                all_pass = False
                continue
            if start < 0 or end > len(cps):
                print(f"FAIL: {dr['id']} finding {fnd.get('id')} out of bounds")
                all_pass = False
                continue
            actual = "".join(cps[start:end])
            if actual != span:
                print(f"FAIL: {dr['id']} finding {fnd.get('id')} text mismatch")
                all_pass = False
            else:
                print(f"PASS: {dr['id']} finding {fnd.get('id')} span matches")
            count_cp = 0
            cps_text = get_code_points(text)
            sp = get_code_points(span)
            for i in range(len(cps_text) - len(sp) + 1):
                if cps_text[i:i+len(sp)] == sp:
                    count_cp += 1
            if count_cp != 1:
                print(f"FAIL: {dr['id']} finding {fnd.get('id')} span appears {count_cp} times")
                all_pass = False
            else:
                print(f"PASS: {dr['id']} finding {fnd.get('id')} span appears exactly once")
    
    # Check snippets
    for sn in e.get("snippets", []):
        text = sn.get("text", "")
        cps = get_code_points(text)
        for tc in e.get("test_cases", []):
            if tc.get("input", {}).get("type") == "snippet" and tc.get("input", {}).get("id") == sn["id"]:
                exp = tc.get("expected", {})
                if exp.get("outcome") == "no_finding":
                    continue
                start = exp.get("start")
                end = exp.get("end")
                span = exp.get("span_text")
                if start is None or end is None or span is None:
                    print(f"FAIL: {tc['id']} has null span")
                    all_pass = False
                    continue
                if end <= start:
                    print(f"FAIL: {tc['id']} end <= start")
                    all_pass = False
                    continue
                if start < 0 or end > len(cps):
                    print(f"FAIL: {tc['id']} out of bounds")
                    all_pass = False
                    continue
                actual = "".join(cps[start:end])
                if actual != span:
                    print(f"FAIL: {tc['id']} text mismatch")
                    all_pass = False
                else:
                    print(f"PASS: {tc['id']} span matches")
                count_cp = 0
                cps_text = get_code_points(text)
                sp = get_code_points(span)
                for i in range(len(cps_text) - len(sp) + 1):
                    if cps_text[i:i+len(sp)] == sp:
                        count_cp += 1
                if count_cp != 1:
                    print(f"FAIL: {tc['id']} span appears {count_cp} times")
                    all_pass = False
                else:
                    print(f"PASS: {tc['id']} span appears exactly once")
    
    # INFORMATIONAL
    print("INFORMATIONAL: Non-BMP texts and spans")
    for dr in d.get("drafts", []):
        text = dr.get("text", "")
        has_nonbmp = any(ord(ch) > 0xFFFF for ch in text)
        if has_nonbmp:
            print(f"INFO: {dr['id']} has non-BMP chars")
            cps = get_code_points(text)
            for fnd in dr.get("expected_findings", []):
                start = fnd.get("start")
                end = fnd.get("end")
                span = fnd.get("span_text", "")
                if start is None or end is None:
                    continue
                utf16_start = utf16_units("".join(cps[:start]))
                utf16_end = utf16_units("".join(cps[:end]))
                print(f"  {dr['id']} {fnd.get('id')} span_text={ascii(span)} cp_start={start} cp_end={end} utf16_start={utf16_start} utf16_end={utf16_end}")
        rtext = dr.get("revised_text") or (dr.get("revised_draft") or {}).get("text")
        if rtext:
            has_nonbmp_r = any(ord(ch) > 0xFFFF for ch in rtext)
            if has_nonbmp_r:
                print(f"INFO: {dr['id']}-revised has non-BMP chars")
    for dr in d.get("drafts", []):
        h = dr.get("headline")
        if h and any(ord(ch) > 0xFFFF for ch in h):
            print(f"INFO: {dr['id']}-headline has non-BMP chars")
    for sn in e.get("snippets", []):
        text = sn.get("text", "")
        if any(ord(ch) > 0xFFFF for ch in text):
            print(f"INFO: {sn['id']} has non-BMP chars")
            cps = get_code_points(text)
            for tc in e.get("test_cases", []):
                if tc.get("input", {}).get("type") == "snippet" and tc.get("input", {}).get("id") == sn["id"]:
                    exp = tc.get("expected", {})
                    if exp.get("outcome") == "no_finding":
                        continue
                    start = exp.get("start")
                    end = exp.get("end")
                    span = exp.get("span_text", "")
                    if start is None or end is None:
                        continue
                    utf16_start = utf16_units("".join(cps[:start]))
                    utf16_end = utf16_units("".join(cps[:end]))
                    print(f"  {sn['id']} {tc['id']} span_text={ascii(span)} cp_start={start} cp_end={end} utf16_start={utf16_start} utf16_end={utf16_end}")
    
    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED")
        return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())