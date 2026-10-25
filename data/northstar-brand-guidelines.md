> **FICTIONAL TEST DATA — NOT A REAL COMPANY**
>
> FICTIONAL TEST DATA — NOT A REAL COMPANY. Northstar Planner is an invented brand. Every name, product, price, policy, owner role, and fact in this pack is invented for software testing and describes no real company, product, or person. Do not publish this content or present it as real.

# Northstar Planner — Fictional Brand Guideline Pack

**Pack ID:** `northstar-demo-pack` · **Schema version:** `1.0.0` · **Evaluation date:** 23 October 2026

---

## 1. Overview and audience

Northstar Planner is a fictional work-planning app for small teams of 5 to 50 people. It helps team leads and operations managers plan the week, keep a shared timeline, connect their calendars, and review AI-generated task suggestions. The voice is calm, clear, practical, and warm.

**Audience:** Team leads at small businesses and Operations managers at small businesses.

**Voice:** calm, clear, practical, and warm.

**Features:** Focus Boards, Team Timeline, Calendar Sync, and Assist Suggestions.

**Plans:** Starter and Team.

This pack is a fictional test fixture. It is not a statement of real product capabilities, prices, policies, or roadmaps. Every name, product, price, policy, owner role, and fact is invented for software testing.

**How to use this pack**

- **Rules** are the checks a reviewer or rule engine can apply. Each rule cites a source document and section.
- **Facts** are the only approved factual statements. A fact that is expired or superseded must not be used as current information.
- **The source register** lists the fictional documents used for citations. The documents themselves are not stored in this repository.
- **The evaluation date is fixed at 23 October 2026.** Fact status and days are calculated against that date, not the system clock.

---

## 2. Voice and tone

Northstar's voice is calm, clear, practical, and warm. It should sound like a thoughtful colleague: direct about the work, never pushy, and never theatrical. The rules below are the enforceable part of that voice.

### NS-TONE-001 — Calm voice with limited exclamation marks

- **Severity:** medium
- **Check method:** hybrid
- **Applies to:** `all_content`, `headlines`
- **Owner:** Director of Brand and Content
- **Source:** NS-DOC-VOICE §2.1 Calm voice
- **Status:** active
- **Effective date:** 15 June 2026
- **Pattern hints (case-insensitive regex):** `!`, `\b[A-Z]{3,}\b`

**Rule.** Write in a calm, clear voice. Use at most one exclamation mark in a whole piece, and use none in a headline. Do not use all-caps words or phrases for emphasis.

**Good example**

> Focus Boards help your team see what matters this week.

**Bad example**

> FOCUS BOARDS ARE HERE!!!

**Fix guidance.** Remove the extra exclamation marks and rewrite the all-caps words in sentence case.

**Notes.** Count exclamation marks across the whole piece, including headlines. Acronyms and product names are not all-caps emphasis; a human reviewer confirms context.

### NS-TONE-002 — No pressure or urgency language

- **Severity:** medium
- **Check method:** computed
- **Applies to:** `all_content`
- **Owner:** Director of Brand and Content
- **Source:** NS-DOC-VOICE §2.2 Pressure-free language
- **Status:** active
- **Effective date:** 15 June 2026
- **Pattern hints (case-insensitive regex):** `\bact now\b`, `\bdon'?t miss out\b`, `\blast chance\b`, `\bhurry\b`, `\blimited time only\b`, `\bbuy now\b`, `\bonly \d+ left\b`, `\boffer ends today\b`

**Rule.** Do not pressure the reader with urgency, scarcity, fear of missing out, or commands to act immediately. Examples include 'act now', 'don't miss out', 'last chance', 'hurry', and 'limited time only'.

**Good example**

> Start with the free Starter plan and upgrade when your team needs more room.

**Bad example**

> Act now — don't miss out on the last chance to save!

**Fix guidance.** Replace the pressure phrase with a factual description of the offer, plan, or deadline.

**Notes.** A factual deadline without pressure language is allowed, but it must also meet NS-REQ-003.

### NS-TONE-003 — Respectful serious notices

- **Severity:** high
- **Check method:** hybrid
- **Applies to:** `serious_notices`
- **Owner:** Director of Brand and Content
- **Source:** NS-DOC-VOICE §2.3 Serious notices
- **Status:** active
- **Effective date:** 15 June 2026
- **Pattern hints (case-insensitive regex):** `\b(oops|whoops|yikes)\b`, `[\U0001F300-\U0001FAFF]`

**Rule.** Serious notices about security, outages, sign-in problems, or billing must be factual and respectful. Do not use humour, slang, or emoji. State what happened, who was affected, and what was done.

**Good example**

> On 3 October 2026, Calendar Sync was unavailable for 40 minutes for some Team plan workspaces. The cause was a failed calendar connector update. The update was rolled back and Calendar Sync is working again.

**Bad example**

> Oops! Calendar Sync had a little wobble today. Sorry, folks — we're back!

**Fix guidance.** Remove jokes, slang, and emoji. Add the date, the people or workspaces affected, and the action taken.

**Notes.** If any of the three required facts is unknown, say what is known and mark the notice for human review. Do not speculate.

---

## 3. Preferred terminology

Names and everyday words are part of the brand. Use the exact product and feature names, and prefer the plain words in these rules. A substitute may be understandable but still inconsistent with the brand.

### NS-NAME-001 — Write the product name correctly

- **Severity:** medium
- **Check method:** hybrid
- **Applies to:** `all_content`, `product_names`
- **Owner:** Product Marketing Lead
- **Source:** NS-DOC-NAMING §3.1 Product name
- **Status:** active
- **Effective date:** 20 May 2026
- **Pattern hints (case-insensitive regex):** `\bNorth Star\b`, `\bNorthStar\b`, `\bNorth-Star\b`, `\bNorthstar App\b`, `\bPlanner Pro\b`

