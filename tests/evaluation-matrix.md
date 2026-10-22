# Northstar Evaluation Matrix

> FICTIONAL TEST DATA — NOT A REAL COMPANY. Northstar Planner is an invented brand. Every name, product, price, policy, owner role, and fact in this pack is invented for software testing and describes no real company, product, or person. Do not publish this content or present it as real.

Status: test plan only. No results have been measured.

## 1. Purpose and how to use it

This matrix is a test plan for checking whether a brand-guideline review tool finds the expected issues in fictional Northstar Planner content. Each row is one input and one expected result. Run the input once, compare the tool's findings with the expected result, and record the outcome in the results template. The matrix is not evidence that any feature works and contains no measured scores.

The dataset is text-only and intentionally small. Use it to make test runs repeatable, not to estimate production accuracy.

## 2. Fixed evaluation date

The fixed evaluation date is **2026-10-23**. All fact status, expiry, supersession, and offer checks must use this date. Tests must not read the system clock to decide whether a fact is active, expired, or superseded.

## 3. Evaluation matrix

| Test ID | Type | Input | Expected rule or fact | Expected finding | Expected citation | Expected severity | Expected suggested fix | Expected outcome |
|---|---|---|---|---|---|---|---|---|
| NS-TC-001 | positive | NS-DRAFT-01 | NS-BAN-001 | "Revolutionary" is a banned hype word in the Northstar guideline pack. | NS-DOC-EDITORIAL section 5.1 Banned hype words | medium | Replace it with a plain description of what the product helps the team do. | finding |
| NS-TC-002 | positive | NS-DRAFT-01 | NS-BAN-001 | "Game-changing" is also a banned hype word and adds no concrete information. | NS-DOC-EDITORIAL section 5.1 Banned hype words | medium | Remove it and describe the benefit directly. | finding |
| NS-TC-003 | positive | NS-DRAFT-01 | NS-TERM-001 | The preferred term is "team members" in customer-facing copy. | NS-DOC-NAMING section 4.1 People | low | Replace "users" with "team members". | finding |
| NS-TC-004 | positive | NS-DRAFT-01 | NS-BAN-002 | "Synergy" is discouraged jargon and makes the sentence less clear. | NS-DOC-EDITORIAL section 5.2 Discouraged jargon | low | Replace it with a plain description such as "plan work together". | finding |
| NS-TC-005 | positive | NS-DRAFT-02 | NS-TONE-003 | The opening uses humour, slang, and an emoji in a serious sign-in notice, and it does not clearly state what happened, who was affected, or what was done. | NS-DOC-VOICE section 2.3 Serious notices | high | Rewrite as a factual notice with the time window, affected group, and resolution, without jokes or emoji. | finding |
| NS-TC-006 | positive | NS-DRAFT-02 | NS-TONE-003 | This sentence is vague about who was affected and for how long, so readers cannot tell the scope of the incident. | NS-DOC-VOICE section 2.3 Serious notices | medium | Name the affected group and the time window, and state that the issue is fixed. | finding |
| NS-TC-007 | positive | NS-DRAFT-03 | NS-REQ-001 | The post states a price but omits the required sentence "Prices exclude applicable taxes." | NS-DOC-EDITORIAL section 6.1 Price disclosure | medium | Add the exact sentence after the price: "Prices exclude applicable taxes." | finding |
| NS-TC-008 | positive | NS-DRAFT-04 | NS-CLAIM-001 | The superlative "fastest ... on the market" is an unsupported market-position claim; no approved fact supports it. | NS-DOC-CLAIMS section 3.1 Superlatives | high | Remove the ranking and describe the planning benefit in plain language. | finding |
| NS-TC-009 | positive | NS-DRAFT-04 | NS-CLAIM-002 | The "10 hours every week" claim is a numeric productivity claim with no approved fact behind it. | NS-DOC-CLAIMS section 3.2 Performance claims | high | Remove the number and describe the task the product supports instead. | finding |
| NS-TC-010 | positive | NS-DRAFT-05 | NS-FACT-001 | The Starter plan supports up to 5 team members, not 10, so this contradicts active fact NS-FACT-001. | NS-DOC-PRICING section 2.1 Starter plan | high | Change "10" to "5". | finding |
| NS-TC-011 | positive | NS-DRAFT-05 | NS-FACT-008 | Team Timeline is on the Team plan only and is not included in Starter, so this contradicts active fact NS-FACT-008. | NS-DOC-PRODUCT section 4.3 Team Timeline | high | Remove the Starter claim and state that Team Timeline is available on the Team plan. | finding |
| NS-TC-012 | positive | NS-DRAFT-06 | NS-FACT-010 | The $10 price is the old Team plan price; NS-FACT-010 was superseded by NS-FACT-002, which sets the current price at $12. | NS-DOC-PRICING section 2.4 Historical pricing | high | Replace "$10" with "$12" and refer to NS-FACT-002. | finding |
| NS-TC-013 | positive | NS-DRAFT-06 | NS-FACT-003 | The 20% launch offer ended on 30 September 2026, before the fixed evaluation date of 23 October 2026, so it must not be presented as current. | NS-DOC-PRICING section 2.3 Launch offer | high | Remove the expired offer, or clearly mark it as historical if it is needed for context. | finding |
| NS-TC-014 | positive | NS-DRAFT-07 | NS-NAME-001 | The product name is written as "North Star Planner"; the approved name is "Northstar Planner". | NS-DOC-NAMING section 3.1 Product name | medium | Use "Northstar Planner". | finding |
| NS-TC-015 | positive | NS-DRAFT-07 | NS-NAME-001 | The brand is written as "NorthStar"; the approved form is "Northstar". | NS-DOC-NAMING section 3.1 Product name | medium | Use "Northstar" or "Northstar Planner". | finding |
| NS-TC-016 | positive | NS-DRAFT-07 | NS-NAME-001 | The product is called "Planner Pro", which is not an approved product name. | NS-DOC-NAMING section 3.1 Product name | medium | Replace it with "Northstar Planner". | finding |
| NS-TC-017 | ambiguous | NS-DRAFT-08 | NS-FACT-006 | The phrase "works with your calendar" is vague and could imply support for calendars that do not use the iCal (.ics) standard. | NS-DOC-PRODUCT section 4.1 Calendar Sync | medium | Use the approved wording: "Calendar Sync works with calendars that support the iCal (.ics) standard." | needs_human_judgement |
| NS-TC-018 | ambiguous | NS-DRAFT-08 | NS-CLAIM-006 | "Will soon be available everywhere" implies a release timeline and platform availability that no approved fact supports; Android is not yet available and no date is announced. | NS-DOC-CLAIMS section 3.6 Roadmap and availability | medium | State the current platforms only, or mark the future plan for human review with no promised date. | needs_human_judgement |
| NS-TC-019 | positive | NS-DRAFT-09 | NS-FMT-004 | The post uses two emoji, exceeding the limit of one emoji per social post. | NS-DOC-EDITORIAL section 7.4 Social posts | low | Keep at most one emoji, or remove them. | finding |
| NS-TC-020 | positive | NS-DRAFT-09 | NS-TONE-001 | The headline uses all caps and three exclamation marks, breaking the calm-voice limit. | NS-DOC-VOICE section 2.1 Calm voice | medium | Rewrite in sentence case with no more than one exclamation mark across the piece. | finding |
| NS-TC-021 | positive | NS-DRAFT-09 | NS-NAME-001 | The product is called "Planner Pro", which is not an approved name. | NS-DOC-NAMING section 3.1 Product name | medium | Use "Northstar Planner". | finding |
| NS-TC-022 | positive | NS-DRAFT-09 | NS-FACT-007 | Android is not yet available, and no release date has been announced, so this contradicts active fact NS-FACT-007. | NS-DOC-PRODUCT section 4.2 Platforms | high | Remove the Android claim or state clearly that Android is not yet available. | finding |
| NS-TC-023 | positive | NS-DRAFT-09 | NS-CLAIM-003 | This is an absolute security claim with no approved fact behind it; the approved wording only says customer data is encrypted in transit and at rest. | NS-DOC-CLAIMS section 3.3 Security and uptime | high | Replace it with the approved encryption fact, without absolutes. | finding |
| NS-TC-024 | positive | NS-DRAFT-09 | NS-CLAIM-005 | This is a customer-count and social-proof claim with no approved evidence. | NS-DOC-CLAIMS section 3.5 Social proof | high | Remove the count and do not replace it with another unverified number. | finding |
| NS-TC-025 | positive | NS-DRAFT-09 | NS-FACT-010 | The $10 price is the old Team plan price; NS-FACT-010 was superseded by NS-FACT-002, which sets the current price at $12. | NS-DOC-PRICING section 2.4 Historical pricing | high | Replace "$10" with "$12" and use the full approved price wording. | finding |
| NS-TC-026 | positive | NS-DRAFT-09 | NS-FMT-004 | The post uses three hashtags, exceeding the limit of two per social post. | NS-DOC-EDITORIAL section 7.4 Social posts | low | Remove one hashtag so at most two remain. | finding |
| NS-TC-027 | negative | NS-DRAFT-10 | — | — | — | — | — | no_finding |
| NS-TC-028 | negative | NS-DRAFT-01 revised | — | — | — | — | — | no_finding |
| NS-TC-029 | negative | NS-DRAFT-02 revised | — | — | — | — | — | no_finding |
| NS-TC-030 | negative | NS-DRAFT-03 revised | — | — | — | — | — | no_finding |
| NS-TC-031 | negative | NS-DRAFT-04 revised | — | — | — | — | — | no_finding |
| NS-TC-032 | negative | NS-DRAFT-05 revised | — | — | — | — | — | no_finding |
| NS-TC-033 | negative | NS-DRAFT-06 revised | — | — | — | — | — | no_finding |
| NS-TC-034 | negative | NS-DRAFT-07 revised | — | — | — | — | — | no_finding |
| NS-TC-035 | negative | NS-DRAFT-08 revised | — | — | — | — | — | no_finding |
| NS-TC-036 | negative | NS-DRAFT-09 revised | — | — | — | — | — | no_finding |
| NS-TC-037 | edge | NS-SNIP-01 | — | — | — | — | — | no_finding |
| NS-TC-038 | edge | NS-SNIP-02 | — | — | — | — | — | no_finding |
| NS-TC-039 | edge | NS-SNIP-03 | — | — | — | — | — | no_finding |
| NS-TC-040 | edge | NS-SNIP-04 | — | — | — | — | — | no_finding |
| NS-TC-041 | edge | NS-SNIP-05 | — | — | — | — | — | no_finding |
| NS-TC-042 | edge | NS-SNIP-06 | — | — | — | — | — | no_finding |
| NS-TC-043 | positive | NS-SNIP-07 | NS-TONE-002 | The phrase 'Don't miss out: act now' uses pressure and urgency language. | NS-DOC-VOICE section 2.2 Pressure-free language | medium | Replace 'Don't miss out: act now' with a calm statement such as 'Upgrade your plan when you're ready.' | finding |
| NS-TC-044 | positive | NS-SNIP-08 | NS-NAME-002 | The label 'kanban boards' is not the approved feature name 'Focus Boards'. | NS-DOC-NAMING section 3.2 Feature names | low | Replace 'kanban boards' with 'Focus Boards'. | finding |
| NS-TC-045 | positive | NS-SNIP-08 | NS-NAME-002 | The label 'Gantt view' is not the approved feature name 'Team Timeline'. | NS-DOC-NAMING section 3.2 Feature names | low | Replace 'Gantt view' with 'Team Timeline'. | finding |
| NS-TC-046 | positive | NS-SNIP-09 | NS-TERM-002 | The word 'package' should be 'plan' when naming a commercial plan. | NS-DOC-NAMING section 4.2 Plans | low | Replace 'package' with 'plan'. | finding |
| NS-TC-047 | positive | NS-SNIP-10 | NS-FMT-001 | The headline uses title case instead of sentence case. | NS-DOC-EDITORIAL section 7.1 Headline case | low | Rewrite the headline in sentence case: 'Plan your week with Focus Boards'. | finding |
| NS-TC-048 | positive | NS-SNIP-11 | NS-FMT-002 | The date '15/10/2026' is not in the required human-readable format. | NS-DOC-EDITORIAL section 7.2 Dates | low | Write the date as '15 October 2026'. | finding |
| NS-TC-049 | positive | NS-SNIP-12 | NS-FMT-003 | The price uses the shortened unit '$12/mo' instead of the full price wording. | NS-DOC-EDITORIAL section 7.3 Prices | low | Write the price as '$12 per team member per month'. | finding |
| NS-TC-050 | positive | NS-SNIP-13 | NS-FMT-005 | The headline is 61 characters, one character over the 60-character limit. | NS-DOC-EDITORIAL section 7.5 Headline length | low | Shorten the headline to 60 characters or fewer, for example 'Plan your week with Focus Boards'. | finding |
| NS-TC-051 | positive | NS-SNIP-14 | NS-CLAIM-004 | The phrase 'simpler than other planning apps' compares Northstar Planner with other products. | NS-DOC-CLAIMS section 3.4 Competitors | medium | Remove the comparison and describe Northstar Planner's own benefit, for example 'Northstar Planner helps your team plan the week.' | finding |
| NS-TC-052 | positive | NS-SNIP-15 | NS-REQ-002 | The text mentions Assist Suggestions without the required AI disclosure. | NS-DOC-EDITORIAL section 6.2 AI disclosure | medium | Add the exact disclosure sentence: 'Suggestions are generated by AI and should be reviewed before use.' | finding |
| NS-TC-053 | ambiguous | NS-SNIP-16 | NS-FACT-009 | The phrase 'available to everyone' may overstate the availability of Assist Suggestions, which is in beta on the Team plan. | NS-DOC-PRODUCT section 4.4 Assist Suggestions | medium | Replace the availability claim with the approved wording: 'Assist Suggestions is in beta on the Team plan and supports English only.' Also add the required AI disclosure. | needs_human_judgement |
| NS-TC-054 | ambiguous | NS-SNIP-17 | NS-FACT-004 | The phrase 'strong security' is vague and may imply a security claim not supported by the approved fact wording. | NS-DOC-SECURITY section 3.1 Encryption | medium | Replace 'strong security' with the approved wording: 'Customer data is encrypted in transit and at rest.' | needs_human_judgement |

