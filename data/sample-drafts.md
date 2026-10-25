> **FICTIONAL TEST DATA — NOT A REAL COMPANY.**
>
> Northstar is an invented brand. Every draft, name, product, price, person, and policy in this file is invented for software testing and describes no real company, product, or person. Do not publish this content or present it as real.

# Northstar Sample Marketing Drafts

**Pack ID:** `northstar-demo-pack`  
**Guidelines file:** `data/northstar-brand-guidelines.json`  
**Evaluation date:** 2026-10-23  
**Offset unit:** unicode_code_points; JavaScript string indexes use UTF-16 units and will differ after emoji

## Definitions

| Expected label | Meaning |
|---|---|
| `violation` | The text breaks the cited rule or approved fact; a correction is required before publication. |
| `needs_human_judgement` | The text may break a rule or fact, but the available wording is ambiguous enough that a person must decide. |
| `unsupported` | The text makes a claim that approved facts do not support; a person must verify, revise, or remove it. |
| `contradicted` | The text conflicts with an active approved fact. |
| `outdated` | The text relies on a fact that was superseded or expired on the fixed evaluation date. |

**Human review definition:** A finding requires human review when the label is needs_human_judgement, unsupported, contradicted, or outdated, or when a reviewer must confirm a sensitive factual, legal, security, or customer-impact decision. The draft-level flag is true when at least one finding in that draft requires human review. It is an expected routing signal for this test data, not a claim that any reviewer has approved the text.

## Drafts

## NS-DRAFT-01 — Homepage introduction

**Channel:** `website_copy`  
**Audience:** first-time visitors  
**Purpose:** one-sentence homepage introduction  
**Scenario types:** `banned_language`, `terminology`  
**Expected outcome:** `needs_changes`  
**Human review required:** false

### Draft text

> Northstar Planner is a revolutionary, game-changing way for busy users to boost team synergy.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-01-F1` | `revolutionary` | `NS-BAN-001` | medium | `violation` | false |
| `NS-DRAFT-01-F2` | `game-changing` | `NS-BAN-001` | medium | `violation` | false |
| `NS-DRAFT-01-F3` | `users` | `NS-TERM-001` | low | `violation` | false |
| `NS-DRAFT-01-F4` | `synergy` | `NS-BAN-002` | low | `violation` | false |

### Finding details

#### NS-DRAFT-01-F1 — `revolutionary`

**Explanation:** "Revolutionary" is a banned hype word in the Northstar guideline pack.

**Suggested correction:** Replace it with a plain description of what the product helps the team do.

#### NS-DRAFT-01-F2 — `game-changing`

**Explanation:** "Game-changing" is also a banned hype word and adds no concrete information.

**Suggested correction:** Remove it and describe the benefit directly.

#### NS-DRAFT-01-F3 — `users`

**Explanation:** The preferred term is "team members" in customer-facing copy.

**Suggested correction:** Replace "users" with "team members".

#### NS-DRAFT-01-F4 — `synergy`

**Explanation:** "Synergy" is discouraged jargon and makes the sentence less clear.

**Suggested correction:** Replace it with a plain description such as "plan work together".

### Revised text

> Northstar Planner is a practical, clear way for busy teams to plan work together.

**Notes:** Four independent, low-to-medium findings; all are safe for a deterministic first-pass review.

---

## NS-DRAFT-02 — Sign-in incident notice

**Channel:** `status_notice`  
**Audience:** affected customers  
**Purpose:** tell customers about a resolved sign-in incident  
**Scenario types:** `serious_notice`, `tone`, `vague_wording`  
**Expected outcome:** `needs_changes`  
**Human review required:** true

### Draft text

> Oops! 😬 We had a teeny-tiny whoopsie with sign-in this morning, lol. Some of you couldn't log in for a bit. It's all sorted now, thanks for hanging in there.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-02-F1` | `Oops! 😬 We had a teeny-tiny whoopsie with sign-in this morning, lol.` | `NS-TONE-003` | high | `violation` | true |
| `NS-DRAFT-02-F2` | `Some of you couldn't log in for a bit.` | `NS-TONE-003` | medium | `violation` | true |

### Finding details

#### NS-DRAFT-02-F1 — `Oops! 😬 We had a teeny-tiny whoopsie with sign-in this morning, lol.`