**Rule.** Write 'Northstar' as one word. The product is 'Northstar Planner'. Do not use 'North Star', 'NorthStar', 'North-Star', 'Northstar App', or 'Planner Pro'.

**Good example**

> Northstar Planner keeps the weekly plan in one place.

**Bad example**

> NorthStar Planner is the new Planner Pro for small teams.

**Fix guidance.** Use 'Northstar Planner' for the product and 'Northstar' for the brand.

**Notes.** A literal reference to the star is an edge case, not an error. A human reviewer decides whether the text is about astronomy or the brand.

### NS-NAME-002 — Use exact feature names

- **Severity:** low
- **Check method:** computed
- **Applies to:** `all_content`, `feature_names`
- **Owner:** Product Marketing Lead
- **Source:** NS-DOC-NAMING §3.2 Feature names
- **Status:** active
- **Effective date:** 20 May 2026
- **Pattern hints (case-insensitive regex):** `\bkanban boards?\b`, `\bGantt view\b`, `\bcalendar integration\b`, `\bAI assistant\b`, `\bAI helper\b`

**Rule.** Use the approved feature names: 'Focus Boards', 'Team Timeline', 'Calendar Sync', and 'Assist Suggestions'. Do not substitute generic or invented labels such as 'kanban boards', 'Gantt view', 'calendar integration', or 'AI assistant'.

**Good example**

> Team Timeline shows the work planned for the next few weeks.

**Bad example**

> The Gantt view and kanban boards are ready.

**Fix guidance.** Replace the substitute with the approved feature name.

**Notes.** Capitalise feature names exactly as shown. Generic descriptions are allowed when they do not name a feature, but human review may be needed.

### NS-TERM-001 — Prefer 'team members' to 'users'

- **Severity:** low
- **Check method:** computed
- **Applies to:** `all_content`, `body_copy`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-NAMING §4.1 People
- **Status:** active
- **Effective date:** 20 May 2026
- **Pattern hints (case-insensitive regex):** `\busers?\b`

**Rule.** In customer-facing copy, prefer 'team members' to 'users'. Use 'users' only when quoting a technical or legal source that cannot be changed.

**Good example**

> Team members can see their assigned work on Focus Boards.

**Bad example**

> Users can see their assigned work on Focus Boards.

**Fix guidance.** Replace 'user' or 'users' with 'team member' or 'team members'.

**Notes.** Do not use this rule to rewrite code, API field names, or direct quotations. Flag those for human review.

### NS-TERM-002 — Prefer 'plan' to 'package' or 'tier'

- **Severity:** low
- **Check method:** computed
- **Applies to:** `all_content`, `pricing_content`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-NAMING §4.2 Plans
- **Status:** active
- **Effective date:** 20 May 2026
- **Pattern hints (case-insensitive regex):** `\bpackages?\b`, `\btiers?\b`

**Rule.** Call a commercial plan a 'plan'. Do not use 'package' or 'tier' as a synonym for a plan.

**Good example**

> The Team plan includes Team Timeline.

**Bad example**

> The Team tier includes Team Timeline.

**Fix guidance.** Replace 'package' or 'tier' with 'plan'.

**Notes.** The words may still appear in direct quotations or legal names; flag those for human review instead of editing them.

---

## 4. Banned and discouraged terms

Banned terms are never allowed in Northstar copy. Discouraged terms are usually a sign that the sentence can be clearer; they are lower severity and may need human review when the word has a legitimate meaning.

### NS-BAN-001 — No hype words

- **Severity:** medium
- **Check method:** computed
- **Applies to:** `all_content`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §5.1 Banned hype words
- **Status:** active
- **Effective date:** 10 July 2026
- **Pattern hints (case-insensitive regex):** `\brevolutionary\b`, `\bgame[- ]changing\b`, `\bworld[- ]class\b`, `\bcutting[- ]edge\b`, `\bnext[- ]generation\b`, `\bbest[- ]in[- ]class\b`, `\bgroundbreaking\b`

**Rule.** Do not use these hype words: revolutionary, game-changing, world-class, cutting-edge, next-generation, best-in-class, groundbreaking.

**Good example**

> A practical planning tool for small teams.

**Bad example**

> A revolutionary, game-changing planning tool.

**Fix guidance.** Delete the hype word and describe the feature or benefit in plain language.

**Notes.** Match hyphenated and spaced forms. The list is exhaustive for this pack.

### NS-BAN-002 — Avoid discouraged jargon

- **Severity:** low
- **Check method:** hybrid
- **Applies to:** `all_content`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §5.2 Discouraged jargon
- **Status:** active
- **Effective date:** 10 July 2026
- **Pattern hints (case-insensitive regex):** `\bsynergy\b`, `\bleverage\b`, `\brockstars?\b`, `\bninjas?\b`, `\bgurus?\b`, `\bcrush it\b`, `\bno[- ]brainer\b`

**Rule.** Avoid these jargon terms: synergy, leverage (as a verb), rockstar, ninja, guru, crush it, no-brainer.

**Good example**

> Use the timeline to agree on priorities.

**Bad example**

> Leverage synergy to crush it like a rockstar.

**Fix guidance.** Rewrite the sentence in plain language that describes the action or benefit.

**Notes.** 'Leverage' is flagged only when it is used as a verb. The noun is uncommon in our copy but is not an error; a human reviewer confirms word class.

---

## 5. Required wording

