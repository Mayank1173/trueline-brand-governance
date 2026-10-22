# Accessibility and Visual Validation Plan — Trueline

> **Status note:** This is a **plan**, not an implementation. No accessibility or visual checks exist in the codebase yet. Nothing in this document has been tested. Every check below is marked **NOT IMPLEMENTED** unless explicitly stated otherwise. Do not claim any visual or accessibility feature works until it has been implemented and tested with recorded evidence.
>
> **Scope note:** The Trueline MVP primarily reviews **text and documents**. Most visual checks require inputs (color values, image files, metadata) that the MVP may not receive. This document separates realistic MVP checks from optional and future checks.

---

## 1. Purpose

This document plans how Trueline will validate **visual and accessibility aspects** of marketing drafts. It covers:

- What can realistically be checked in the MVP.
- What requires additional input before it can be checked.
- What is a future capability and must not be claimed now.
- How color contrast is calculated and which WCAG thresholds apply.
- What automated checks can and cannot prove.

---

## 2. Important limitation (must be stated to users)

**Automated checks cannot establish complete accessibility compliance.**

- A passing contrast check does not mean the document is accessible.
- A missing alt-text check only works when image metadata is available.
- Heading-structure checks detect structural issues, not whether the heading text makes sense.
- Automated tools miss many WCAG success criteria entirely (e.g., meaningful sequence, sensory characteristics, cognitive load).

Any user-facing message about accessibility must say this clearly. Trueline reports **potential issues**, not a compliance certificate.

---

## 3. MVP checks (realistic now, text-based)

These checks can be performed on text input without image files or rendering. They are the only accessibility-related checks planned for the MVP.

All checks below are **NOT IMPLEMENTED**.

### 3.1 Text contrast ratio (when color values are provided)

- **Input required:** foreground color and background color, as explicit values (hex, RGB, or named CSS colors) supplied in the draft metadata or request payload.
- **Not supported:** inferring colors from a rendered screenshot or from styled HTML without parsed color values.
- **Calculation method:** WCAG 2.x relative luminance and contrast ratio.



- **WCAG thresholds (WCAG 2.1 / 2.2):**
- **Normal text:** minimum **4.5:1** (Level AA); enhanced **7:1** (Level AAA).
- **Large text** (≥ 18pt regular, or ≥ 14pt bold): minimum **3:1** (AA); enhanced **4.5:1** (AAA).
- **Non-text UI components and graphical objects** (e.g., icons, form borders): minimum **3:1** (AA, WCAG 1.4.11).
- **Output:** a finding with `category = "contrast"` (proposed; must be added to the category enum after confirmation), the calculated ratio, the threshold applied, and the pass/fail result against that threshold.
- **Edge cases:**
- Missing one of the two colors → cannot compute; report as "insufficient input", not as a pass.
- Invalid color value → reject with a clear error.
- Alpha/transparency → document behavior; recommend rejecting transparent colors in the MVP rather than guessing the composited result.
- Named colors → must be resolved via a fixed, versioned color table.
- **Deterministic?** Yes, given valid color inputs.
- **Limitation:** A ratio above the threshold does not guarantee readability in context (font size, weight, rendering).

### 3.2 Missing or invalid color values

- **Input required:** color values in the draft metadata or request payload.
- **Logic:** if a color field is present but empty, malformed, or not a recognized format, flag it.
- **Output:** finding stating which field was invalid and why.
- **Edge cases:** shorthand hex (`#fff`), uppercase/lowercase hex, `rgb()` vs `rgba()`, named colors.
- **Deterministic?** Yes.
- **Limitation:** This checks format validity, not design quality.

### 3.3 Presence of text that depends only on color

- **Input required:** structured draft metadata that marks spans as color-only emphasis (e.g., "this span is red to indicate an error"). Free text alone cannot support this check.
- **Logic:** flag spans that are marked as conveying meaning through color alone (WCAG 1.4.1, "Use of Color").
- **Output:** finding with the span and an explanation.
- **Edge cases:** color used purely decoratively should not be flagged; the distinction must come from the input metadata, not from guessing.
- **Deterministic?** Yes for explicitly marked spans. **Not possible** from plain text.
- **Limitation:** If the input does not mark color-only meaning, this check cannot run.

