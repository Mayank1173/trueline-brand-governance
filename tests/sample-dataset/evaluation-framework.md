# Trueline Evaluation Framework

> **Status note:** This framework is a **proposed design**. No tests have been executed, no dataset exists yet, and **no scores are reported in this document**. All metric values are marked **PENDING** until real test runs produce evidence. Do not add numbers here until they come from an executed test run. Rule IDs and finding fields follow the proposed schema in `docs/rule-engine-spec.md`, which is pending confirmation from Mayank and Kushal. Dataset must come from Apurwa when available.

---

## 1. Purpose

This document defines **how we measure whether Trueline is doing a good job**. It covers:

- What we measure (metrics).
- How each metric is calculated (formulas).
- Where the numbers come from (labels and test runs).
- How to report results honestly.

It separates **automated metrics** (calculated by a script from labeled data) from **human judgments** (e.g., "is this suggested fix useful?"), which must not be blended into a single number.

---

## 2. Definitions used throughout

| Term | Meaning |
|---|---|
| **Draft** | One text submitted to Trueline for review. |
| **Finding** | One issue reported by Trueline (see finding schema). |
| **Expected finding** | A finding that a human labeler says *should* be reported for this draft. |
| **Predicted finding** | A finding that Trueline actually reported. |
| **True positive (TP)** | A predicted finding that matches an expected finding. |
| **False positive (FP)** | A predicted finding with no matching expected finding. |
| **False negative (FN)** | An expected finding that Trueline did not report. |
| **True negative (TN)** | A draft with no expected findings, correctly reported with no findings. |
| **Match** | A predicted finding and an expected finding are considered the *same issue*. |

### 2.1 What counts as a "match" (must be fixed before scoring)

Two findings match when **all** of the following hold:

1. Same `rule_id`.
2. Same `category`.
3. For a sentence-level annotation, a **positive overlap** between the predicted `[start_offset, end_offset)` and the annotated span. Missing, zero-length, adjacent, and disjoint spans do not match. Findings keep their precise word/pattern span; they are not widened to sentences.
4. Missing-content and length findings have no span. Match them at **draft/rule level** when both the prediction and annotation are spanless, rather than aligning them to an arbitrary sentence.

If a draft has multiple identical rules triggering at different positions, matches are assigned **one-to-one** (each predicted finding can match at most one expected finding, and vice versa). The matching procedure must be implemented as a script and stored with the results so it is reproducible. The backend helper implementation is documented in [`docs/evaluation-matching.md`](../../docs/evaluation-matching.md).

**This definition must be agreed with Mayank and Kushal before scores are calculated.** If the definition changes, old scores are invalid.

---

## 3. Metrics

Each metric below gives: **definition**, **formula**, **zero-denominator rule**, **source of labels**, and **current value (PENDING)**.

### 3.1 Finding precision

- **Question:** Of the findings we reported, how many were real?
- **Formula:**


- **Zero-denominator rule:** If `TP + FP = 0` (no findings predicted), precision is **not defined**. Report as `N/A`, not as 1.0 or 0.0. Record how many drafts produced this case.
- **Labels:** Human-labeled expected findings per draft.
- **Current value:** **PENDING**

---

### 3.2 Finding recall

- **Question:** Of the real issues, how many did we catch?
- **Formula:**


- **Zero-denominator rule:** If `TP + FN = 0` (no expected findings in the dataset), recall is **not defined**. Report as `N/A`. Record how many drafts produced this case.
- **Labels:** Human-labeled expected findings per draft.
- **Current value:** **PENDING**

---

### 3.3 False-positive rate

- **Question:** How often do we cry wolf?
- **Formula (per-draft rate, recommended):**


- **Alternative (per-finding rate):**


This equals `1 − Precision`. Choose one and state which was used. **Recommend the per-draft rate** because it reflects user experience.
- **Zero-denominator rule:** If no drafts were evaluated, report `N/A`.
- **Current value:** **PENDING**

---

### 3.4 Severity classification accuracy

- **Question:** When we flag an issue, do we assign the right severity?
- **Scope:** Only applied to **matched** findings (TPs). Unmatched findings have no expected severity.
- **Formula:**


- **Zero-denominator rule:** If there are no TPs, report `N/A`.
- **Optional breakdown:** Report accuracy per severity level (critical/high/medium/low/info) so a systematic bias is visible.
- **Current value:** **PENDING**

---

### 3.5 Citation validity rate

- **Question:** Do our findings point to real, relevant sources?
- **Formula:**


- **"Valid"** means: `source_reference` is non-null, `source_id` exists in the loaded guideline/fact library, `quoted_text` is present in that source, `source_version` matches the loaded source (including both being absent), and (for facts) the fact was valid on the run's `evaluation_date`.
- **Zero-denominator rule:** If there are no findings, report `N/A`.
- **Also report separately:** the count of findings rejected for a null or fabricated `source_reference` (this should be zero; if not, it is a critical defect).
- **Current value:** **PENDING**

---

### 3.6 Suggested-fix usefulness