Some statements carry legal, billing, or trust obligations. When the trigger applies, the required sentence must appear exactly as written in the same piece. Do not paraphrase it, shorten it, or move it to a linked page.

### NS-REQ-001 — Price tax disclosure

- **Severity:** medium
- **Check method:** computed
- **Applies to:** `all_content`, `pricing_content`
- **Owner:** Revenue Operations Manager
- **Source:** NS-DOC-EDITORIAL §6.1 Price disclosure
- **Status:** active
- **Effective date:** 10 July 2026
- **Required phrase:** “Prices exclude applicable taxes.”
- **Trigger:** A price, discount, or billing period appears anywhere in the piece.
- **Pattern hints (case-insensitive regex):** `\$\d`, `\bper team member\b`, `\bbilled annually\b`, `\bdiscount\b`

**Rule.** Any piece that states a price, a discount, or a billing period must include the exact sentence: 'Prices exclude applicable taxes.'

**Good example**

> The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes.

**Bad example**

> The Team plan costs $12 per team member per month, billed annually.

**Fix guidance.** Add the exact sentence 'Prices exclude applicable taxes.' near the price or in the pricing footnote.

**Notes.** The required sentence must appear exactly once per piece; do not paraphrase, shorten, or change the full stop. A price in an image alt text or table still triggers the rule.

### NS-REQ-002 — AI suggestion disclosure

- **Severity:** medium
- **Check method:** computed
- **Applies to:** `all_content`, `assist_suggestions_mentions`
- **Owner:** Legal Counsel
- **Source:** NS-DOC-EDITORIAL §6.2 AI disclosure
- **Status:** active
- **Effective date:** 10 July 2026
- **Required phrase:** “Suggestions are generated by AI and should be reviewed before use.”
- **Trigger:** Assist Suggestions, AI-generated suggestions, or generated suggestions are mentioned.
- **Pattern hints (case-insensitive regex):** `\bAssist Suggestions\b`, `\bAI[- ]generated\b`, `\bgenerated suggestions?\b`, `\bAI suggestions?\b`

**Rule.** Any mention of Assist Suggestions, AI-generated task suggestions, or generated suggestions must include the exact sentence: 'Suggestions are generated by AI and should be reviewed before use.'

**Good example**

> Assist Suggestions can propose next tasks for the team. Suggestions are generated by AI and should be reviewed before use.

**Bad example**

> Assist Suggestions can propose next tasks for the team.

**Fix guidance.** Add the exact disclosure sentence after the first mention.

**Notes.** The disclosure must not be hidden in a linked page or tooltip. It must appear in the same piece as the mention.

### NS-REQ-003 — Offer end date and terms

- **Severity:** medium
- **Check method:** hybrid
- **Applies to:** `offer_content`, `pricing_content`
- **Owner:** Revenue Operations Manager
- **Source:** NS-DOC-EDITORIAL §6.3 Offer disclosure
- **Status:** active
- **Effective date:** 10 July 2026
- **Required phrase:** “Terms apply.”
- **Trigger:** An offer, discount, or promotion is described.
- **Pattern hints (case-insensitive regex):** `\b\d{1,2}% off\b`, `\boffer\b`, `\bpromotion\b`, `\bdiscount\b`

**Rule.** Any offer, discount, or promotion must state an end date in the format '23 October 2026' and include the exact sentence: 'Terms apply.'

**Good example**

> The Team plan offer ends on 30 November 2026. Terms apply.

**Bad example**

> New workspaces get 20% off the Team plan. Don't miss it!

**Fix guidance.** Add a correctly formatted end date and the exact sentence 'Terms apply.' Remove pressure language.

**Notes.** The end date must be a calendar date, not 'while supplies last' or 'soon'. Both the date and the sentence are required. The expired launch offer in NS-FACT-003 must not be reused as a current offer.

---

## 6. Formatting rules

Formatting makes the copy predictable and easy to scan. These rules are mostly low severity, but they matter in a brand review because they are easy to check and easy to fix.

### NS-FMT-001 — Sentence-case headlines

- **Severity:** low
- **Check method:** computed
- **Applies to:** `headlines`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §7.1 Headline case
- **Status:** active
- **Effective date:** 10 July 2026

**Rule.** Write headlines in sentence case: capitalise the first word and proper nouns only. Do not use title case or all caps.

**Good example**

> Plan the week with your team

**Bad example**

> Plan The Week With Your Team

**Fix guidance.** Lowercase words other than the first word and proper nouns.

**Notes.** Product and feature names keep their approved capitalisation inside a headline, for example 'Northstar Planner'. Acronyms such as AI and iOS are allowed.

### NS-FMT-002 — Human-readable dates

- **Severity:** low
- **Check method:** computed
- **Applies to:** `all_content`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §7.2 Dates
- **Status:** active
- **Effective date:** 10 July 2026
- **Pattern hints (case-insensitive regex):** `\b\d{4}-\d{2}-\d{2}\b`, `\b\d{1,2}/\d{1,2}/\d{4}\b`, `\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b`

**Rule.** Write dates as '23 October 2026' in customer-facing copy. Do not use 2026-10-23, 10/23/2026, October 23, 2026, or 23/10/2026.

**Good example**

> The team review is on 30 October 2026.

**Bad example**

> The team review is on 09/30/2026.

**Fix guidance.** Rewrite the date as day month year, for example 30 October 2026.

**Notes.** ISO dates are allowed in metadata, API examples, and audit logs, but not in customer-facing copy. The evaluation date in the JSON is machine-readable and is displayed as 23 October 2026 in this guide.

### NS-FMT-003 — Price format