## 4. Matching rules

A returned finding matches an expected finding only when the cited ID, span overlap, and one-to-one conditions all hold.

- The returned finding's cited ID equals expected.rule_or_fact_id or appears in expected.acceptable_alternate_ids.
- The returned finding's span overlaps the expected span by at least 50% of the expected span's characters. Overlap is max(0, min(returned_end, expected_end) - max(returned_start, expected_start)); the threshold is 0.5 * (expected_end - expected_start).
- Matching is one-to-one: each returned finding may match at most one expected finding, and each expected finding may be matched by at most one returned finding. Use an assignment that maximizes valid matches and break ties deterministically.
- Returned findings that match nothing are false positives, including extra findings on negative or edge inputs.

**Proposal note:** These matching rules are a proposal. Confirm them against docs/api-contracts.md before relying on any score.

## 5. Metrics

These are definitions only. No scores have been measured. All results fields stay null until the tests are actually run.

### Finding precision

**Definition:** True positives divided by true positives plus false positives.

**Formula:** `TP / (TP + FP)`

**Unit:** ratio from 0 to 1

**What is counted:** TP is returned findings matched one-to-one to an expected finding. FP is returned findings that match no expected finding, including any finding raised on a negative or edge input.

**Breakdowns:** Overall; by the cited rule or fact category from the guidelines file; and by check_method (computed, ai, hybrid).

