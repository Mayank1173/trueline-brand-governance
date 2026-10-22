# Demo Script

1. Load sample brand guidelines.
2. Submit a flawed draft.
3. Review findings and source citations.
4. Apply a suggested fix.
5. Submit for human approval.

## Northstar 3 to 5 minute demo script (draft by Apurwa)

Purpose: show Trueline as a pre-publication review layer that grounds findings in the Northstar guideline pack, explains each finding, keeps a person in control of changes, and records human approval.

> **Status banner:** Demo plan only. Features are shown live only if the developers have implemented and tested them; otherwise they are labelled MOCKUP.

Fixed evaluation date for this demo: **23 October 2026**. The expired offer in the draft depends on this date.

### Total time budget

| Step | Segment | Time | Cumulative |
|---|---:|---:|---|
| 1 | Load the Northstar guidelines | 40 s | 0:40 |
| 2 | Submit the flawed draft | 35 s | 1:15 |
| 3 | Show findings, spans, and citations | 55 s | 2:10 |
| 4 | Review the suggested fix | 35 s | 2:45 |
| 5 | Resubmit the revised draft | 40 s | 3:25 |
| 6 | Show human approval, revision history, and audit trace | 65 s | 4:30 |
| **Total** | | **270 s** | **4:30** |

Hard stop: 5:00.

### Demo data copied from the project files

Draft ID: `NS-DRAFT-06` — “Outdated offer sales email”.

Draft text, exact from `data/sample-drafts.json`:

> Team plan from $10 per team member per month, billed annually. Save 20% until 30 September 2026. Terms apply. Prices exclude applicable taxes.

Expected draft outcome: `needs_changes`.

| Finding | Exact span | Citation ID | Severity | Explanation | Suggested correction |
|---|---|---|---|---|---|
| `NS-DRAFT-06-F1` | `$10 per team member per month` | `NS-FACT-010` | `high` | The $10 price is the old Team plan price; NS-FACT-010 was superseded by NS-FACT-002, which sets the current price at $12. | Replace "$10" with "$12" and refer to NS-FACT-002. |
| `NS-DRAFT-06-F2` | `Save 20% until 30 September 2026.` | `NS-FACT-003` | `high` | The 20% launch offer ended on 30 September 2026, before the fixed evaluation date of 23 October 2026, so it must not be presented as current. | Remove the expired offer, or clearly mark it as historical if it is needed for context. |

Citation source lookup from `data/northstar-brand-guidelines.json`:

| Fact ID | Source document | Section | Status on 23 October 2026 |
|---|---|---|---|
| `NS-FACT-010` | `NS-DOC-PRICING` | 2.4 Historical pricing | `superseded` by `NS-FACT-002` |
| `NS-FACT-003` | `NS-DOC-PRICING` | 2.3 Launch offer | `expired` on 30 September 2026 |
| `NS-FACT-002` | `NS-DOC-PRICING` | 2.2 Team plan | `active`; current price is $12 |

Both findings have `human_review_required: true` in the sample data.

Revised text, exact from `data/sample-drafts.json`:

> The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes.

### Step 1 — Load the Northstar guidelines (40 seconds)

- **What the presenter does:** Click `Guidelines`, then select `Northstar Demo Pack`. Say: “First, I load the fictional Northstar pack. It contains the source documents, rules, and approved facts that the review must use.” Point to `NS-FACT-010`, `NS-FACT-003`, and `NS-FACT-002`. Point to the `superseded` and `expired` labels. Say: “The date I use is fixed at 23 October 2026.”
- **What the audience should see:** The guideline pack, document list, rule IDs, fact IDs, and status labels. The fictional-data notice should be visible. If the screen is not connected, show a labelled `DATA VIEW — SAMPLE GUIDELINES`.
- **What this proves:** The demo starts from a controlled guideline source, not general model memory. Link: `FR-01`, `FR-05`.
- **Status label:** `MOCKUP`
- **Fallback if not ready:** Show a screenshot of the guideline library or a table built from `data/northstar-brand-guidelines.json`. Label it `MOCKUP — GUIDELINES LIBRARY` or `DATA VIEW — SAMPLE GUIDELINES`. Do not call it a live upload.

### Step 2 — Submit the flawed draft (35 seconds)

- **What the presenter does:** Click `New draft`. Choose the Northstar pack. Paste the exact `NS-DRAFT-06` text. Say: “This sales email quotes an old price and an expired offer.” Click `Submit for review`. Point to the state change from `Draft` to `In AI review`.
- **What the audience should see:** The draft fields, the exact sales email, the selected guideline pack, and the state badge. The draft moves to `In AI review`.
- **What this proves:** Content enters a review pipeline tied to a specific guideline pack. Link: `FR-06`, `FR-07`, `FR-27`.
- **Status label:** `MOCKUP`
- **Fallback if not ready:** Show a screenshot of the draft form or the draft data from `data/sample-drafts.json`. Label it `MOCKUP — SUBMISSION FORM` or `DATA VIEW — SAMPLE DRAFT`. Say that the submit action is simulated.