- **Severity:** low
- **Check method:** computed
- **Applies to:** `pricing_content`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §7.3 Prices
- **Status:** active
- **Effective date:** 10 July 2026
- **Pattern hints (case-insensitive regex):** `\$\d+(?:\.\d+)?\s*/\s*(?:mo|month|user|seat)\b`, `\$\d+(?:\.\d+)?\s+per\s+(?:user|seat)\b`, `\b\d+\s*USD\s*/\s*(?:mo|month)\b`

**Rule.** Write prices in the form '$12 per team member per month'. Do not use '/mo', '/month', '/user', or 'per user' as a shortened price unit.

**Good example**

> The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes.

**Bad example**

> The Team plan costs $12/mo per user.

**Fix guidance.** Spell out the full unit: '$12 per team member per month'.

**Notes.** Keep the order: amount, 'per team member', 'per month'. Use the currency symbol, not the currency code, in customer-facing copy. A monthly-equivalent figure for an annually billed plan must still use the full wording.

### NS-FMT-004 — Social post hashtags and emoji

- **Severity:** low
- **Check method:** computed
- **Applies to:** `social_posts`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §7.4 Social posts
- **Status:** active
- **Effective date:** 10 July 2026
- **Pattern hints (case-insensitive regex):** `#[A-Za-z0-9_]+`, `[\U0001F300-\U0001FAFF]`

**Rule.** A social post may use at most two hashtags and at most one emoji.

**Good example**

> Focus Boards are ready for small teams. #NorthstarPlanner #TeamPlanning 🙂

**Bad example**

> Focus Boards are ready! #NorthstarPlanner #TeamPlanning #SmallTeams 🎉🚀

**Fix guidance.** Remove extra hashtags or emoji so the post has no more than two hashtags and one emoji.

**Notes.** Count every hashtag occurrence, including repeated ones. Count visible emoji glyphs, not digits, '#', '*', or punctuation. Do not use emoji in serious notices; NS-TONE-003 takes precedence.

### NS-FMT-005 — Headline length

- **Severity:** low
- **Check method:** computed
- **Applies to:** `headlines`
- **Owner:** Editorial Lead
- **Source:** NS-DOC-EDITORIAL §7.5 Headline length
- **Status:** active
- **Effective date:** 10 July 2026

**Rule.** A headline must be 60 characters or fewer, including spaces and punctuation.

**Good example**

> Plan the week with your team

**Bad example**

> Plan the week, align the timeline, and keep every project moving forward

**Fix guidance.** Shorten the headline to 60 characters or fewer, or move detail into the body copy.

**Notes.** Count characters, not words. This rule applies to headlines only, not body copy, button labels, or alt text.

---

## 7. Approved facts

These are the only approved factual statements in the pack. Status is calculated for the fixed evaluation date, 23 October 2026. A fact is active when the evaluation date is on or before its expiry date. An expired fact must not be used as current information. A superseded fact has been replaced by another fact.

| ID | Topic | Approved statement | Owner | Source | Valid from | Expires | Status on 23 October 2026 | Days until expiry |
|---|---|---|---|---|---|---|---|---|
| NS-FACT-001 | Starter plan limits | The Starter plan is free, supports up to 5 team members, and includes up to 3 Focus Boards. | Revenue Operations Manager | NS-DOC-PRICING §2.1 Starter plan | 1 July 2026 | 30 June 2027 | active | 250 |
| NS-FACT-002 | Team plan price | The Team plan costs $12 per team member per month, billed annually. | Revenue Operations Manager | NS-DOC-PRICING §2.2 Team plan | 1 July 2026 | 30 June 2027 | active | 250 |
| NS-FACT-003 | Launch offer | The launch offer gave new workspaces 20% off the Team plan on annual billing from 1 August 2026 to 30 September 2026. | Revenue Operations Manager | NS-DOC-PRICING §2.3 Launch offer | 1 August 2026 | 30 September 2026 | expired | -23 |
| NS-FACT-004 | Encryption | Customer data is encrypted in transit and at rest. | Security and Trust Lead | NS-DOC-SECURITY §3.1 Encryption | 1 April 2026 | 31 March 2027 | active | 159 |
| NS-FACT-005 | Uptime target | Northstar Planner has a monthly uptime target of 99.5%. This is a target, not a guarantee. | Reliability Engineering Manager | NS-DOC-SECURITY §3.2 Uptime target | 1 August 2026 | 31 January 2027 | active | 100 |
| NS-FACT-006 | Calendar Sync compatibility | Calendar Sync works with calendars that support the iCal (.ics) standard. | Product Manager | NS-DOC-PRODUCT §4.1 Calendar Sync | 1 July 2026 | 30 June 2027 | active | 250 |
| NS-FACT-007 | Platform availability | Northstar Planner is available on the web and iOS. An Android app is not yet available, and no release date has been announced. | Product Manager | NS-DOC-PRODUCT §4.2 Platforms | 1 July 2026 | 15 January 2027 | active | 84 |
| NS-FACT-008 | Team Timeline plan availability | Team Timeline is on the Team plan only. It is not included in the Starter plan. | Product Manager | NS-DOC-PRODUCT §4.3 Team Timeline | 1 July 2026 | 30 June 2027 | active | 250 |
| NS-FACT-009 | Assist Suggestions availability | Assist Suggestions is in beta on the Team plan and supports English only. | AI Product Manager | NS-DOC-PRODUCT §4.4 Assist Suggestions | 15 September 2026 | 31 December 2026 | active | 69 |
| NS-FACT-010 | Historical Team plan price | The Team plan cost $10 per team member per month until 30 June 2026. | Revenue Operations Manager | NS-DOC-PRICING §2.4 Historical pricing | 1 July 2025 | 30 June 2026 | superseded by NS-FACT-002 | — |

