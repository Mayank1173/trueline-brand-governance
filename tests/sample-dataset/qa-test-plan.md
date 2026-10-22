# Trueline QA Test Plan

> **Status note:** This is the **overall QA plan** for the Trueline MVP. It explains *how* we test, *what* we test, and *when* a test may be marked passed. The detailed test cases live in `tests/test-cases.md`. This document does **not** contain test results. No test has been executed. Nothing here should be read as evidence that any part of Trueline works.
>
> **Schema note:** Rule IDs, finding fields, and severity levels follow the proposed schema in `docs/rule-engine-spec.md`, which is pending confirmation from Mayank and Kushal. If the schema changes, this plan and the test cases must be updated together.

---

## 1. Purpose

This plan defines the QA approach for the Trueline MVP so that:

- Testing is **consistent** across testers.
- Every test is **traceable** to a requirement or spec section.
- Results are **honest and reproducible**.
- The team knows **what is in scope**, **what is out of scope**, and **what is blocked** waiting on decisions.

It is written for a beginner-friendly audience but is technically precise enough for the developers to act on.

---

## 2. Scope

### 2.1 In scope for the MVP

- Deterministic brand-rule checks (banned terms, preferred terms, required phrases, product names, formatting, missing content, length limits).
- Approved-fact matching and citation validity.
- Expired or missing fact metadata.
- Suggested fixes and the recheck flow, as far as Intent Lock requirements are agreed.
- Review and audit workflow (approve, reject, request changes, revision history, permissions).
- Reliability and error handling for the engine and API.
- Basic text-based accessibility checks that require supplied inputs (color values, heading markup, link markup, image metadata) — **only if** these are implemented.

### 2.2 Out of scope for the MVP

- Visual logo recognition, image-content classification, and any vision-model feature.
- Automated accessibility compliance certification.
- OCR from screenshots.
- Performance and load testing at scale (a separate plan is needed if the MVP must handle production load).
- Security penetration testing (separate plan).
- Data migration or legacy import testing.

### 2.3 Explicitly not claimable

No test in this plan may be used to claim that Trueline is "production ready", "secure", "accessible", or "compliant". The plan measures correctness of specified behavior only.

---

## 3. Test levels

| Level | What it checks | Who runs it (proposed) | Depends on |
|---|---|---|---|
| **Unit** | One function or rule in isolation (e.g., banned-term matcher, contrast calculator) | Developer + QA review | Code exists |
| **Integration** | Engine + ruleset + facts library together | QA / developer | Code and data exist |
| **API** | Request/response behavior, validation, error handling | QA / developer | API running |
| **Workflow** | Review, approval, audit, permissions end-to-end | QA | API and frontend running |
| **Evaluation** | Quality metrics over a labeled dataset | QA + Apurwa | Labeled dataset and a running engine |
| **Regression** | Smoke subset after each change | Whoever made the change | A previously passing baseline |

Each test case in `tests/test-cases.md` must declare which level it belongs to once the developers confirm the test framework. Until then, the level is **"Unassigned"** and recorded in the test case.

---

## 4. Test environment requirements

To move any test from **Not Run** to a real status, the following must exist:

1. **A running backend** that accepts a draft and returns findings in the agreed schema.
2. **A loaded ruleset** with a version identifier.
3. **A loaded facts library** with a version identifier.
4. **An explicit `evaluation_date`** supplied per run (source pending decision — see `docs/rule-engine-spec.md` §7).
5. **A test harness or script** that can submit drafts and capture findings as JSON.
6. **A schema validator** matching the agreed finding schema.
7. **A labeled dataset** from Apurwa for evaluation tests.
8. **A place to record evidence** (logs, screenshots, JSON outputs) linked from each test case.

If any of these is missing, the affected tests are **Blocked**, not **Failed**.

---

## 5. Entry and exit criteria

### 5.1 Entry criteria (before any test execution begins)

- [ ] Finding schema confirmed by Mayank and Kushal.
- [ ] Rule ID convention confirmed.
- [ ] Backend running and reachable.
- [ ] Ruleset and facts library loaded with recorded versions.
- [ ] `evaluation_date` source decided.
- [ ] Test cases in `tests/test-cases.md` reviewed and IDs stable.
- [ ] Evidence storage location agreed.

All items **Not done** at the time this plan was written.

### 5.2 Exit criteria (before the MVP can be called tested)

- [ ] All P0 tests executed and passed, with evidence linked.
- [ ] All P1 tests executed; any failures triaged into bugs with severity and priority.
- [ ] No open Critical bug.
- [ ] Evaluation report produced with all metrics either measured or explicitly `N/A` with reasons.
- [ ] Accessibility checks either implemented and tested, or clearly reported as "not checked".
- [ ] Regression checklist run after the final change, with a recorded run block.

These are **criteria**, not current status. None is met today.

---

## 6. Test data strategy