### Step 3 — Show findings, spans, and citations (55 seconds)

- **What the presenter does:** Click `View findings`. Highlight the span `$10 per team member per month`. Say: “The first finding cites `NS-FACT-010` from `NS-DOC-PRICING`, section 2.4 Historical pricing. That price was superseded by `NS-FACT-002`, which sets the current price at $12.” Highlight `Save 20% until 30 September 2026.` Say: “The second finding cites `NS-FACT-003` from `NS-DOC-PRICING`, section 2.3 Launch offer. That offer expired on 30 September 2026, before our fixed evaluation date.” Read the labels: both are `outdated` and `high` severity. Point to the AI-use disclosure.
- **What the audience should see:** Two findings with exact spans, citation IDs, source document and section, severity, explanation, suggested correction, and the AI-use disclosure. The state changes to `Needs changes`.
- **What this proves:** Findings are explainable and grounded in the selected pack. Link: `FR-13`, `FR-14`, `FR-18`, `FR-19`; `AC-05`, `AC-06`.
- **Status label:** `SIMULATED`
- **Fallback if not ready:** Show a static findings mockup or the expected findings from `data/sample-drafts.json`. Label it `MOCKUP — FINDINGS VIEW` or `DATA VIEW — EXPECTED FINDINGS`. Say: “These are the expected findings from the sample data; the live review is not connected in this demo.”

### Step 4 — Review the suggested fix (35 seconds)

- **What the presenter does:** Click `Suggested fix`. Point to the first correction: replace `$10` with `$12` and refer to `NS-FACT-002`. Point to the second correction: remove the expired offer, or mark it as historical. Say: “Nothing changes until a person confirms it.” If Intent Lock is shown, point to the meaning check and say it is planned. If it is not shown, say: “Intent Lock is planned and is not shown in this demo.”
- **What the audience should see:** The two suggested corrections, a confirm or edit control, and a clear warning that the draft has not changed yet.
- **What this proves:** The product suggests fixes but keeps the person in control. It does not rewrite content silently. Link: `FR-20`, `FR-21`, `FR-24`.
- **Status label:** `MOCKUP`
- **Fallback if not ready:** Show the exact suggested corrections from the sample data and the exact revised text. Label it `PROPOSED FIX — SAMPLE DATA`. Do not say the product applied the fix.

### Step 5 — Resubmit the revised draft (40 seconds)

- **What the presenter does:** Apply the confirmed corrections, or paste the exact revised text. Click `Resubmit for review`. Say: “This is the revised text from the sample data.” Show the clean re-review result. Point to the state change from `In AI review` to `In human review`.
- **What the audience should see:** The exact revised text, a comparison with the original, a clean re-review result, and the state `In human review`.
- **What this proves:** The revision loop closes and the revised draft is checked again. Link: `FR-22`, `FR-27`, `FR-30`.
- **Status label:** `SIMULATED`
- **Fallback if not ready:** Show the exact revised text and a labelled `SIMULATED RE-REVIEW — NO FINDINGS` panel. Do not claim the re-review ran live.

### Step 6 — Show human approval, revision history, and audit trace (65 seconds)

- **What the presenter does:** Switch to the Manager role, or open the approval screen. Show the draft in `In human review`. Say: “The AI does not approve. A person with approval permission does.” Click `Approve`. Point to the state `Approved`. Open revision history and the audit trace. Read the chain: `Draft → In AI review → Needs changes → In AI review → In human review → Approved`. Point to the actor and time for each transition.
- **What the audience should see:** The approval action, the final state, the revision history, and an audit trace with each transition. The approval control should be limited to an authorised role. If the audit screen is not connected, show a clearly labelled simulated trace.
- **What this proves:** Human approval, role-based review, revision history, and auditability. Link: `FR-25`, `FR-28`, `FR-29`, `FR-31`, `FR-32`, `FR-33`; `AC-16`, `AC-19`.
- **Status label:** `SIMULATED`
- **Fallback if not ready:** Use screenshots or a storyboard for approval and revision history. Show a table labelled `SIMULATED AUDIT TRACE — PLANNED WORKFLOW`. Do not claim an audit log exists if it is not shown and tested.

### Pre-demo checklist