### Finding recall

**Definition:** True positives divided by true positives plus false negatives.

**Formula:** `TP / (TP + FN)`

**Unit:** ratio from 0 to 1

**What is counted:** TP is returned findings matched one-to-one to an expected finding. FN is expected findings with no match.

**Breakdowns:** Overall; by the cited rule or fact category from the guidelines file; and by check_method (computed, ai, hybrid).

### Finding F1

**Definition:** Two times precision times recall, divided by precision plus recall.

**Formula:** `2PR / (P + R)`

**Unit:** ratio from 0 to 1

**What is counted:** P is finding precision and R is finding recall. Report the same overall, category, and check_method breakdowns as precision and recall.

**Breakdowns:** Overall; by the cited rule or fact category from the guidelines file; and by check_method (computed, ai, hybrid).

### Citation validity rate

**Definition:** Returned findings whose cited ID exists in the guidelines file and whose cited text a human reviewer judges to support the finding, divided by all returned findings.

**Formula:** `(ID_exists AND human_support) / returned_findings`

**Unit:** ratio from 0 to 1

**What is counted:** ID_exists is 1 when the cited ID is present in the guidelines file. Human_support is 1 when a reviewer judges the cited text to support the finding, otherwise 0. Score both parts for every returned finding. Report the automated part separately from the human-judged part.