Negative days mean the fact expired that many days before the evaluation date. A dash means the fact is superseded, so expiry is not used to decide its status.

### Fact notes

- **NS-FACT-001 — Starter plan limits:** Approved wording for the free plan. Do not describe Starter as unlimited or add features that are not listed here.
- **NS-FACT-002 — Team plan price:** Use the full price format from NS-FMT-003 and include the tax sentence from NS-REQ-001.
- **NS-FACT-003 — Launch offer:** EXPIRED on the evaluation date. Do not present this offer as current. Any historical mention must make clear that it has ended and must include the tax sentence and 'Terms apply.'
- **NS-FACT-004 — Encryption:** This is the only approved encryption wording in this pack. Do not add '100%', 'military-grade', or other absolutes.
- **NS-FACT-005 — Uptime target:** Keep both sentences together. The qualifier is mandatory; do not shorten the fact to '99.5% uptime'.
- **NS-FACT-006 — Calendar Sync compatibility:** Do not name specific calendar providers unless a separate approved fact authorises it. Do not imply support for calendars that do not support iCal.
- **NS-FACT-007 — Platform availability:** The Android app is not available. Do not say 'coming soon' with a date or imply that it can be used now.
- **NS-FACT-008 — Team Timeline plan availability:** Do not describe Team Timeline as available on Starter. If the plan changes, update this fact and its effective date.
- **NS-FACT-009 — Assist Suggestions availability:** Active but expiring soon. Always pair a mention with the AI disclosure in NS-REQ-002. Do not describe beta software as fully available or supported in other languages.
- **NS-FACT-010 — Historical Team plan price:** Superseded by NS-FACT-002 on 1 July 2026. Do not use this price in current copy. It may appear only in a clearly historical comparison, with human approval.

---

## 8. Unsupported claims

A claim is unsupported when the pack does not contain evidence for it. These rules are high severity when a false claim could mislead a customer or create legal risk. When in doubt, describe what the product does and leave out the comparison or the number.

### NS-CLAIM-001 — No superlative or market-position claims

- **Severity:** high
- **Check method:** hybrid
- **Applies to:** `public_claims`
- **Owner:** Legal Counsel
- **Source:** NS-DOC-CLAIMS §3.1 Superlatives
- **Status:** active
- **Effective date:** 5 August 2026
- **Pattern hints (case-insensitive regex):** `\bfastest\b`, `\bbest\b`, `\b#1\b`, `\bnumber one\b`, `\bleading\b`, `\bmost powerful\b`, `\bunbeatable\b`, `\bworld'?s best\b`

**Rule.** Do not claim that Northstar Planner or a feature is the fastest, best, number one, leading, most powerful, or unbeatable, or use similar market-position language.

**Good example**

> A practical way for small teams to plan the week.

**Bad example**

> The fastest and best planning app for small teams.

**Fix guidance.** Remove the superlative and describe the specific feature or benefit without ranking it.

**Notes.** Words such as 'best' are flagged for review even when they appear in a phrase such as 'best practice'; a human reviewer confirms whether the text is a claim about Northstar. Rankings and awards require evidence that is not approved in this pack.

### NS-CLAIM-002 — No numeric performance or productivity claims

- **Severity:** high
- **Check method:** hybrid
- **Applies to:** `public_claims`
- **Owner:** Legal Counsel
- **Source:** NS-DOC-CLAIMS §3.2 Performance claims
- **Status:** active
- **Effective date:** 5 August 2026
- **Pattern hints (case-insensitive regex):** `\bsaves? \d+(?:\.\d+)?\s*(?:hours?|minutes?|days?)\b`, `\b\d+(?:\.\d+)?x (?:faster|more productive)\b`, `\b(?:increase|boost|improve|reduce)[s]? .{0,30}\bby \d+(?:\.\d+)?%\b`, `\b\d+(?:\.\d+)?% (?:faster|more productive|less time)\b`

**Rule.** Do not make numeric performance or productivity claims, such as 'saves 10 hours', '2x faster', or 'boosts productivity by 30%', unless a verified approved fact authorises the exact claim.

**Good example**

> See the week ahead and agree on the next task.

**Bad example**

> Northstar Planner saves 10 hours every week and makes teams 2x faster.

**Fix guidance.** Remove the number and describe the feature or the task it supports. Do not replace it with a different unverified number.

**Notes.** No performance or productivity claim is approved in this pack. Even a number with 'up to' or 'on average' still requires evidence and human review.

### NS-CLAIM-003 — No absolute security or uptime claims

- **Severity:** high
- **Check method:** computed
- **Applies to:** `public_claims`
- **Owner:** Legal Counsel
- **Source:** NS-DOC-CLAIMS §3.3 Security and uptime
- **Status:** active
- **Effective date:** 5 August 2026
- **Pattern hints (case-insensitive regex):** `\b100% secure\b`, `\b100 percent secure\b`, `\bzero downtime\b`, `\bguaranteed uptime\b`, `\buptime guarantee\b`, `\bcompletely secure\b`, `\bfully secure\b`, `\bmilitary[- ]grade\b`

**Rule.** Do not claim that Northstar Planner is '100% secure', has 'zero downtime', guarantees uptime, or is completely safe. Use only the approved wording in NS-FACT-004 and NS-FACT-005.

**Good example**

> Customer data is encrypted in transit and at rest. Northstar Planner has a monthly uptime target of 99.5%; this is a target, not a guarantee.

**Bad example**

> Northstar Planner is 100% secure, with zero downtime and guaranteed uptime.

