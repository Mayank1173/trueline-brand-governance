#!/usr/bin/env python3
"""Unit tests for the Northstar dataset validators.

Every negative test mutates a deep copy of the real data in memory (the data
files are never changed) and asserts that the validator reports the exact
broken record ID and the issue, in the form
`FAIL: file=<path> record_id=<id> issue=<text>`.
"""
import contextlib
import copy
import importlib.util
import io
import json
import os
import sys
import unittest
from unittest import mock


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _run_main(module, guidelines, drafts, evaluation):
    """Run a validator's main() against in-memory data and return (code, output)."""
    real_open = open

    def payload_for(path):
        base = os.path.basename(str(path)).lower()
        if "guideline" in base:
            return guidelines
        if "draft" in base:
            return drafts
        if "evaluation" in base or "eval" in base:
            return evaluation
        return None

    sources = []
    for attr in ("GUIDELINES", "DRAFTS", "EVAL"):
        if hasattr(module, attr):
            sources.append(getattr(module, attr))
    sources.extend(getattr(module, "DATA_FILES", []))
    payloads = {}
    for path in sources:
        payload = payload_for(path)
        if payload is not None:
            payloads[os.path.normcase(os.path.abspath(path))] = payload

    def fake_open(path, *args, **kwargs):
        key = os.path.normcase(os.path.abspath(path))
        if key in payloads:
            return io.StringIO(json.dumps(payloads[key], ensure_ascii=False))
        return real_open(path, *args, **kwargs)

    output = io.StringIO()
    with mock.patch("builtins.open", side_effect=fake_open):
        with contextlib.redirect_stdout(output):
            code = module.main()
    return code, output.getvalue()


def fail_line(path, record_id, issue):
    return f"FAIL: file={path} record_id={record_id} issue={issue}"


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATE_DATASETS = os.path.join(ROOT, "tests", "validate_datasets.py")
VALIDATE_IDS = os.path.join(ROOT, "tests", "validate_ids.py")
VALIDATE_REFERENCES = os.path.join(ROOT, "tests", "validate_references.py")
VALIDATE_SPANS = os.path.join(ROOT, "tests", "validate_spans.py")
VALIDATE_EXPECTED = os.path.join(ROOT, "tests", "validate_expected_statuses.py")