**Note:** 100% is the plan's target, not a result. Report the automated and human parts separately.

**Component — Automated ID-exists rate:** Returned findings whose cited ID exists in the guidelines file divided by all returned findings.

Formula: `ID_exists / returned_findings`. Unit: ratio from 0 to 1. The automated check only; it does not judge whether the cited text supports the finding.

**Component — Human-judged citation support rate:** Returned findings whose cited text a human reviewer judges to support the finding divided by all returned findings.

Formula: `human_support / returned_findings`. Unit: ratio from 0 to 1. The reviewer scores support as 0 or 1 for each returned finding.

### Correct severity rate

**Definition:** Among true-positive findings, the share whose returned severity equals the expected severity.

**Formula:** `TP_exact_severity / TP`

**Unit:** ratio from 0 to 1

**What is counted:** Only findings already matched as true positives are scored.

**Component — Severity within one level:** Among true-positive findings, the share whose returned severity is within one level of the expected severity.

Formula: `TP_within_one_level / TP`. Unit: ratio from 0 to 1. Severity order is low < medium < high. One level means the same level or an adjacent level.

### Suggested-fix usefulness

**Definition:** Sum of reviewer usefulness scores divided by two times the number of true-positive findings.

**Formula:** `sum(score_f) / (2 * TP)`