**Explanation:** The opening uses humour, slang, and an emoji in a serious sign-in notice, and it does not clearly state what happened, who was affected, or what was done.

**Suggested correction:** Rewrite as a factual notice with the time window, affected group, and resolution, without jokes or emoji.

#### NS-DRAFT-02-F2 — `Some of you couldn't log in for a bit.`

**Explanation:** This sentence is vague about who was affected and for how long, so readers cannot tell the scope of the incident.

**Suggested correction:** Name the affected group and the time window, and state that the issue is fixed.

### Revised text

> Some customers could not sign in between 08:10 and 08:55 this morning. The issue is fixed, and sign-in is working normally. We are sorry for the disruption.

**Notes:** Serious-notice test. Both findings need human review because the notice is vague and uses humour, slang, and an emoji.

---

## NS-DRAFT-03 — Social pricing post

**Channel:** `social_post`  
**Audience:** small-team leads  
**Purpose:** announce the Team plan price on social media  
**Scenario types:** `pricing`, `required_wording`  
**Expected outcome:** `needs_changes`  
**Human review required:** false

### Draft text

> Planning for a small team? The Team plan costs $12 per team member per month, billed annually. Start with Focus Boards today.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-03-F1` | `$12 per team member per month, billed annually` | `NS-REQ-001` | medium | `violation` | false |

### Finding details

#### NS-DRAFT-03-F1 — `$12 per team member per month, billed annually`

**Explanation:** The post states a price but omits the required sentence "Prices exclude applicable taxes."

**Suggested correction:** Add the exact sentence after the price: "Prices exclude applicable taxes."

### Revised text

> Planning for a small team? The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes. Start with Focus Boards today.

**Notes:** Required-wording test. The only defect is the missing tax sentence; the price format itself is correct.

---

## NS-DRAFT-04 — Landing page hero

**Channel:** `landing_page`  
**Audience:** evaluators comparing planning tools  
**Purpose:** lead a landing page with a performance claim  
**Scenario types:** `unsupported_claim`, `superlative`, `numeric_performance`  
**Expected outcome:** `needs_changes`  
**Human review required:** true

### Draft text

> Northstar Planner is the fastest planning tool on the market. Teams using Northstar Planner save 10 hours every week.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-04-F1` | `the fastest planning tool on the market` | `NS-CLAIM-001` | high | `unsupported` | true |
| `NS-DRAFT-04-F2` | `Teams using Northstar Planner save 10 hours every week.` | `NS-CLAIM-002` | high | `unsupported` | true |

### Finding details

#### NS-DRAFT-04-F1 — `the fastest planning tool on the market`

**Explanation:** The superlative "fastest ... on the market" is an unsupported market-position claim; no approved fact supports it.

**Suggested correction:** Remove the ranking and describe the planning benefit in plain language.

#### NS-DRAFT-04-F2 — `Teams using Northstar Planner save 10 hours every week.`

**Explanation:** The "10 hours every week" claim is a numeric productivity claim with no approved fact behind it.

**Suggested correction:** Remove the number and describe the task the product supports instead.

### Revised text

> Northstar Planner helps teams plan the week, share deadlines, and see who owns what.

**Notes:** High-severity unsupported-claim test. No approved facts support the superlative or the numeric productivity claim.

---

## NS-DRAFT-05 — Starter plan FAQ

**Channel:** `pricing_page`  
**Audience:** customers comparing Starter and Team  
**Purpose:** explain what the Starter plan includes  
**Scenario types:** `contradicted_fact`, `plan_limits`  
**Expected outcome:** `needs_changes`  
**Human review required:** true

### Draft text