**Fix guidance.** Replace the absolute claim with the approved fact wording, including the target-not-guarantee qualifier for uptime.

**Notes.** The approved uptime fact is a target, never a promise. Do not remove the qualifier or turn 99.5% into a guarantee. Security wording must match NS-FACT-004.

### NS-CLAIM-004 — No competitor naming or comparison

- **Severity:** medium
- **Check method:** ai
- **Applies to:** `public_claims`
- **Owner:** Legal Counsel
- **Source:** NS-DOC-CLAIMS §3.4 Competitors
- **Status:** active
- **Effective date:** 5 August 2026

**Rule.** Do not name a competitor or compare Northstar Planner with another product, including phrases such as 'unlike other tools' or 'better than the alternatives'.

**Good example**

> Focus Boards give the team one place to agree on the week.

**Bad example**

> Unlike Brand X, Northstar Planner keeps the whole team aligned.

**Fix guidance.** Remove the competitor name and the comparison. Describe Northstar Planner's own feature or benefit.

**Notes.** 'Brand X' in the bad example is fictional and is not a real product. A human reviewer confirms indirect comparisons that do not name a competitor.

### NS-CLAIM-005 — No customer-count, rating, or testimonial claims

- **Severity:** high
- **Check method:** hybrid
- **Applies to:** `public_claims`
- **Owner:** Legal Counsel
- **Source:** NS-DOC-CLAIMS §3.5 Social proof
- **Status:** active
- **Effective date:** 5 August 2026
- **Pattern hints (case-insensitive regex):** `\btrusted by\b`, `\bthousands of (?:teams|companies|customers)\b`, `\b\d+(?:\.\d+)?\s*/\s*5\b`, `\b\d+(?:\.\d+)? stars?\b`, `\brated\b`, `\baward[- ]winning\b`, `\bour customers say\b`, `\btestimonial\b`

**Rule.** Do not claim customer counts, ratings, awards, or testimonials, including 'trusted by thousands of teams', '4.9/5', 'rated number one', or 'our customers say'.

**Good example**

> Small teams use Focus Boards to agree on the week's priorities.

**Bad example**

> Trusted by thousands of teams and rated 4.9/5.

**Fix guidance.** Remove the count, rating, award, or testimonial. Do not invent a replacement.

**Notes.** No customer evidence or testimonial permission is approved in this pack. A customer quote, logo, or rating requires documented permission and human approval outside this pack.

### NS-CLAIM-006 — No unreleased features or promised dates

- **Severity:** medium
- **Check method:** hybrid
- **Applies to:** `release_content`, `platform_availability`
- **Owner:** Product Manager
- **Source:** NS-DOC-CLAIMS §3.6 Roadmap and availability
- **Status:** active
- **Effective date:** 5 August 2026
- **Pattern hints (case-insensitive regex):** `\bcoming soon\b`, `\bwill (?:launch|ship|be available)\b`, `\bavailable (?:this|next) (?:month|quarter|year)\b`, `\broadmap\b`, `\bAndroid\b`

**Rule.** Do not present an unreleased feature or platform as available, and do not promise a release date. State clearly when a feature is in beta, limited to a plan, or not yet available.

**Good example**

> Assist Suggestions is in beta on the Team plan and supports English only. The Android app is not yet available, and no release date has been announced.

**Bad example**

> The Android app launches next quarter, and Assist Suggestions is available to everyone.

**Fix guidance.** Describe the current state only. Remove promised dates and any suggestion that an unreleased platform is already available.

**Notes.** The Android pattern is a prompt for review, not an automatic error: a factual statement that the Android app is not available is allowed under NS-FACT-007. 'Coming soon' without a date is vague but not a promise; a human reviewer decides whether it implies availability.

---

## 9. Source document register

The `documents` list is citation metadata for the fictional source documents used by the rules and facts. The documents themselves are not separate files in this repository. Each citation in the JSON uses a document ID and a section title from this register.

| Document ID | Title | Version | Owner | Last reviewed | Rules citing it | Facts citing it |
|---|---|---|---|---|---|---|
| NS-DOC-VOICE | Voice and Tone Guide | 2.1 | Director of Brand and Content | 15 June 2026 | NS-TONE-001, NS-TONE-002, NS-TONE-003 | — |
| NS-DOC-NAMING | Product Naming and Terminology Standard | 1.6 | Product Marketing Lead | 20 May 2026 | NS-NAME-001, NS-NAME-002, NS-TERM-001, NS-TERM-002 | — |
| NS-DOC-EDITORIAL | Editorial and Formatting Standard | 3.2 | Editorial Lead | 10 July 2026 | NS-BAN-001, NS-BAN-002, NS-REQ-001, NS-REQ-002, NS-REQ-003, NS-FMT-001, NS-FMT-002, NS-FMT-003, NS-FMT-004, NS-FMT-005 | — |
| NS-DOC-CLAIMS | Claims and Evidence Policy | 2.4 | Legal Counsel | 5 August 2026 | NS-CLAIM-001, NS-CLAIM-002, NS-CLAIM-003, NS-CLAIM-004, NS-CLAIM-005, NS-CLAIM-006 | — |
| NS-DOC-PRICING | Pricing and Offers Policy | 1.3 | Revenue Operations Manager | 28 September 2026 | — | NS-FACT-001, NS-FACT-002, NS-FACT-003, NS-FACT-010 |
| NS-DOC-SECURITY | Security and Reliability Statement | 1.2 | Security and Trust Lead | 1 September 2026 | — | NS-FACT-004, NS-FACT-005 |
| NS-DOC-PRODUCT | Product Availability and Roadmap Statement | 1.1 | Product Manager | 30 September 2026 | — | NS-FACT-006, NS-FACT-007, NS-FACT-008, NS-FACT-009 |

