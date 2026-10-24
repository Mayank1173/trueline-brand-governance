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
import subprocess

scripts = [
    "tests/validate_datasets.py",
    "tests/validate_ids.py",
    "tests/validate_references.py",
    "tests/validate_spans.py",
    "tests/validate_expected_statuses.py",
]

def main():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    results = []
    for script in scripts:
        print(f"=== Running {script} ===")
        try:
            result = subprocess.run([sys.executable, script], cwd=os.getcwd(), env=env)
            results.append((script, result.returncode))
            print(f"=== Exit code {result.returncode} ===\n")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((script, 1))
    
    print("=== SUMMARY TABLE ===")
    print("| Script | Status |")
    print("|--------|--------|")
    all_ok = True
    for script, code in results:
        if code == 0:
            print(f"| {script} | PASS |")
        else:
            print(f"| {script} | FAIL |")
            all_ok = False
    if all_ok:
        print("\nALL SCRIPTS PASSED")
        return 0
    else:
        print("\nSOME SCRIPTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())