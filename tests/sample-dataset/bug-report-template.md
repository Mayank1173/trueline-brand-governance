# Bug Report Template and Regression Checklist — Trueline

> **Status note:** This is a **template and process document**. It does not describe any bug that currently exists. No bugs have been logged yet because no running system exists. Severity definitions below are **proposals** pending agreement with Mayank, Kushal, and the team lead.
>
> **Honesty rule:** Do not create a bug report with fabricated steps, screenshots, or logs. If you cannot reproduce a bug, say so in the report. If evidence is unavailable, write "No evidence captured" instead of inventing one.

---

## 1. Purpose

This document provides:

- A lightweight bug-report template (copy-paste ready).
- Severity and priority definitions so the team distinguishes critical workflow failures from cosmetic issues.
- A regression checklist to run after changes to the rules engine, API, review workflow, or AI prompts.

---

## 2. Bug report template (copy this for each new bug)


---

## 3. Severity definitions (proposed)

Severity describes **impact**. It does not describe how urgent the fix is (that is priority).

| Severity | Definition | Examples |
|---|---|---|
| **Critical** | A core workflow is broken, data is corrupted or lost, or the system silently gives a wrong pass on a compliance check. | Approval recorded against the wrong draft version; a finding shown with a fabricated `source_reference`; engine returns "no findings" when the ruleset failed to load. |
| **High** | A major feature produces wrong results, but the system does not lose data or silently pass unsafe content. | Banned phrase missed at a specific position; expired fact treated as valid; suggested fix alters unrelated text. |
| **Medium** | A feature works partially or a non-core path is broken; workaround exists. | Heading-structure check misses a skipped level; contrast finding uses the wrong threshold for large text. |
| **Low** | Cosmetic or minor issue with no functional impact on review outcomes. | Finding explanation has a typo; severity label displayed in the wrong color. |

**Rule:** If unsure between Critical and High, ask: *"Can this cause an unsafe draft to be approved, or can it lose audit data?"* If yes → Critical.

---

## 4. Priority definitions (proposed)

Priority describes **when to fix**.

| Priority | Meaning |
|---|---|
| **P0** | Fix immediately; blocks MVP or blocks other work. |
| **P1** | Fix in the current milestone. |
| **P2** | Fix before release if possible; not blocking MVP. |
| **P3** | Fix when convenient; nice to have. |

Severity and priority are set independently. A Critical bug is normally P0, but a Low-severity cosmetic bug can be P0 if it blocks a demo.

---

## 5. Regression checklist

Run this checklist **after any change** to the rules engine, API, review workflow, or AI prompts. It is a quick smoke check; it does not replace the full test plan in `tests/test-cases.md`.

All items below are **Not Run** until actually executed. Do not mark an item "Pass" without evidence.

### 5.1 Rule engine changes

- [ ] Banned-term detection still fires on a known input (TC-A-001) — **Not Run**
- [ ] Word-boundary guard still prevents substring false positives (TC-A-003) — **Not Run**
- [ ] Missing required phrase still produces a null-offset finding (TC-A-009) — **Not Run**
- [ ] Every finding still carries a valid `rule_id` (TC-A-018) — **Not Run**
- [ ] Deterministic output is identical across two runs of the same input (TC-E-015) — **Not Run**
- [ ] Offsets still index correctly into the submitted text (TC-E-012) — **Not Run**
- [ ] Engine still fails closed when the ruleset is missing (TC-E-005) — **Not Run**

### 5.2 Approved facts and citations

- [ ] Supported claim still matches its fact (TC-B-001) — **Not Run**
- [ ] Expired fact is still rejected as support (TC-B-004) — **Not Run**
- [ ] Every finding still has a non-null `source_reference` (TC-B-008) — **Not Run**
- [ ] Fabricated source reference is still rejected or flagged (TC-B-009) — **Not Run**

### 5.3 API changes

- [ ] Findings output still validates against the agreed schema (TC-E-014) — **Not Run**
- [ ] Malformed input payloads are still rejected with a validation error (TC-E-007) — **Not Run**
- [ ] Empty draft still returns the documented info finding, no crash (TC-E-001) — **Not Run**
- [ ] AI service failure still leaves deterministic findings intact (TC-E-009) — **Not Run**

### 5.4 Review workflow changes

- [ ] Authorized reviewer can still approve (TC-D-001) — **Not Run**
- [ ] Unauthorized user is still blocked from approving (TC-D-003) — **Not Run**
- [ ] Approval is still bound to the correct draft version (TC-D-005) — **Not Run**
- [ ] Post-approval edits are still handled per the agreed workflow (TC-D-006) — **Not Run**

### 5.5 AI prompt changes

- [ ] Deterministic findings are unchanged by prompt edits (run TC-E-015) — **Not Run**
- [ ] AI-dependent findings still carry `requires_human_review = true` where the spec requires it (TC-B-002, TC-B-013) — **Not Run**
- [ ] No new finding appears without a `source_reference` (TC-B-008) — **Not Run**
- [ ] Suggested fixes are still scoped to the targeted span (TC-C-002) — **Not Run**

### 5.6 Accessibility checks (once implemented)

- [ ] Contrast ratio matches the hand-calculated value for a known color pair (TC-V-001) — **Not Run**
- [ ] Missing input reports "not checked", never "passed" (TC-V-013, TC-V-014) — **Not Run**

---

## 6. How to record a regression run

When the checklist is actually run, add a short block to the change's pull request or to the team log:


Do not mark the checklist "passed" as a whole. Report each item or at least each section with its result. If an item could not be run, mark it **Blocked** with the reason.

---

## 7. Status of this document

- **Design:** Proposed template and process; severity and priority definitions pending team agreement.
- **Bugs logged:** None. No running system exists to produce bugs.
- **Regression runs:** None performed.
- **Results:** None measured. Do not cite this checklist as evidence that regressions were tested until a run is recorded with the block in §6.