---

## 10. Owners and expiry summary

Owners are job titles, not real people. This summary shows who is responsible for each rule, fact, and source document, and which facts need attention around the evaluation date.

### Owners

| Owner role | Rules | Facts | Documents |
|---|---|---|---|
| AI Product Manager | 0 | 1 | 0 |
| Director of Brand and Content | 3 | 0 | 1 |
| Editorial Lead | 9 | 0 | 1 |
| Legal Counsel | 6 | 0 | 1 |
| Product Manager | 1 | 3 | 1 |
| Product Marketing Lead | 2 | 0 | 1 |
| Reliability Engineering Manager | 0 | 1 | 0 |
| Revenue Operations Manager | 2 | 4 | 1 |
| Security and Trust Lead | 0 | 1 | 1 |

**Rule ownership detail**

- **Director of Brand and Content:** NS-TONE-001, NS-TONE-002, NS-TONE-003
- **Editorial Lead:** NS-TERM-001, NS-TERM-002, NS-BAN-001, NS-BAN-002, NS-FMT-001, NS-FMT-002, NS-FMT-003, NS-FMT-004, NS-FMT-005
- **Legal Counsel:** NS-REQ-002, NS-CLAIM-001, NS-CLAIM-002, NS-CLAIM-003, NS-CLAIM-004, NS-CLAIM-005
- **Product Manager:** NS-CLAIM-006
- **Product Marketing Lead:** NS-NAME-001, NS-NAME-002
- **Revenue Operations Manager:** NS-REQ-001, NS-REQ-003

**Fact ownership detail**

- **AI Product Manager:** NS-FACT-009
- **Product Manager:** NS-FACT-006, NS-FACT-007, NS-FACT-008
- **Reliability Engineering Manager:** NS-FACT-005
- **Revenue Operations Manager:** NS-FACT-001, NS-FACT-002, NS-FACT-003, NS-FACT-010
- **Security and Trust Lead:** NS-FACT-004

**Document ownership detail**

- **Director of Brand and Content:** NS-DOC-VOICE
- **Editorial Lead:** NS-DOC-EDITORIAL
- **Legal Counsel:** NS-DOC-CLAIMS
- **Product Manager:** NS-DOC-PRODUCT
- **Product Marketing Lead:** NS-DOC-NAMING
- **Revenue Operations Manager:** NS-DOC-PRICING
- **Security and Trust Lead:** NS-DOC-SECURITY

### Expiry summary

- **Expired:** **NS-FACT-003 — Launch offer** expired on 30 September 2026, 23 days before the evaluation date.
- **Superseded:** **NS-FACT-010 — Historical Team plan price** was superseded by NS-FACT-002 (original expiry 30 June 2026).
- **Active and expiring within 90 days:** **NS-FACT-009 — Assist Suggestions availability** expires on 31 December 2026 (69 days left). **NS-FACT-007 — Platform availability** expires on 15 January 2027 (84 days left).

**Action for the demo:** do not quote NS-FACT-003 as a current offer. Re-check NS-FACT-009 before the demo; it is active but expires soon.

### Active facts in expiry order

| ID | Topic | Expires | Days left |
|---|---|---|---|
| NS-FACT-009 | Assist Suggestions availability | 31 December 2026 | 69 |
| NS-FACT-007 | Platform availability | 15 January 2027 | 84 |
| NS-FACT-005 | Uptime target | 31 January 2027 | 100 |
| NS-FACT-004 | Encryption | 31 March 2027 | 159 |
| NS-FACT-001 | Starter plan limits | 30 June 2027 | 250 |
| NS-FACT-002 | Team plan price | 30 June 2027 | 250 |
| NS-FACT-006 | Calendar Sync compatibility | 30 June 2027 | 250 |
| NS-FACT-008 | Team Timeline plan availability | 30 June 2027 | 250 |

---

## Appendix A. How to read the JSON

This appendix is for anyone who needs to edit, test, or explain the pack. The JSON file is the source of truth. This Markdown file is generated from it, so the two cannot disagree unless someone edits the Markdown by hand.

### A.1 Top-level keys

| Key | What it holds | In this pack |
|---|---|---|
| `schema_version` | Version of the JSON layout. | `1.0.0` |
| `pack_id` | Stable identifier for this guideline pack. | `northstar-demo-pack` |
| `is_fictional` | `true` when every detail is invented. | `true` |
| `fictional_notice` | Plain-language warning that the pack is not real. | See the top of this file. |
| `evaluation_as_of_date` | The fixed date used to calculate fact status. | `2026-10-23` |
| `brand` | Object with the fictional product, audience, voice, features, and plan names. | 1 object |
| `documents` | Register of fictional source documents used for citations. | 7 records |
| `rules` | The checks a reviewer or engine applies. | 23 rules |
| `facts` | The approved factual statements and their expiry state. | 10 facts |

### A.2 Rule fields