| Data type | Source | Notes |
|---|---|---|
| Brand guidelines (rules) | Apurwa | Must be versioned. Placeholder rules must not be mixed with real ones in the same run. |
| Approved facts library | Apurwa | Must include valid, expired, and metadata-incomplete facts for coverage. |
| Sample drafts | Apurwa | Must include compliant drafts, drafts with known violations, and edge cases (empty, very long, Unicode). |
| Labeled expected findings | Apurwa + QA | Must be created **without** looking at Trueline's output first, to avoid biasing scores. |
| Machine-readable fixtures | Developers + QA | `tests/fixtures/rule-engine-cases.json` is proposed; not created yet. |

**Rule:** Do not invent brand rules or facts for testing if Apurwa's dataset is available or imminent. Placeholder data, when unavoidable, must be marked as placeholder in every test case and report that uses it.

---

## 7. Test execution process

1. Confirm entry criteria (§5.1).
2. Pick a test case from `tests/test-cases.md` in priority order (P0 first).
3. Set up the environment exactly as the test case specifies.
4. Submit the specified input.
5. Capture the actual output as evidence (JSON, log, screenshot).
6. Compare actual vs expected.
7. Update **only that test case** with status (Pass / Fail / Blocked), evidence link, run date, and version identifiers.
8. If Fail, create a bug report using `tests/bug-report-template.md` and link it from the test case.
9. If Blocked, record the missing dependency.
10. Do not bulk-update other tests. Do not mark a test Pass without evidence.

---

## 8. Result recording rules (non-negotiable)

- **No test is Pass without evidence.** Evidence means a captured output, log, or screenshot, linked from the test case.
- **No test is marked Pass because "it looks fine".**
- **No metric is reported without its denominator.** Precision, recall, and other metrics must show the counts used to compute them (see `tests/evaluation-framework.md`).
- **`N/A` is not a pass.** When a metric or test cannot be evaluated, report `N/A` or `Blocked` with the reason.
- **Do not reword an expected result to match observed behavior.** If the expected result was wrong, update the spec first, get agreement, then update the test.
- **Do not copy results between environments.** A pass on local is not a pass on staging unless the test case says so.

---

## 9. Defect management

- Bugs are logged using `tests/bug-report-template.md`.
- Severity and priority are assigned per the definitions in that template.
- A failed P0 test with a Critical severity bug blocks the MVP exit criteria.
- Every bug must reference at least one related test case or be marked "exploratory".
- Bugs are closed only after the fix is verified by re-running the related test with evidence.

---

## 10. Traceability

Every test case must trace to one of:

- A rule type in `docs/rule-engine-spec.md`.
- A workflow requirement agreed with the team.
- An accessibility check in `docs/accessibility-validation.md`.
- A reliability requirement in §2.1 of this plan.

If a test case cannot be traced to any of these, it must be removed or the missing requirement must be added first. Traceability IDs are maintained in `tests/test-cases.md` (to be added once the schema is confirmed).

---

## 11. Risks and dependencies

| Risk | Impact | Mitigation |
|---|---|---|
| Schema not confirmed | Blocks many tests; results invalid if schema changes later | Confirm schema before executing; freeze it per run |
| Dataset from Apurwa not ready | Category A and B tests cannot run meaningfully | Use clearly marked placeholders only; do not score against placeholders |
| Intent Lock requirements undefined | TC-C-003 and TC-C-010 cannot be finalized | Do not claim Intent Lock is tested until requirements exist |
| No `evaluation_date` source decided | Expiry tests cannot run consistently | Decide source before running TC-B-004/TC-B-005/TC-B-014 |
| Accessibility inputs not supplied | Visual checks cannot run | Report "not checked", never "passed" |
| Pressure to mark tests passed without evidence | Dishonest reporting; hides real defects | Enforce §8 rules; require evidence links |

---

## 12. Roles (proposed)

| Role | Person (proposed) | Responsibility |
|---|---|---|
| QA owner | Vandana | Maintains test plan and test cases, records results, files bugs |
| Schema owner | Mayank / Kushal | Confirms finding schema and API behavior |
| Data owner | Apurwa | Provides rules, facts, drafts, and labels |
| Bug triage | Team lead | Assigns severity/priority, decides exit |

Roles must be confirmed by the team; this table is a proposal.

---

## 13. Reporting cadence (proposed)

- **Per test run:** update the affected test cases and the evaluation report (if applicable).
- **Per change to engine/API/workflow/prompts:** run the regression checklist in `tests/bug-report-template.md` §5 and record the run block.
- **Milestone summary:** count of tests by status (Pass/Fail/Blocked/Not Run), open bugs by severity, and evaluation metrics with denominators. **Pending** until the first run.

---

## 14. Status of this document

- **Design:** Proposed QA plan; entry and exit criteria are targets, not current state.
- **Execution:** None. No test in this plan has been run.
- **Results:** None. No pass/fail counts, coverage percentages, or metrics exist yet. Do not add them until they come from executed tests with evidence.
- **Open decisions:** schema confirmation, rule ID convention, `evaluation_date` source, Intent Lock requirements, review permission model, dataset availability, evidence storage location.

Trigger PR for QA deliverables