### 3.4 Basic heading structure

- **Input required:** text with heading markup (Markdown `#`, `##`, or structured heading metadata). Plain text with no structure cannot be checked reliably.
- **Logic:** detect skipped heading levels (e.g., `#` followed by `###` with no `##`), multiple top-level headings where only one is expected, and empty headings.
- **Output:** finding per structural issue, with line or offset reference.
- **Edge cases:** documents that intentionally start at `##` (embedded content) — must be configurable; headings inside code blocks must be excluded.
- **Deterministic?** Yes for markup-based input. **Not reliable** for plain text.
- **Limitation:** Detects structure problems, not whether headings describe their sections.

### 3.5 Descriptive link text

- **Input required:** text with link markup (Markdown `[text](url)` or structured link metadata).
- **Logic:** flag link text that is empty, or matches a configured list of non-descriptive phrases (e.g., "click here", "read more", "here"). The list must be configurable and documented.
- **Output:** finding per flagged link with the link text and a suggested improvement direction (not a fabricated replacement).
- **Edge cases:** link text that is non-descriptive but accompanied by surrounding context — still flag, with `requires_human_review = true`; images used as links (see §4.2).
- **Deterministic?** Yes for empty text and configured phrase list. Judging whether a link is *meaningful* in context is heuristic → `requires_human_review = true`.
- **Limitation:** A link not on the configured list may still be non-descriptive.

### 3.6 Missing alternative text (when image metadata is available)

- **Input required:** image metadata that includes the `alt` attribute value (or its absence) alongside the image reference.
- **Logic:** flag images whose `alt` field is missing or empty.
- **Output:** finding per image, referencing the image identifier.
- **Edge cases:** decorative images legitimately have empty `alt` — this must be marked as intentional in the input, otherwise flag for review; alt text that merely repeats a filename should be flagged as low quality (heuristic).
- **Deterministic?** Detection of missing/empty `alt` is deterministic. Judging alt-text *quality* is heuristic.
- **Limitation:** **Not possible from plain text.** Requires image metadata; not an image-recognition feature.

---

## 4. Optional checks (require additional input)

These checks are only possible if the team decides to accept the required inputs. They are **NOT IMPLEMENTED** and are not part of the MVP by default.

### 4.1 Brand palette compliance

- **Input required:** brand palette definition (list of approved color values with names and allowed usage) plus the colors used in the draft.
- **Logic:** compare used colors to the approved palette; flag off-palette colors.
- **Output:** finding naming the used color, the nearest approved color (if any), and the palette rule.
- **Edge cases:** anti-aliasing and transparency produce intermediate colors not in the palette; the MVP must not attempt to correct for this.
- **Deterministic?** Yes for exact color matching. "Nearest palette color" is heuristic and must be marked as such.
- **Status:** NOT IMPLEMENTED; requires brand palette data from Apurwa.

### 4.2 Image/logo checks (where metadata or files are available)

- **Input required:** image files plus metadata (dimensions, format, declared logo identity) or a logo reference set.
- **Logic (only if implemented):** check declared dimensions against a configured minimum, check file format against an allowed list, check that a declared logo matches a reference by exact file hash (not by visual recognition).
- **What is NOT planned:** visual logo recognition, image-content classification, or brand-compliance judgment of image content. These require a vision model and are **future capabilities**, not MVP.
- **Deterministic?** File-hash and dimension/format checks are deterministic. Visual matching is not implemented.
- **Status:** NOT IMPLEMENTED.

### 4.3 Image format and size metadata

- **Input required:** image metadata.
- **Logic:** flag unsupported formats or images below configured minimum dimensions.
- **Output:** finding per image.
- **Deterministic?** Yes.
- **Status:** NOT IMPLEMENTED; requires an image-processing library decision (see §6).

---

## 5. Future visual-analysis capabilities (explicitly not now)

The following are **future possibilities only**. They must not be described to users or in demos as working, and must not appear in the MVP acceptance criteria:

- Visual logo recognition in images.
- Detection of brand colors in a rendered design (as opposed to declared color values).
- OCR-based contrast or readability assessment of screenshots.
- Judgment of whether imagery is on-brand or appropriate.
- Automated WCAG conformance certification of any kind.

