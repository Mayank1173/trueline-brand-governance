# Tests README - Validation

## How to run

From the repo root in PowerShell:
```powershell
python tests/run_all_validations.py
```

Or run individual scripts:
```powershell
python tests/validate_datasets.py
python tests/validate_ids.py
python tests/validate_references.py
python tests/validate_spans.py
python tests/validate_expected_statuses.py
```

From cmd:
```cmd
python tests\run_all_validations.py
```

## What each script checks
- validate_datasets.py: files exist, valid UTF-8 with no U+FFFD, JSON parses, required keys, evaluation_as_of_date identical across the three data files (2026-10-23), is_fictional true, schema_version present.
- validate_ids.py: required fields of every rule, fact, draft, finding, snippet and test case (check_required_fields; the lists are literal and a unit test compares them with the keys present in every real record); unique IDs, where a duplicate error names the duplicated ID (`record_id=<the actual ID>`); ID formats (NS-<CATEGORY>-###, NS-FACT-###, NS-DRAFT-##, NS-DRAFT-##-F#, NS-SNIP-##, NS-TC-###); the Markdown check verifies that EVERY rule ID and fact ID appears in data/northstar-brand-guidelines.md, EVERY draft ID and finding ID in data/sample-drafts.md, and EVERY test case ID in tests/evaluation-matrix.md (the error names the missing ID).
- validate_references.py: citations and alternates exist in guidelines, test case inputs resolve, target_finding_id exists for draft cases, citation documents/sections resolve, superseded_by exists, referenced paths exist.
- validate_spans.py: end > start, within bounds, span_text appears EXACTLY ONCE using Unicode code points (end exclusive), text[start:end] == span_text; informational BMP/Non-BMP table with code-point and UTF-16 offsets.
- validate_expected_statuses.py: enums valid, booleans correct, no_finding null fields, results_template all null except ids/status not_run, all metrics status not_run (UNMEASURED), banned words check on drafts/revised (except NS-SNIP-01). Fact status: `compute_fact_status` recomputes each fact's status on the evaluation date from `superseded_by`, `expires_on` and `valid_from` (the dataset has no `valid_until` key), and the script FAILS when the result differs from the stored `status_on_evaluation_date`. `expires_on` is treated as the last valid day (Proposed, to be confirmed). A `days_until_expiry` that differs from `expires_on` minus the evaluation date is only reported as INFO because its meaning is not agreed yet.

## Error format
Every failure line names the file, the record and the issue:
```text
FAIL: file=data/northstar-brand-guidelines.json record_id=NS-FACT-003 issue=status_on_evaluation_date is active but computed expired
```
(validate_datasets.py names the file in its own wording.)

## Notes
- Scripts only read data files, they never change them.
- No system clock used; evaluation date read from data files.
- Scores are UNMEASURED.
- Script names do not start with test_ so pytest does not collect them.
- Scripts are safe on cp1252 consoles (use UTF-8 with backslashreplace).

## Unit tests
The tests change deep copies of the real data in memory (the data files are never modified), run the validators and assert the exact record ID and issue:
```powershell
python -m unittest tests.test_northstar_validators -v
```
