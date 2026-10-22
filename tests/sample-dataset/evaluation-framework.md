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
2. Overlapping text span: the predicted `[start_offset, end_offset)` overlaps the expected span, **or** both spans are `null` (missing-content findings).
3. Same `category`.

If a draft has multiple identical rules triggering at different positions, matches are assigned **one-to-one** (each predicted finding can match at most one expected finding, and vice versa). The matching procedure must be implemented as a script and stored with the results so it is reproducible.

**This definition must be agreed with Mayank and Kushal before scores are calculated.** If the definition changes, old scores are invalid.

---

## 3. Metrics

Each metric below gives: **definition**, **formula**, **zero-denominator rule**, **source of labels**, and **current value (PENDING)**.

### 3.1 Finding precision

- **Question:** Of the findings we reported, how many were real?
- **Formula:**