| Field | Type | Required | What it means |
|---|---|---|---|
| `id` | string | yes | Unique rule ID, for example `NS-BAN-001`. |
| `category` | string | yes | Rule family: tone, naming, terminology, banned_language, required_wording, formatting, or claims. |
| `title` | string | yes | Short human-readable name. |
| `rule_text` | string | yes | The instruction a writer or reviewer follows. |
| `check_method` | string | yes | `computed`, `ai`, or `hybrid`. See A.4. |
| `severity_default` | string | yes | `low`, `medium`, or `high`. See A.5. |
| `applies_to` | array of strings | yes | Content types the rule applies to. See A.11. |
| `source` | object | yes | `document_id` plus `section` from the document register. |
| `owner_role` | string | yes | Job title responsible for the rule, never a person's name. |
| `status` | string | yes | `active`, `draft`, or `retired`. All rules here are active. |
| `effective_date` | ISO date | yes | Date the rule took effect. |
| `patterns` | array of strings | no | Optional regex hints for testing or a rule engine. |
| `required_phrase` | string or null | no | Exact sentence that must appear when the trigger applies. |
| `trigger` | string or null | no | Condition that makes a required phrase mandatory. |
| `good_example` | string | no | A short example that follows the rule. |
| `bad_example` | string | no | A short example that breaks the rule. |
| `fix_guidance` | string | no | Practical instruction for fixing a finding. |
| `notes` | string | no | Edge cases and review guidance. |

### A.3 Fact fields

| Field | Type | Required | What it means |
|---|---|---|---|
| `id` | string | yes | Unique fact ID, for example `NS-FACT-002`. |
| `topic` | string | yes | Short label for the fact. |
| `statement` | string | yes | The approved wording. Do not paraphrase it in published copy. |
| `owner_role` | string | yes | Job title responsible for keeping the fact current. |
| `source` | object | yes | `document_id` plus `section` from the document register. |
| `valid_from` | ISO date | yes | First day the fact is valid. |
| `expires_on` | ISO date | yes | Last day the fact is valid, inclusive. |
| `status_on_evaluation_date` | string | yes | Computed: `active`, `expired`, or `superseded`. |
| `days_until_expiry` | integer or null | yes | Computed calendar days from the evaluation date to `expires_on`. Negative means already expired. Null means superseded. |
| `superseded_by` | string or null | yes | ID of the fact that replaced this one, if any. |
| `notes` | string | yes | Usage guidance and edge cases. |

### A.4 Check methods

| Value | Meaning |
|---|---|
| `computed` | A deterministic check. The same input should produce the same result, and the finding can cite the rule directly. |
| `hybrid` | A deterministic pre-check plus human or model judgment. For example, a pattern may find a candidate, but a person decides whether it is really a problem. |
| `ai` | The check needs model judgment, such as recognising a competitor comparison. A human should review the result. |

### A.5 Severity levels

| Value | Meaning in this pack |
|---|---|
| `high` | Legal, trust, or reputational risk. Fix before publication. |
| `medium` | A clear brand or disclosure problem. Fix before publication. |
| `low` | A consistency or style issue. Fix in normal editing. |

### A.6 Status and date math

The evaluation date is fixed at `2026-10-23`. It is not the system clock. `expires_on` is the last valid day. The JSON stores the computed status and day count, and the validator recomputes both independently.

```text
if superseded_by is set:
    status = "superseded"
    days_until_expiry = null
else if evaluation_as_of_date > expires_on:
    status = "expired"
    days_until_expiry = expires_on - evaluation_as_of_date
else:
    status = "active"
    days_until_expiry = expires_on - evaluation_as_of_date
```

A negative `days_until_expiry` is expected for an expired fact. A superseded fact has no meaningful expiry count, so the value is null.

### A.7 Source references

Every rule and fact has a `source` object with a `document_id` and a `section`. The `document_id` must appear in the `documents` list. The section is a short title from the fictional source document. The register is metadata for citations; the source documents are not separate files in this repository.

### A.8 Pattern hints and examples

`patterns` is an optional list of regular expressions. They are hints for a deterministic check or a test, not a complete implementation of the rule. All patterns are matched case-insensitively. A pattern match is a candidate finding; the check method and the notes decide whether a human must review it. The good and bad examples are short illustrations, not a sample draft dataset.

### A.9 How this file is generated

The JSON file is the source of truth. A temporary Python script reads the JSON and generates this Markdown file. A separate validation script checks the JSON, recomputes fact status, checks every source reference and ID, and confirms that this Markdown mentions every rule and fact. Do not hand-edit the Markdown; change the JSON and regenerate.

### A.10 Glossary

- **Rule:** an instruction that can produce a finding when content breaks it.
- **Fact:** an approved statement with a source, an owner, and an expiry date.
- **Pack:** this complete set of brand metadata for one fictional brand.
- **Evaluation date:** the fixed date used to decide whether a fact is active, expired, or superseded.
- **Superseded:** replaced by a newer fact, even if the old fact has not yet reached its expiry date.
- **Finding:** a review result that cites a rule or fact. Findings are outside the scope of this pack; the pack only defines the rules and facts they can cite.

### A.11 Content types used in `applies_to`

| Value | Meaning |
|---|---|
| `all_content` | Any customer-facing piece. |
| `headlines` | Titles, subject lines, and on-page headings. |
| `body_copy` | Paragraphs and explanatory text. |
| `social_posts` | Posts for social channels. |
| `pricing_content` | Pages, emails, or posts that state prices or plan limits. |
| `offer_content` | Promotions, discounts, and launch offers. |
| `serious_notices` | Security, outage, sign-in, and billing notices. |
| `product_names` | Places where the product name is written. |
| `feature_names` | Places where feature names are written. |
| `assist_suggestions_mentions` | Any mention of Assist Suggestions or AI-generated suggestions. |
| `public_claims` | Marketing and public statements about the product. |
| `release_content` | Launch and roadmap content. |
| `platform_availability` | Statements about web, iOS, and Android availability. |

### A.12 What this pack is not

This is not a real brand guide, not legal advice, and not a sample draft dataset. It does not prove that any Trueline feature works. It is fictional test data for evaluating brand-governance checks.

---

*End of the Northstar Planner fictional guideline pack.*