> Starter is free for up to 10 team members. Every Starter workspace also includes Team Timeline.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-05-F1` | `up to 10 team members` | `NS-FACT-001` | high | `contradicted` | true |
| `NS-DRAFT-05-F2` | `Every Starter workspace also includes Team Timeline.` | `NS-FACT-008` | high | `contradicted` | true |

### Finding details

#### NS-DRAFT-05-F1 — `up to 10 team members`

**Explanation:** The Starter plan supports up to 5 team members, not 10, so this contradicts active fact NS-FACT-001.

**Suggested correction:** Change "10" to "5".

#### NS-DRAFT-05-F2 — `Every Starter workspace also includes Team Timeline.`

**Explanation:** Team Timeline is on the Team plan only and is not included in Starter, so this contradicts active fact NS-FACT-008.

**Suggested correction:** Remove the Starter claim and state that Team Timeline is available on the Team plan.

### Revised text

> Starter is free for up to 5 team members. Team Timeline is available on the Team plan.

**Notes:** Contradicted-fact test. Both claims conflict with active approved facts.

---

## NS-DRAFT-06 — Outdated offer sales email

**Channel:** `sales_email`  
**Audience:** prospects who requested pricing  
**Purpose:** test stale pricing and an expired launch offer  
**Scenario types:** `outdated_fact`, `superseded_price`, `expired_offer`  
**Expected outcome:** `needs_changes`  
**Human review required:** true

### Draft text

> Team plan from $10 per team member per month, billed annually. Save 20% until 30 September 2026. Terms apply. Prices exclude applicable taxes.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-06-F1` | `$10 per team member per month` | `NS-FACT-010` (alt: `NS-FACT-002`) | high | `outdated` | true |
| `NS-DRAFT-06-F2` | `Save 20% until 30 September 2026.` | `NS-FACT-003` | high | `outdated` | true |

### Finding details

#### NS-DRAFT-06-F1 — `$10 per team member per month`

**Explanation:** The $10 price is the old Team plan price; NS-FACT-010 was superseded by NS-FACT-002, which sets the current price at $12.

**Suggested correction:** Replace "$10" with "$12" and refer to NS-FACT-002.

#### NS-DRAFT-06-F2 — `Save 20% until 30 September 2026.`

**Explanation:** The 20% launch offer ended on 30 September 2026, before the fixed evaluation date of 23 October 2026, so it must not be presented as current.

**Suggested correction:** Remove the expired offer, or clearly mark it as historical if it is needed for context.

### Revised text

> The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes.

**Notes:** Must be evaluated against the fixed evaluation date 2026-10-23, not the system clock. Both cited facts are stale: NS-FACT-010 is superseded and NS-FACT-003 is expired.

---

## NS-DRAFT-07 — Product introduction newsletter

**Channel:** `email_marketing`  
**Audience:** newsletter subscribers  
**Purpose:** introduce the product in a welcome newsletter  
**Scenario types:** `naming_inconsistency`, `product_name`  
**Expected outcome:** `needs_changes`  
**Human review required:** false

### Draft text

> Meet North Star Planner: a calm place to plan work, share deadlines and see who owns what. With NorthStar, your team stays on top of every task. Ready to try Planner Pro? Start on the Starter plan.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-07-F1` | `North Star Planner` | `NS-NAME-001` | medium | `violation` | false |
| `NS-DRAFT-07-F2` | `NorthStar` | `NS-NAME-001` | medium | `violation` | false |
| `NS-DRAFT-07-F3` | `Planner Pro` | `NS-NAME-001` | medium | `violation` | false |

### Finding details

#### NS-DRAFT-07-F1 — `North Star Planner`

**Explanation:** The product name is written as "North Star Planner"; the approved name is "Northstar Planner".

**Suggested correction:** Use "Northstar Planner".

#### NS-DRAFT-07-F2 — `NorthStar`

**Explanation:** The brand is written as "NorthStar"; the approved form is "Northstar".

**Suggested correction:** Use "Northstar" or "Northstar Planner".

#### NS-DRAFT-07-F3 — `Planner Pro`

**Explanation:** The product is called "Planner Pro", which is not an approved product name.

**Suggested correction:** Replace it with "Northstar Planner".

### Revised text

> Meet Northstar Planner: a calm place to plan work, share deadlines and see who owns what. With Northstar Planner, your team stays on top of every task. Ready to try Northstar Planner? Start on the Starter plan.

**Notes:** Naming-consistency test. All three findings are low-risk naming fixes and do not need specific human review.

---

## NS-DRAFT-08 — App description

**Channel:** `app_description`  
**Audience:** prospective users browsing an app store  
**Purpose:** describe calendar support and future availability  
**Scenario types:** `ambiguous_wording`, `platform_availability`, `fact_precision`  
**Expected outcome:** `needs_human_judgement`  
**Human review required:** true

### Draft text

> Northstar Planner works with your calendar and will soon be available everywhere.

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-08-F1` | `works with your calendar` | `NS-FACT-006` | medium | `needs_human_judgement` | true |
| `NS-DRAFT-08-F2` | `will soon be available everywhere` | `NS-CLAIM-006` (alt: `NS-FACT-007`) | medium | `needs_human_judgement` | true |

