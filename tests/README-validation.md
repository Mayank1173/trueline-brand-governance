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
- validate_ids.py: unique IDs, ID formats (NS-<CATEGORY>-###, NS-FACT-###, NS-DRAFT-##, NS-DRAFT-##-F#, NS-SNIP-##, NS-TC-###), Markdown files mention IDs.
- validate_references.py: citations and alternates exist in guidelines, test case inputs resolve, target_finding_id exists for draft cases, citation documents/sections resolve, superseded_by exists, referenced paths exist.
- validate_spans.py: end > start, within bounds, span_text appears EXACTLY ONCE using Unicode code points (end exclusive), text[start:end] == span_text; informational BMP/Non-BMP table with code-point and UTF-16 offsets.
- validate_expected_statuses.py: enums valid, fact status recomputes from evaluation date, booleans correct, no_finding null fields, results_template all null except ids/status not_run, all metrics status not_run (UNMEASURED), banned words check on drafts/revised (except NS-SNIP-01).

## Notes
- Scripts only read data files, they never change them.
- No system clock used; evaluation date read from data files.
- Scores are UNMEASURED.
- Script names do not start with test_ so pytest does not collect them.
- Scripts are safe on cp1252 consoles (use UTF-8 with backslashreplace).