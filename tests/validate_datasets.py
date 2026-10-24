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

DATA_FILES = [
    "data/northstar-brand-guidelines.json",
    "data/sample-drafts.json",
    "data/evaluation-dataset.json",
]

def check_file_exists(path):
    if not os.path.exists(path):
        print("FAIL: " + path + " does not exist")
        return False
    print("PASS: " + path + " exists")
    return True

def read_json_utf8(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if "\ufffd" in content:
            print("FAIL: " + path + " contains U+FFFD replacement character")
            return None
        print("PASS: " + path + " valid UTF-8 and no U+FFFD")
        data = json.loads(content)
        print("PASS: " + path + " parses as JSON")
        return data
    except Exception as e:
        print("FAIL: " + path + ": " + str(e))
        return None

def main():
    all_pass = True
    datas = {}
    for path in DATA_FILES:
        if not check_file_exists(path):
            all_pass = False
            continue
        data = read_json_utf8(path)
        if data is None:
            all_pass = False
            continue
        datas[path] = data
        for k in ["evaluation_as_of_date", "is_fictional"]:
            if k not in data:
                print("FAIL: " + path + " missing required key " + k)
                all_pass = False
            else:
                print("PASS: " + path + " has " + k)
        if "schema_version" in data:
            print("PASS: " + path + " has schema_version")
        else:
            print("FAIL: " + path + " missing schema_version")
            all_pass = False
        if data.get("is_fictional") is True:
            print("PASS: " + path + " is_fictional is true")
        else:
            print("FAIL: " + path + " is_fictional is not true")
            all_pass = False
    dates = []
    for p in DATA_FILES:
        if p in datas:
            dates.append(datas[p].get("evaluation_as_of_date"))
    if len(set(dates)) == 1 and dates and dates[0] == "2026-10-23":
        print("PASS: evaluation_as_of_date identical across all three files: " + str(dates[0]))
    else:
        print("FAIL: evaluation_as_of_date mismatch or wrong value: " + str(dates))
        all_pass = False
    if all_pass:
        print("SUMMARY: ALL CHECKS PASSED")
        return 0
    else:
        print("SUMMARY: SOME CHECKS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())