- [ ] Confirm `docs/demo-script.md` still has only the original five bullets before this section.
- [ ] Confirm the demo draft is `NS-DRAFT-06`; keep `NS-DRAFT-04` as backup.
- [ ] Confirm the review uses the fixed evaluation date `23 October 2026`, not the system clock.
- [ ] Confirm every step is labelled `LIVE`, `MOCKUP`, or `SIMULATED`; use `LIVE` only after owner confirmation.
- [ ] Confirm the Manager approval action and the role restriction.
- [ ] Confirm the revision history and audit trace, or prepare the simulated backup.
- [ ] Rehearse with a timer: target 4:30, hard stop 5:00.
- [ ] Test the demo screen at final resolution and zoom.
- [ ] Prepare backup screenshots, a JSON printout, and an offline copy.
- [ ] Reset the demo environment and remove duplicate drafts.
- [ ] Keep the fictional-data notice visible.
- [ ] Confirm no real customer data appears.
- [ ] Prepare short answers for “Is this live?” and “Does the AI approve?”
- [ ] Record a backup screen capture if the team allows it.

### Sample speaker script (about 4:30)

**Opening:** “Trueline is a pre-publication review layer. It checks a draft against an approved brand pack, explains each finding, and keeps a person in charge of approval. This is a demo plan; every screen is a mockup or simulated unless the owners confirm it is live.”

**Step 1:** “First, I open the Northstar guideline pack. You can see the source documents, rule IDs such as `NS-BAN-001`, and facts such as `NS-FACT-002`, `NS-FACT-003` and `NS-FACT-010`. The status of each fact matters. This pack is fictional and the evaluation date is fixed at 23 October 2026.”

**Step 2:** “Next, I select `NS-DRAFT-06`, the outdated offer sales email. The text reads: ‘Team plan from $10 per team member per month, billed annually. Save 20% until 30 September 2026. Terms apply. Prices exclude applicable taxes.’ I submit it. The planned state changes from `Draft` to `In AI review`.”

**Step 3:** “The review returns two high-severity findings. The first span is ‘$10 per team member per month’. It cites `NS-FACT-010` from `NS-DOC-PRICING`, section 2.4 Historical pricing. That price was superseded by `NS-FACT-002`, which sets the current Team plan price at $12. The second span is ‘Save 20% until 30 September 2026.’ It cites `NS-FACT-003` from `NS-DOC-PRICING`, section 2.3 Launch offer. That offer expired on 30 September 2026, before our fixed evaluation date. Both findings are labelled `outdated`. The draft moves to `Needs changes`.”

**Step 4:** “I open the suggested-fix view. The first correction is to replace ‘$10’ with ‘$12’ and refer to `NS-FACT-002`. The second correction is to remove the expired offer, or mark it clearly as historical. The important point is that nothing changes until a person confirms it. This is where Intent Lock would check that the author’s meaning is preserved. Intent Lock is planned; if it is not live, I will say so.”

**Step 5:** “I resubmit the revised text: ‘The Team plan costs $12 per team member per month, billed annually. Prices exclude applicable taxes.’ In this simulated re-review, the two findings are gone. The draft moves to `In human review`.”

**Step 6:** “Finally, a Manager opens the draft in human review. The Manager can approve or reject. The AI cannot approve, reject or publish. I click `Approve` as the authorised person. The state becomes `Approved`. The revision history shows the original and revised text. The audit trace shows each transition: `Draft`, `In AI review`, `Needs changes`, `In AI review`, `In human review`, `Approved`. If this screen is not live, it is a simulated trace from the planned workflow.”

**Close:** “Trueline does not promise perfect review, and I am not showing a score or benchmark. The value is a review that is grounded, explainable, human-approved and recorded.”

### Three likely audience questions and honest answers

**Q1: Does the AI approve content?**

No. AI is planned to explain findings and suggest corrections. A person with approval permission makes the decision. AI cannot approve, reject, or publish content. If the approval screen is a mockup, say so.

**Q2: What if the AI cites a wrong rule?**

The design goal is citation validation. Every finding should cite a real rule or fact ID in the selected pack. An invalid citation should be discarded or downgraded. This is a design goal to be tested; I am not claiming it is proven. In this demo, the citations are the exact sample-data citations for `NS-DRAFT-06`.

**Q3: How do you know the offer is expired?**

The demo uses the fixed evaluation date `23 October 2026`, not the system clock. `NS-FACT-003` is marked `expired` and ended on 30 September 2026. That is why the second finding is real for this demo.

### What we must not claim

- Do not say a feature is live unless the owners confirm it is ready and tested.
- Do not say the AI approves, rejects, or publishes content.
- Do not claim a score, benchmark, quality rate, or measured result.
- Do not claim citations are always valid; say citation validation is a design goal to be tested.
- Do not claim Intent Lock is present unless it is shown and tested.
- Do not claim the audit log is tamper-proof in production unless it is shown and tested.
- Do not say the revised draft is published.
- Do not present the fictional Northstar pack as real company policy.
- Do not imply that 23 October 2026 is the current date; it is the fixed evaluation date.
- Do not call a mockup or simulated screen “live”.