**Unit:** ratio from 0 to 1

**What is counted:** Each true-positive finding receives a reviewer score: 0 = missing, wrong, or changes the meaning; 1 = points in the right direction but incomplete; 2 = usable as written, fixes the issue, keeps the creator's meaning, and introduces no new violation.

**Component — Fix re-check pass rate:** Share of true-positive fixes that, once applied, raise no finding for the same rule.

Formula: `fixes_recheck_pass / TP`. Unit: ratio from 0 to 1. Automated re-check of the applied fix for the same rule only.

### False-positive rate on compliant inputs

**Definition:** Number of compliant inputs with at least one returned finding divided by the number of compliant inputs.

**Formula:** `compliant_inputs_with_a_finding / compliant_inputs`

**Unit:** ratio from 0 to 1

**What is counted:** Compliant inputs are the negative and edge test cases. A near-expiry notice to a fact owner is not a finding.

**Component — Returned findings per compliant input:** Total returned findings on compliant inputs divided by the number of compliant inputs.

Formula: `returned_findings_on_compliant_inputs / compliant_inputs`. Unit: findings per input. All returned findings on negative and edge inputs, including duplicate rule hits.

### Ambiguity handling rate

**Definition:** Among ambiguous cases, the share where the tool returns needs_human_judgement or an explicitly low confidence instead of a confident violation.

**Formula:** `ambiguous_cases_handled / ambiguous_cases`

**Unit:** ratio from 0 to 1

**What is counted:** Ambiguous cases are the test cases with case_type ambiguous.

### High-severity recall

**Definition:** Recall computed over expected findings whose severity is high.

**Formula:** `TP_high / (TP_high + FN_high)`

**Unit:** ratio from 0 to 1

**What is counted:** Only expected findings with severity high are included in the denominator and numerator.

**Metrics note:** No scores have been measured. All results fields stay null until the tests are actually run.

## 6. How to run a test round

1. Fix the evaluation date at 2026-10-23 and confirm that the runner does not use the system clock for fact or offer status.
2. Run every input in the matrix exactly once and save the raw output with the test ID.
3. Record the run date and tool version for each case.
4. Match returned findings to expected findings using section 4, including the 50% span-overlap and one-to-one rules.
5. Fill one results record for each test case in `results_template`; do not leave a case unrun without a note.
6. Have a human reviewer score citation support (0 or 1) and suggested-fix usefulness (0, 1, or 2), then calculate the metrics.
7. Keep every score as not run until the full round and the human ratings are complete.

## 7. Results