If the team later decides to pursue any of these, they require a new spec, new tests, and new evaluation metrics. None of that exists today.

---

## 6. Image-processing library considerations (decision pending)

If optional checks in §4 are pursued, an image-processing library will be needed. This is a **decision for the developers**, not a recommendation to adopt now.

- **Pillow (PIL):** well-suited for reading image files, dimensions, format, and metadata. Simple and widely used. Does not perform recognition or classification.
- **OpenCV:** heavier; useful if future work requires computer vision. Not needed for metadata checks.

**Rule:** Do not claim Pillow or OpenCV is "in use" until the developers have added it to the backend and a test confirms it. This document records the option, not the decision.

---

## 7. Separation of check categories (must be preserved in the UI and in reports)

| Check | Category | Requires extra input? | Status |
|---|---|---|---|
| Text contrast ratio | MVP | Yes — color values | NOT IMPLEMENTED |
| Missing/invalid color values | MVP | Yes — color values | NOT IMPLEMENTED |
| Color-only meaning | MVP | Yes — marked spans | NOT IMPLEMENTED |
| Heading structure | MVP | Yes — heading markup | NOT IMPLEMENTED |
| Descriptive link text | MVP | Yes — link markup | NOT IMPLEMENTED |
| Missing alt text | MVP (conditional) | Yes — image metadata | NOT IMPLEMENTED |
| Brand palette compliance | Optional | Yes — palette data | NOT IMPLEMENTED |
| Image/logo metadata checks | Optional | Yes — image files/metadata | NOT IMPLEMENTED |
| Visual logo recognition | Future | Yes — vision model | NOT PLANNED |

The UI must not mix "not checked because input was missing" with "checked and passed". These are different outcomes and must be displayed differently.

---

## 8. Proposed test cases for this plan (all Not Run)

These will be added to `tests/test-cases.md` under a new category once the schema is confirmed. They are listed here so the plan is testable. **All are Not Run; none has been executed.**

| ID | Purpose | Status |
|---|---|---|
| TC-V-001 | Contrast ratio computed correctly for a known color pair (compare against a hand-calculated value) | Not Run |
| TC-V-002 | Contrast finding applies the correct AA threshold for normal vs large text | Not Run |
| TC-V-003 | Missing background color produces "insufficient input", not a pass | Not Run |
| TC-V-004 | Invalid color value is rejected with a clear error | Not Run |
| TC-V-005 | Transparent color behavior matches the documented rule | Not Run |
| TC-V-006 | Color-only meaning flagged only when marked in metadata | Not Run |
| TC-V-007 | Skipped heading level detected | Not Run |
| TC-V-008 | Heading inside code block is not treated as a heading | Not Run |
| TC-V-009 | Non-descriptive link text from configured list is flagged | Not Run |
| TC-V-010 | Link text not on the list is not flagged (known limitation recorded) | Not Run |
| TC-V-011 | Missing alt text flagged when metadata is present | Not Run |
| TC-V-012 | Decorative image with intentional empty alt is not flagged | Not Run |
| TC-V-013 | When image metadata is absent, check reports "not checked", not "passed" | Not Run |
| TC-V-014 | No accessibility feature is reported as working when unimplemented | Not Run |

---

## 9. Reporting rules for accessibility findings

- Every accessibility finding must say **which input was required** and **whether it was present**.
- A check that could not run because input was missing must be reported as **"Not checked"**, never as **"Passed"**.
- Contrast findings must include the calculated ratio and the threshold applied, so the user can verify the result.
- No user-facing text may describe Trueline as making a document "accessible" or "compliant". The wording must be "potential accessibility issue detected" or "could not be checked".

---

## 10. Status of this document

- **Design:** Proposed plan.
- **Implementation:** None. No accessibility or visual check exists in the codebase.
- **Execution:** None. All test cases in §8 are **Not Run**.
- **Results:** None measured. Do not report any accessibility coverage percentage or compliance result until checks are implemented and tests are executed with evidence.
- **Decisions pending:** category enum extension for accessibility findings (with Mayank/Kushal); brand palette data (with Apurwa); whether optional checks in §4 are in scope at all.