### Finding details

#### NS-DRAFT-08-F1 — `works with your calendar`

**Explanation:** The phrase "works with your calendar" is vague and could imply support for calendars that do not use the iCal (.ics) standard.

**Suggested correction:** Use the approved wording: "Calendar Sync works with calendars that support the iCal (.ics) standard."

#### NS-DRAFT-08-F2 — `will soon be available everywhere`

**Explanation:** "Will soon be available everywhere" implies a release timeline and platform availability that no approved fact supports; Android is not yet available and no date is announced.

**Suggested correction:** State the current platforms only, or mark the future plan for human review with no promised date.

### Revised text

> Northstar Planner is available on the web and iOS. Calendar Sync works with calendars that support the iCal (.ics) standard.

**Notes:** Expected outcome is needs_human_judgement with low confidence, not a hard violation. The wording is vague rather than clearly false; a human must decide whether it overpromises.

---

## NS-DRAFT-09 — Launch announcement stress test

**Channel:** `social_post`  
**Audience:** small-business owners  
**Purpose:** stress-test many rule types in one launch post  
**Scenario types:** `stress_test`, `social_post`, `mixed_findings`  
**Expected outcome:** `needs_changes`  
**Human review required:** true

### Draft text

> 🚀🚀 HUGE NEWS!!! Planner Pro is now on Android, 100% secure and trusted by thousands of teams. Plans from $10 per team member per month. Prices exclude applicable taxes. #planning #teamwork #productivity

### Findings

| ID | Flagged text | Cited ID | Severity | Label | Human review |
|---|---|---|---|---|---|
| `NS-DRAFT-09-F1` | `🚀🚀` | `NS-FMT-004` | low | `violation` | false |
| `NS-DRAFT-09-F2` | `HUGE NEWS!!!` | `NS-TONE-001` | medium | `violation` | false |
| `NS-DRAFT-09-F3` | `Planner Pro` | `NS-NAME-001` | medium | `violation` | false |
| `NS-DRAFT-09-F4` | `is now on Android` | `NS-FACT-007` | high | `contradicted` | true |
| `NS-DRAFT-09-F5` | `100% secure` | `NS-CLAIM-003` | high | `unsupported` | true |
| `NS-DRAFT-09-F6` | `trusted by thousands of teams` | `NS-CLAIM-005` | high | `unsupported` | true |
| `NS-DRAFT-09-F7` | `$10 per team member per month` | `NS-FACT-010` (alt: `NS-FACT-002`) | high | `outdated` | true |
| `NS-DRAFT-09-F8` | `#planning #teamwork #productivity` | `NS-FMT-004` | low | `violation` | false |

### Finding details

#### NS-DRAFT-09-F1 — `🚀🚀`

**Explanation:** The post uses two emoji, exceeding the limit of one emoji per social post.

**Suggested correction:** Keep at most one emoji, or remove them.

#### NS-DRAFT-09-F2 — `HUGE NEWS!!!`

**Explanation:** The headline uses all caps and three exclamation marks, breaking the calm-voice limit.

**Suggested correction:** Rewrite in sentence case with no more than one exclamation mark across the piece.

#### NS-DRAFT-09-F3 — `Planner Pro`

**Explanation:** The product is called "Planner Pro", which is not an approved name.

**Suggested correction:** Use "Northstar Planner".

#### NS-DRAFT-09-F4 — `is now on Android`

**Explanation:** Android is not yet available, and no release date has been announced, so this contradicts active fact NS-FACT-007.

**Suggested correction:** Remove the Android claim or state clearly that Android is not yet available.

#### NS-DRAFT-09-F5 — `100% secure`

**Explanation:** This is an absolute security claim with no approved fact behind it; the approved wording only says customer data is encrypted in transit and at rest.

**Suggested correction:** Replace it with the approved encryption fact, without absolutes.

#### NS-DRAFT-09-F6 — `trusted by thousands of teams`