- **Question:** When we suggest a correction, is it actually helpful?
- **This is a HUMAN judgment, not an automated metric.** Keep it separate.
- **Two sub-measures:**
1. **Fix presence rate** (automated):


2. **Fix usefulness rate** (human):
- A human reviewer labels each suggested fix as `useful`, `partially useful`, or `not useful`.
- Formula:


- **Zero-denominator rule:** Report `N/A` if no fixes were reviewed.
- **Rule:** The automated fix-presence rate and the human usefulness rate **must be reported separately** and never averaged together.
- **Current value:** **PENDING**

---

### 3.7 Correct detection of compliant drafts

- **Question:** When a draft is actually clean, do we correctly report no issues?
- **Formula:**


- **Labels:** Drafts that human labelers marked as compliant (no expected findings).
- **Zero-denominator rule:** If there are no compliant drafts, report `N/A`.
- **Current value:** **PENDING**

---

## 4. How to calculate metrics from test results

The procedure must be **reproducible**. A script (not manual counting) should produce every automated number.

### 4.1 Inputs required

1. **Labeled dataset** (from Apurwa): drafts + expected findings, each expected finding with `rule_id`, `category`, offsets (or null for missing-content), expected severity, and `source_reference`.
2. **Predicted findings**: the JSON output of a Trueline run over the same drafts, with the run's `evaluation_date`, ruleset version, and facts-library version recorded.
3. **Matching script**: implements §2.1 and outputs TP/FP/FN counts and per-metric results.

### 4.2 Steps

1. Load the dataset and predicted findings.
2. For each draft, match predicted findings to expected findings using §2.1.
3. Count TP, FP, FN per draft and in total.
4. Compute each automated metric using the formulas in §3.
5. Apply the zero-denominator rules and record `N/A` cases with counts.
6. Produce the report in the format of §6.
7. Store the script, its version, the dataset version, and the report together, so results can be reproduced.

### 4.3 What must never be done

- Never compute precision/recall on a dataset where expected findings were created **after** seeing Trueline's output (that inflates scores).
- Never drop drafts that produced `N/A` metrics without recording that they were dropped.
- Never report an average of precision and recall as a single "accuracy" number.
- Never mix human usefulness judgments into automated metric totals.

---

## 5. Handling empty and degenerate cases

| Situation | What to report |
|---|---|
| No findings predicted at all | Precision = `N/A`; record count of affected drafts |
| No expected findings at all | Recall = `N/A`; record count of affected drafts |
| Both empty | Both `N/A`; count as TN if the draft is labeled compliant |
| No TPs | Severity accuracy = `N/A` |
| No findings | Citation validity = `N/A` |
| No fixes reviewed | Fix usefulness = `N/A` |

`N/A` is never treated as a pass, a fail, or a zero. It is reported as `N/A` with the reason.

---

## 6. Recommended evaluation report format

Each evaluation run produces one report with the following sections. **All values below are PENDING — fill them only after a real run.**


If there is no previous run, the regression section states "No previous run."

---

## 7. Known limitations (must appear in every report)

These limitations are inherent to this framework and must be stated honestly in every evaluation report:

1. **Labeled data is finite and human-labeled.** Results generalize only as far as the dataset does.
2. **Matching depends on the §2.1 definition.** If the definition changes, scores are not comparable.
3. **Precision and recall are reported separately.** No single "accuracy" number is used.
4. **Human usefulness judgments are subjective** and must be reported with the number of reviewers and the rubric used.
5. **Deterministic and heuristic rules are mixed in the finding set.** A per-category breakdown must accompany headline numbers so a weak heuristic does not hide behind a strong deterministic rule.
6. **The framework measures detection, not correctness of the underlying guideline.** If a guideline is wrong, Trueline can score well while still being wrong.
7. **Claims that are silently passed** (not detected as claims) are invisible to these metrics unless the dataset includes such cases.
8. **No visual/accessibility metrics are included here.** Those are covered separately in `docs/accessibility-validation.md`.

---

## 8. Separation of automated metrics and human judgments

| Metric | Type | Reported in |
|---|---|---|
| Precision | Automated | Metrics section |
| Recall | Automated | Metrics section |
| False-positive rate | Automated | Metrics section |
| Severity accuracy | Automated | Metrics section |
| Citation validity rate | Automated | Metrics section |
| Fix presence rate | Automated | Metrics section |
| Fix usefulness rate | **Human** | Separate human-judgment subsection with reviewer count and rubric |
| Compliant-draft accuracy | Automated | Metrics section |

The human-judgment subsection must not be merged into the automated totals. If a summary is required, show both side by side without combining them.

---

## 9. Status of this document

- **Design:** Proposed; matching definition (§2.1) and report format (§6) pending agreement with Mayank, Kushal, and Apurwa.
- **Data:** None. No labeled dataset exists yet.
- **Execution:** None. No test runs performed.
- **Results:** None. Every metric value is **PENDING**. Do not replace `PENDING` with a number until the number comes from an executed run with a recorded dataset, engine, ruleset, and facts-library version.
- 