class TestNorthstarValidators(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_cwd = os.getcwd()
        os.chdir(ROOT)
        with open(os.path.join(ROOT, "data", "northstar-brand-guidelines.json"), "r", encoding="utf-8") as f:
            cls.g = json.load(f)
        with open(os.path.join(ROOT, "data", "sample-drafts.json"), "r", encoding="utf-8") as f:
            cls.d = json.load(f)
        with open(os.path.join(ROOT, "data", "evaluation-dataset.json"), "r", encoding="utf-8") as f:
            cls.e = json.load(f)
        cls.vi = _load_module("validate_ids_mod_t", VALIDATE_IDS)
        cls.vr = _load_module("validate_refs_mod_t", VALIDATE_REFERENCES)
        cls.vs = _load_module("validate_spans_mod_t", VALIDATE_SPANS)
        cls.ve = _load_module("validate_exp_mod_t", VALIDATE_EXPECTED)
        cls.vd = _load_module("validate_dsets_mod_t", VALIDATE_DATASETS)

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls._old_cwd)

    def _fact(self, data, fact_id):
        for fact in data["facts"]:
            if fact["id"] == fact_id:
                return fact
        self.fail(f"fact {fact_id} not found in the dataset")

    # ---------- real data ----------

    def test_real_data_no_errors_all_check_functions(self):
        self.assertEqual(self.vi.check_ids(copy.deepcopy(self.g), copy.deepcopy(self.d), copy.deepcopy(self.e)), [])
        self.assertEqual(self.vi.main(), 0)
        self.assertEqual(self.vr.main(), 0)
        self.assertEqual(self.vs.main(), 0)
        self.assertEqual(self.ve.main(), 0)
        self.assertEqual(self.vd.main(), 0)

    def test_real_data_fact_statuses(self):
        code, output = _run_main(self.ve, self.g, self.d, self.e)
        self.assertEqual(code, 0)
        self.assertIn("PASS: fact NS-FACT-003 status expired matches status_on_evaluation_date", output)
        self.assertIn("PASS: fact NS-FACT-010 status superseded matches status_on_evaluation_date", output)

    # ---------- IDs ----------

    def test_duplicate_rule_id_fails(self):
        g = copy.deepcopy(self.g)
        dup_id = g["rules"][0]["id"]
        g["rules"].append(copy.deepcopy(g["rules"][0]))
        errs = self.vi.check_ids(g, self.d, self.e)
        self.assertIn(fail_line(self.vi.GUIDELINES, dup_id, "duplicate rule ID"), errs)

    def test_duplicate_fact_id_fails(self):
        g = copy.deepcopy(self.g)
        dup_id = g["facts"][0]["id"]
        g["facts"].append(copy.deepcopy(g["facts"][0]))
        errs = self.vi.check_ids(g, self.d, self.e)
        self.assertIn(fail_line(self.vi.GUIDELINES, dup_id, "duplicate fact ID"), errs)

    def test_duplicate_finding_id_fails(self):
        d = copy.deepcopy(self.d)
        dup_id = d["drafts"][0]["expected_findings"][0]["id"]
        d["drafts"][0]["expected_findings"].append(copy.deepcopy(d["drafts"][0]["expected_findings"][0]))
        errs = self.vi.check_ids(self.g, d, self.e)
        self.assertIn(fail_line(self.vi.DRAFTS, dup_id, "duplicate finding ID"), errs)

    def test_duplicate_test_case_id_fails(self):
        e = copy.deepcopy(self.e)
        dup_id = e["test_cases"][0]["id"]
        e["test_cases"].append(copy.deepcopy(e["test_cases"][0]))
        errs = self.vi.check_ids(self.g, self.d, e)
        self.assertIn(fail_line(self.vi.EVAL, dup_id, "duplicate test case ID"), errs)

    def test_bad_id_format_fails(self):
        g = copy.deepcopy(self.g)
        g["rules"][0]["id"] = "bad-rule-id"
        errs = self.vi.check_ids(g, self.d, self.e)
        self.assertIn(fail_line(self.vi.GUIDELINES, "bad-rule-id", "bad rule ID format"), errs)

    # ---------- required fields ----------

    def test_missing_id_field_is_reported_without_an_exception(self):
        g = copy.deepcopy(self.g)
        del g["rules"][0]["id"]
        try:
            errs = self.vi.check_ids(g, self.d, self.e)
        except Exception as exc:  # pragma: no cover - the test must fail clearly
            self.fail(f"check_ids raised an exception on a missing id field: {exc}")
        self.assertIn(fail_line(self.vi.GUIDELINES, "RULE-0", "missing required field id"), errs)

    def test_missing_required_field_fails(self):
        g = copy.deepcopy(self.g)
        del g["rules"][0]["id"]
        errs = self.vi.check_required_fields(g, self.d, self.e)
        self.assertIn(fail_line(self.vi.GUIDELINES, "RULE-0", "missing required field id"), errs)

    def test_missing_required_rule_field_other_than_id_fails(self):
        g = copy.deepcopy(self.g)
        rule_id = g["rules"][0]["id"]
        del g["rules"][0]["title"]
        errs = self.vi.check_required_fields(g, self.d, self.e)
        self.assertIn(fail_line(self.vi.GUIDELINES, rule_id, "missing required field title"), errs)

    def test_missing_required_fact_field_other_than_id_fails(self):
        g = copy.deepcopy(self.g)
        fact_id = g["facts"][0]["id"]
        del g["facts"][0]["topic"]
        errs = self.vi.check_required_fields(g, self.d, self.e)
        self.assertIn(fail_line(self.vi.GUIDELINES, fact_id, "missing required field topic"), errs)

    def test_missing_required_finding_field_fails(self):
        d = copy.deepcopy(self.d)
        finding_id = d["drafts"][0]["expected_findings"][0]["id"]
        del d["drafts"][0]["expected_findings"][0]["span_text"]
        errs = self.vi.check_required_fields(self.g, d, self.e)
        self.assertIn(fail_line(self.vi.DRAFTS, finding_id, "missing required field span_text"), errs)

    def test_missing_required_test_case_field_fails(self):
        e = copy.deepcopy(self.e)
        tc_id = e["test_cases"][0]["id"]
        del e["test_cases"][0]["expected"]
        errs = self.vi.check_required_fields(self.g, self.d, e)
        self.assertIn(fail_line(self.vi.EVAL, tc_id, "missing required field expected"), errs)

    def test_required_field_lists_match_the_real_data(self):
        derived = self.vi.derive_required_fields(self.g, self.d, self.e)
        for record_type, required_fields in self.vi.REQUIRED_FIELDS.items():
            self.assertEqual(
                set(derived[record_type]),
                set(required_fields),
                msg=f"required {record_type} fields drifted from the real data",
            )

    # ---------- Markdown ID coverage ----------

    def test_markdown_check_reports_every_missing_id(self):
        errs = self.vi.check_markdown_mentions_all_ids(
            self.g, self.d, self.e,
            guidelines_text="no ids here", drafts_text="no ids here", eval_text="no ids here",
        )
        rule_id = self.g["rules"][0]["id"]
        fact_id = self.g["facts"][0]["id"]
        draft_id = self.d["drafts"][0]["id"]
        finding_id = self.d["drafts"][0]["expected_findings"][0]["id"]
        tc_id = self.e["test_cases"][0]["id"]
        self.assertIn(fail_line("data/northstar-brand-guidelines.md", rule_id, "missing ID in markdown"), errs)
        self.assertIn(fail_line("data/northstar-brand-guidelines.md", fact_id, "missing ID in markdown"), errs)
        self.assertIn(fail_line("data/sample-drafts.md", draft_id, "missing ID in markdown"), errs)
        self.assertIn(fail_line("data/sample-drafts.md", finding_id, "missing ID in markdown"), errs)
        self.assertIn(fail_line("tests/evaluation-matrix.md", tc_id, "missing ID in markdown"), errs)

    def test_markdown_check_reports_only_the_last_rule_when_it_is_missing(self):
        rule_ids = [r["id"] for r in self.g["rules"]]
        fact_ids = [f["id"] for f in self.g["facts"]]
        text = " ".join(rule_ids[:-1] + fact_ids)
        errs = self.vi.check_markdown_mentions_all_ids(
            self.g, None, None, guidelines_text=text, drafts_text="", eval_text="",
        )
        self.assertEqual(errs, [fail_line("data/northstar-brand-guidelines.md", rule_ids[-1], "missing ID in markdown")])

    # ---------- references ----------

    def test_citation_id_does_not_exist_fails(self):
        e = copy.deepcopy(self.e)
        tc_id = e["test_cases"][0]["id"]
        e["test_cases"][0]["expected"]["rule_or_fact_id"] = "NS-DOES-NOT-EXIST"
        _, output = _run_main(self.vr, self.g, self.d, e)
        self.assertIn(fail_line(self.vr.EVAL, tc_id, "rule_or_fact_id NS-DOES-NOT-EXIST not in guidelines"), output)

    def test_alternate_citation_neither_rule_nor_fact_fails(self):
        e = copy.deepcopy(self.e)
        tc_id = e["test_cases"][0]["id"]
        e["test_cases"][0]["expected"]["acceptable_alternate_ids"] = ["NOPE-NEITHER"]
        _, output = _run_main(self.vr, self.g, self.d, e)
        self.assertIn(fail_line(self.vr.EVAL, tc_id, "alternate NOPE-NEITHER not in guidelines"), output)

    def test_superseded_by_unknown_fact_fails(self):
        g = copy.deepcopy(self.g)
        fact = next(f for f in g["facts"] if f.get("superseded_by") is not None)
        fact["superseded_by"] = "NS-FACT-999"
        _, output = _run_main(self.vr, g, self.d, self.e)
        self.assertIn(fail_line(self.vr.GUIDELINES, fact["id"], "superseded_by NS-FACT-999 not found"), output)

    # ---------- spans (Unicode code points, zero-based, end-exclusive) ----------

    def test_span_text_not_in_text_fails(self):
        d = copy.deepcopy(self.d)
        finding_id = d["drafts"][0]["expected_findings"][0]["id"]
        d["drafts"][0]["expected_findings"][0]["span_text"] = "ZZZNOTTHEREZZZ"
        _, output = _run_main(self.vs, self.g, d, self.e)
        self.assertIn(fail_line(self.vs.DRAFTS, finding_id, "text mismatch"), output)

    def test_span_text_occurring_twice_fails(self):
        d = copy.deepcopy(self.d)
        draft = d["drafts"][0]
        finding_id = draft["expected_findings"][0]["id"]
        draft["text"] = draft["text"] + " " + draft["expected_findings"][0]["span_text"]
        _, output = _run_main(self.vs, self.g, d, self.e)
        self.assertIn(fail_line(self.vs.DRAFTS, finding_id, "span appears 2 times"), output)

    def test_wrong_start_fails(self):
        d = copy.deepcopy(self.d)
        finding = d["drafts"][0]["expected_findings"][0]
        finding["start"] = finding["start"] + 1
        _, output = _run_main(self.vs, self.g, d, self.e)
        issues = ("text mismatch", "out of bounds")
        self.assertTrue(any(fail_line(self.vs.DRAFTS, finding["id"], issue) in output for issue in issues), output)

    def test_wrong_end_fails(self):
        d = copy.deepcopy(self.d)
        finding = d["drafts"][0]["expected_findings"][0]
        finding["end"] = finding["end"] - 1
        _, output = _run_main(self.vs, self.g, d, self.e)
        issues = ("text mismatch", "out of bounds", "end <= start")
        self.assertTrue(any(fail_line(self.vs.DRAFTS, finding["id"], issue) in output for issue in issues), output)

    def test_end_le_start_fails(self):
        d = copy.deepcopy(self.d)
        finding = d["drafts"][0]["expected_findings"][0]
        finding["end"] = finding["start"]
        _, output = _run_main(self.vs, self.g, d, self.e)
        self.assertIn(fail_line(self.vs.DRAFTS, finding["id"], "end <= start"), output)

    def test_emoji_case_ns_draft_09_add_two_to_start_and_end_fails(self):
        d = copy.deepcopy(self.d)
        draft = next(dr for dr in d["drafts"] if dr["id"] == "NS-DRAFT-09")
        finding = draft["expected_findings"][0]
        self.assertEqual(finding["id"], "NS-DRAFT-09-F1")
        finding["start"] = finding["start"] + 2
        finding["end"] = finding["end"] + 2
        _, output = _run_main(self.vs, self.g, d, self.e)
        self.assertIn(fail_line(self.vs.DRAFTS, "NS-DRAFT-09-F1", "text mismatch"), output)

    # ---------- enums and statuses ----------

    def test_invalid_expected_label_fails(self):
        d = copy.deepcopy(self.d)
        finding = d["drafts"][0]["expected_findings"][0]
        finding["expected_label"] = "badlabel"
        _, output = _run_main(self.ve, self.g, d, self.e)
        self.assertIn(fail_line(self.ve.DRAFTS, finding["id"], "bad label"), output)

    def test_invalid_severity_fails(self):
        d = copy.deepcopy(self.d)
        finding = d["drafts"][0]["expected_findings"][0]
        finding["severity"] = "critical"
        _, output = _run_main(self.ve, self.g, d, self.e)
        self.assertIn(fail_line(self.ve.DRAFTS, finding["id"], "bad sev"), output)

    def test_invalid_case_type_fails(self):
        e = copy.deepcopy(self.e)
        tc_id = e["test_cases"][0]["id"]
        e["test_cases"][0]["case_type"] = "weird"
        _, output = _run_main(self.ve, self.g, self.d, e)
        self.assertIn(fail_line(self.ve.EVAL, tc_id, "bad case_type"), output)

    def test_invalid_outcome_fails(self):
        e = copy.deepcopy(self.e)
        tc_id = e["test_cases"][0]["id"]
        e["test_cases"][0]["expected"]["outcome"] = "badoutcome"
        _, output = _run_main(self.ve, self.g, self.d, e)
        self.assertIn(fail_line(self.ve.EVAL, tc_id, "bad outcome"), output)

    def test_non_null_results_field_fails(self):
        e = copy.deepcopy(self.e)
        if not e.get("results_template"):
            self.skipTest("results_template is empty in the real data; nothing to mutate")
        record = e["results_template"][0]
        record["passed"] = True
        record_id = record.get("test_case_id") or "results_template"
        _, output = _run_main(self.ve, self.g, self.d, e)
        self.assertIn(fail_line(self.ve.EVAL, record_id, "results_template field passed not null"), output)

    def test_evaluation_as_of_date_mismatch_between_files_fails(self):
        e = copy.deepcopy(self.e)
        e["evaluation_as_of_date"] = "2026-01-01"
        _, output = _run_main(self.vd, self.g, self.d, e)
        self.assertIn("evaluation_as_of_date mismatch or wrong value", output)

    # ---------- fact validity, expiry and supersession ----------

    def test_stored_status_active_for_an_expired_fact_fails(self):
        g = copy.deepcopy(self.g)
        self._fact(g, "NS-FACT-003")["status_on_evaluation_date"] = "active"
        code, output = _run_main(self.ve, g, self.d, self.e)
        self.assertEqual(code, 1)
        self.assertIn(
            fail_line(self.ve.GUIDELINES, "NS-FACT-003", "status_on_evaluation_date is active but computed expired"),
            output,
        )

    def test_stored_status_active_for_a_superseded_fact_fails(self):
        g = copy.deepcopy(self.g)
        self._fact(g, "NS-FACT-010")["status_on_evaluation_date"] = "active"
        _, output = _run_main(self.ve, g, self.d, self.e)
        self.assertIn(
            fail_line(self.ve.GUIDELINES, "NS-FACT-010", "status_on_evaluation_date is active but computed superseded"),
            output,
        )

    def test_active_fact_with_a_past_expires_on_fails(self):
        g = copy.deepcopy(self.g)
        fact = next(f for f in g["facts"] if f["status_on_evaluation_date"] == "active" and f["superseded_by"] is None)
        fact["expires_on"] = "2026-01-01"
        _, output = _run_main(self.ve, g, self.d, self.e)
        self.assertIn(
            fail_line(self.ve.GUIDELINES, fact["id"], "status_on_evaluation_date is active but computed expired"),
            output,
        )

    def test_active_fact_with_a_future_valid_from_fails(self):
        g = copy.deepcopy(self.g)
        fact = next(f for f in g["facts"] if f["status_on_evaluation_date"] == "active" and f["superseded_by"] is None)
        fact["valid_from"] = "2099-01-01"
        _, output = _run_main(self.ve, g, self.d, self.e)
        self.assertIn(
            fail_line(self.ve.GUIDELINES, fact["id"], "status_on_evaluation_date is active but computed expired"),
            output,
        )

    def test_compute_fact_status_uses_expires_on_as_last_valid_day(self):
        from datetime import date
        eval_date = date(2026, 10, 23)
        base = {"superseded_by": None, "valid_from": "2026-01-01"}
        self.assertEqual(self.ve.compute_fact_status(dict(base, expires_on="2026-10-23"), eval_date), "active")
        self.assertEqual(self.ve.compute_fact_status(dict(base, expires_on="2026-10-22"), eval_date), "expired")
        self.assertEqual(self.ve.compute_fact_status(dict(base, expires_on=None), eval_date), "active")
        self.assertEqual(self.ve.compute_fact_status(dict(base, expires_on="2027-01-01", superseded_by="NS-FACT-002"), eval_date), "superseded")


if __name__ == "__main__":
    unittest.main()