**Explanation:** This is a customer-count and social-proof claim with no approved evidence.

**Suggested correction:** Remove the count and do not replace it with another unverified number.

#### NS-DRAFT-09-F7 — `$10 per team member per month`

**Explanation:** The $10 price is the old Team plan price; NS-FACT-010 was superseded by NS-FACT-002, which sets the current price at $12.

**Suggested correction:** Replace "$10" with "$12" and use the full approved price wording.

#### NS-DRAFT-09-F8 — `#planning #teamwork #productivity`

**Explanation:** The post uses three hashtags, exceeding the limit of two per social post.

**Suggested correction:** Remove one hashtag so at most two remain.

### Revised text

> The Northstar Planner app is available on the web and iOS. Customer data is encrypted in transit and at rest. The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes. #planning #teamwork

**Notes:** Eight-finding stress test covering formatting, tone, naming, contradicted facts, unsupported claims and outdated facts. The revised text is the clean control for the same scenario.

---

## NS-DRAFT-10 — Focus Boards product update

**Channel:** `product_update_email`  
**Audience:** current Team plan customers  
**Purpose:** announce a Focus Boards update without raising findings  
**Scenario types:** `fully_compliant`, `false_positive_control`  
**Expected outcome:** `no_findings`  
**Human review required:** false  
**Headline:** Plan your week with Focus Boards

### Draft text

> Plan your week with Focus Boards
>
> Northstar Planner now helps your team see what is due next. Arrange tasks on Focus Boards, give each task an owner and keep your whole team on the same page. Assist Suggestions can propose next steps for your tasks. Suggestions are generated by AI and should be reviewed before use. The Assist Suggestions feature is in beta. It is available on the Team plan and works in English only. The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes.

### Findings

No findings. This is the false-positive control.

### Revised text

_Not applicable. `revised_text` is null because the draft has no findings._

**Notes:** False-positive control. NS-FACT-009 is active but expires on 2026-12-31, 69 days after the evaluation date. A near-expiry notice to the fact owner is acceptable, but no finding should be raised against this draft.

---

## Coverage

| Set | Cited by at least one finding | Not cited by any finding |
|---|---|---|
| Rules (23) | 13 | 10 |
| Facts (10) | 6 | 4 |

### Rules cited by at least one finding

`NS-TONE-001`, `NS-TONE-003`, `NS-NAME-001`, `NS-TERM-001`, `NS-BAN-001`, `NS-BAN-002`, `NS-REQ-001`, `NS-FMT-004`, `NS-CLAIM-001`, `NS-CLAIM-002`, `NS-CLAIM-003`, `NS-CLAIM-005`, `NS-CLAIM-006`

### Rules not cited by any finding

`NS-TONE-002`, `NS-NAME-002`, `NS-TERM-002`, `NS-REQ-002`, `NS-REQ-003`, `NS-FMT-001`, `NS-FMT-002`, `NS-FMT-003`, `NS-FMT-005`, `NS-CLAIM-004`

### Facts cited by at least one finding

`NS-FACT-001`, `NS-FACT-003`, `NS-FACT-006`, `NS-FACT-007`, `NS-FACT-008`, `NS-FACT-010`

### Facts not cited by any finding

`NS-FACT-002`, `NS-FACT-004`, `NS-FACT-005`, `NS-FACT-009`

### Accepted alternate citations

`NS-FACT-002`, `NS-FACT-007`

### Coverage notes

- Rule coverage here counts primary finding citations only. A compliant draft can exercise a rule without raising a finding; for example, `NS-REQ-002` is exercised by `NS-DRAFT-10`.
- `NS-FACT-004` is exercised by the compliant revised text of `NS-DRAFT-09` but is not the primary citation of a finding.
- `NS-FACT-009` is exercised by `NS-DRAFT-10` but is not cited by a finding.
- `NS-FACT-002` is accepted as an alternate citation for `NS-FACT-010` in `NS-DRAFT-06` and `NS-DRAFT-09`.
- `NS-FACT-005` (uptime target) does not appear in any draft text or revised text and is the only fact not covered by any draft.
- The uncited rules above are not finding anchors in this sample set. Some may still be exercised by compliant drafts, so the absence of a finding is not proof that a rule is irrelevant.