| Metric | Overall | By category | By check method | Status |
|---|---|---|---|---|
| Finding precision | Not run | Not run | Not run | Not run |
| Finding recall | Not run | Not run | Not run | Not run |
| Finding F1 | Not run | Not run | Not run | Not run |
| Citation validity rate | Not run | Not run | Not run | Not run |
| Citation validity rate — Automated ID-exists rate | Not run | Not run | Not run | Not run |
| Citation validity rate — Human-judged citation support rate | Not run | Not run | Not run | Not run |
| Correct severity rate | Not run | Not run | Not run | Not run |
| Correct severity rate — Severity within one level | Not run | Not run | Not run | Not run |
| Suggested-fix usefulness | Not run | Not run | Not run | Not run |
| Suggested-fix usefulness — Fix re-check pass rate | Not run | Not run | Not run | Not run |
| False-positive rate on compliant inputs | Not run | Not run | Not run | Not run |
| False-positive rate on compliant inputs — Returned findings per compliant input | Not run | Not run | Not run | Not run |
| Ambiguity handling rate | Not run | Not run | Not run | Not run |
| High-severity recall | Not run | Not run | Not run | Not run |

## 8. Coverage summary and known coverage gaps

Counts include primary expected IDs, acceptable alternates, and acceptable alternative outcomes. Each case counts once per ID.

| ID | Kind | Positive | Negative | Edge | Ambiguous | Total |
|---|---|---|---|---|---|---|
| NS-TONE-001 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-TONE-002 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-TONE-003 | rule | 2 | 0 | 0 | 0 | 2 |
| NS-NAME-001 | rule | 4 | 0 | 1 | 0 | 5 |
| NS-NAME-002 | rule | 2 | 0 | 0 | 0 | 2 |
| NS-TERM-001 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-TERM-002 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-BAN-001 | rule | 2 | 0 | 0 | 0 | 2 |
| NS-BAN-002 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-REQ-001 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-REQ-002 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-FMT-001 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-FMT-002 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-FMT-003 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-FMT-004 | rule | 2 | 0 | 0 | 0 | 2 |
| NS-FMT-005 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-CLAIM-001 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-CLAIM-002 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-CLAIM-003 | rule | 1 | 0 | 0 | 1 | 2 |
| NS-CLAIM-004 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-CLAIM-005 | rule | 1 | 0 | 0 | 0 | 1 |
| NS-CLAIM-006 | rule | 0 | 0 | 0 | 1 | 1 |
| NS-FACT-001 | fact | 1 | 0 | 0 | 0 | 1 |
| NS-FACT-002 | fact | 2 | 0 | 0 | 0 | 2 |
| NS-FACT-003 | fact | 1 | 0 | 0 | 0 | 1 |
| NS-FACT-004 | fact | 0 | 0 | 0 | 1 | 1 |
| NS-FACT-006 | fact | 0 | 0 | 0 | 1 | 1 |
| NS-FACT-007 | fact | 1 | 0 | 0 | 1 | 2 |
| NS-FACT-008 | fact | 1 | 0 | 0 | 0 | 1 |
| NS-FACT-009 | fact | 0 | 0 | 0 | 1 | 1 |
| NS-FACT-010 | fact | 2 | 0 | 0 | 0 | 2 |

Coverage note: Counts include each case once per ID.
Coverage note: NS-FACT-002 appears only as an acceptable alternate citation in positive cases; it is never the primary expected fact.

Known coverage gaps are IDs that no positive case expects:

| ID | Kind | Reason |
|---|---|---|
| NS-REQ-003 | rule | Every offer in the pack is tied to the expired fact NS-FACT-003, so offer wording cannot be tested cleanly in isolation. |
| NS-CLAIM-006 | rule | Only appears as a needs_human_judgement finding in draft 08; Task C classifies that draft's findings as ambiguous, so there is no clean positive case. |
| NS-FACT-004 | fact | Only appears as the primary fact in ambiguous snippet 17; there is no clean positive case for the approved encryption wording. |
| NS-FACT-005 | fact | No test case supplies the approved uptime target wording; adding one would require a new draft or snippet. |
| NS-FACT-006 | fact | Only appears as a needs_human_judgement finding in draft 08; Task C classifies that draft's findings as ambiguous, so there is no clean positive case. |
| NS-FACT-009 | fact | Only appears as the primary fact in ambiguous snippet 16; there is no clean positive case for Assist Suggestions availability. |

## 9. Limitations

- The dataset is small and fictional; it covers one invented brand.
- The inputs are text only; layout, images, video, and interactive UI are out of scope.
- Reviewer ratings for citation support and fix usefulness are subjective.
- These matching rules are a proposal and must be confirmed against the API contracts.
- No score or result in this document is a measurement.

