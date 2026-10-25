# Trueline Product Requirements (Extended)

This document extends the team's base document, [`docs/requirements.md`](requirements.md). `docs/requirements.md` stays the team's base document. This file adds detail, requirement IDs, and acceptance criteria. It does not replace the base document.

Status: planning document only. No feature in this document is claimed to be built or tested.

## Implementation status

Status labels used in this document and in `docs/demo-script.md`:

| Label | Meaning |
|---|---|
| Implemented and tested | A runnable check exists and its result is on record. |
| Code exists, not verified | Code is in the repository, but nobody has checked it against these requirements. |
| Planned | Described only. Nothing is built or tested for it. |

Current status by area:

| Area | Status | Evidence |
|---|---|---|
| Northstar sample data (guidelines, drafts, expected findings, evaluation matrix) | Implemented and tested, for data consistency only | The five validation scripts pass and 36 unit tests pass (checked at commit `ff77689`). This shows the data files agree with each other. It does not show that any product feature works. |
| Validation scripts in `tests/` | Implemented and tested | `python tests\run_all_validations.py` and `python -m unittest tests.test_northstar_validators` |
| AI review engine and backend review API | Code exists, not verified against these requirements | They are on other branches or on `main`. This document does not claim they meet any FR or AC. Open mapping questions are listed in `docs/dataset-mapping.md`. |
| FR-01 to FR-33, NFR-01 to NFR-12, AC-01 to AC-25 | Planned | No product test has been run. Every row below stays `Status: planned` until a test result is on record. |
| Evaluation scores (precision, recall, citation validity) | NOT RUN / UNMEASURED | No score is reported anywhere in this document. |

## 1. Problem statement

Trueline is planned as a **pre-publication review layer**. It is not a content generator, a content management system, or a social-media scheduler.

Small teams often publish content that drifts from their brand rules. A draft can use a banned term, make an unsupported claim, rely on an expired fact, or use an inconsistent product name. Reviewers may not have the guideline open. They may not know which approved fact is current. They may also have no clear record of who approved what, or why.

Trueline is planned to help a team check a draft against an approved brand guideline pack before publication. It should explain each finding, cite the rule or fact behind it, suggest a fix, and keep a human approval record.

The product goal is not to replace human judgement. The goal is to make brand review easier to inspect, repeat, and audit.

## 2. Target users and use cases

### Organisation setting

Trueline is planned for one organisation workspace at a time. The organisation can hold one or more brand guideline packs. The demo organisation is the fictional Northstar Planner brand.

The content audiences in the sample data include team leads and operations managers at small businesses. Other sample audiences include prospects, customers, and first-time visitors. These are audiences for the content. They are not application roles.

### Application roles

The four application roles are planned. The exact permissions are proposals and need team approval. See Section 11.

| Role | Planned purpose | Example use cases |
|---|---|---|
| Creator | Writes and submits content for review. | Create a draft, view findings, apply a suggested fix, resubmit a revised draft. |
| Reviewer | Checks findings, citations, and suggested fixes. | Review a draft, request changes, confirm that a fix keeps the intended meaning. |
| Manager | Owns the review queue and approves or rejects reviewed content. | Assign a reviewer, approve a draft, reject a draft, view team reports. |
| Admin | Manages the organisation workspace, guideline packs, users, and roles. | Load guidelines, manage users, change roles, view audit records. |

### Use cases

| ID | Use case | Main role |
|---|---|---|
| UC-01 | Browse the brand guidelines library and see rule and fact status. | Creator, Reviewer, Admin |
| UC-02 | Create a text draft and choose a guideline pack. | Creator |
| UC-03 | Submit a draft for review. | Creator |
| UC-04 | Review explainable findings and citations. | Reviewer |
| UC-05 | Apply, edit, or reject a suggested fix and confirm the intended meaning. | Creator, Reviewer |
| UC-06 | Request changes, approve, or reject a draft. | Reviewer, Manager, Admin |
| UC-07 | View revision history and audit records. | Reviewer, Manager, Admin |
| UC-08 | Manage guideline packs, rules, facts, users, and roles. | Admin |

## 3. User journey

The workflow states are planned as:

`Draft → In AI review → Needs changes → In human review → Approved` or `Rejected`

AI is not planned to approve, reject, or publish content. A person makes the approval decision.

| Step | Actor | Action | State after the step | Audit note |
|---|---|---|---|---|
| 1 | Admin or Manager | Load or select an approved guideline pack. | No draft state yet | Record the selected pack and version. |
| 2 | Creator | Create a text draft with title, channel, audience, purpose, and body. | Draft | Record the draft creation. |
| 3 | Creator | Submit the draft for review. | In AI review | Record who submitted it and when. |
| 4 | System | Run computed checks first, then use AI only for judgement that computed rules cannot decide. | In AI review | Record the guideline pack and review round. |
| 5 | System | Return findings and a review outcome. | Needs changes if findings block review; otherwise In human review | Record the findings and the transition. |
| 6 | Creator | Read the findings, apply or edit fixes, and confirm the intended meaning. | Needs changes | Record each accepted or rejected fix. |
| 7 | Creator | Resubmit the revised draft. | In AI review | Record the new review round. |
| 8 | System | Re-check the draft and the applied fixes. | Needs changes or In human review | Record the new findings and the transition. |
| 9 | Reviewer | Review the findings, citations, and suggested fixes. | In human review | Record the reviewer action. |
| 10 | Reviewer | Request changes, or recommend approval. | Needs changes or In human review | Record the request or recommendation. |
| 11 | Manager or Admin | Approve or reject the draft. | Approved or Rejected | Record the decision, the decision-maker, and the reason. |
| 12 | System | Keep the final revision and append audit events. | Approved or Rejected | Record the final state and revision link. |

Open question: if a draft is Rejected, does it stay rejected, or return to Draft for another revision? This is listed in Section 11.

## 4. Functional requirements

All requirements in this section are **Status: planned; Tier: MVP**. Each subsection names the MVP feature that its requirements belong to.

### MVP feature 1 — Guidelines library

| ID | Requirement | Status / tier |
|---|---|---|
| FR-01 | The system shall let an Admin or Manager create or import a guideline pack with a name, owner, and version. | Status: planned; Tier: MVP |
| FR-02 | The system shall store each guideline source with a document ID, title, section, and owner role. | Status: planned; Tier: MVP |
| FR-03 | The system shall store rules with a rule ID, category, check method, default severity, source document, section, and status. | Status: planned; Tier: MVP |
| FR-04 | The system shall store approved facts with a fact ID, statement, owner role, source, valid-from date, expiry date, and status. | Status: planned; Tier: MVP |
| FR-05 | The system shall let users browse and search rules and facts and see active, expired, and superseded labels. | Status: planned; Tier: MVP |

### MVP feature 2 — Grounded review

| ID | Requirement | Status / tier |
|---|---|---|
| FR-06 | The system shall let a Creator create a text draft with a title, channel, audience, purpose, and body. | Status: planned; Tier: MVP |
| FR-07 | The system shall let a Creator select a guideline pack and submit a draft for review. | Status: planned; Tier: MVP |
| FR-08 | The system shall run computed checks before any AI judgement. | Status: planned; Tier: MVP |
| FR-09 | The system shall use AI only for judgement that computed rules cannot decide. | Status: planned; Tier: MVP |
| FR-10 | The system shall ground review in the selected guideline pack and approved facts. It shall not use general knowledge as a source of brand rules. | Status: planned; Tier: MVP |
| FR-11 | The system shall return a review result with findings and a draft outcome such as needs changes, needs human judgement, or no findings. | Status: planned; Tier: MVP |
| FR-12 | The system shall not publish, schedule, or send content to a CMS or social platform. | Status: planned; Tier: MVP |

### MVP feature 3 — Explainable findings with citations

| ID | Requirement | Status / tier |
|---|---|---|
| FR-13 | The system shall create findings with an ID, span, severity, label, explanation, citation, and suggested fix. | Status: planned; Tier: MVP |
| FR-14 | The system shall cite a real rule or fact ID for each finding. | Status: planned; Tier: MVP |
| FR-15 | The system shall discard or downgrade a finding whose citation ID does not exist in the selected guideline pack. | Status: planned; Tier: MVP |
| FR-16 | The system shall label a finding needs human judgement when evidence is missing or ambiguous. | Status: planned; Tier: MVP |
| FR-17 | The system shall label a claim unsupported when approved facts do not support it. | Status: planned; Tier: MVP |
| FR-18 | The system shall label a statement contradicted when it conflicts with an active fact, and outdated when it relies on an expired or superseded fact. | Status: planned; Tier: MVP |
| FR-19 | The system shall show the cited source document, section, and a plain-language AI-use disclosure with the review. | Status: planned; Tier: MVP |

### MVP feature 4 — Suggested fixes and Intent Lock

| ID | Requirement | Status / tier |
|---|---|---|
| FR-20 | The system shall suggest a fix for each finding where a fix is possible. | Status: planned; Tier: MVP |
| FR-21 | The system shall let a Creator apply, edit, or reject a suggested fix. | Status: planned; Tier: MVP |
| FR-22 | The system shall re-check an applied fix against the same rule before accepting it. | Status: planned; Tier: MVP |
| FR-23 | The system shall run an Intent Lock check that compares the intended meaning before and after a fix. | Status: planned; Tier: MVP |
| FR-24 | The system shall not silently rewrite content. The Creator must confirm every change. | Status: planned; Tier: MVP |

### MVP feature 5 — Human approval and role-based review

| ID | Requirement | Status / tier |
|---|---|---|
| FR-25 | The system shall support four application roles: Creator, Reviewer, Manager, and Admin. | Status: planned; Tier: MVP |
| FR-26 | The system shall enforce role permissions for submit, review, request changes, approve, reject, manage guidelines, and manage users. | Status: planned; Tier: MVP |
| FR-27 | The system shall move a draft through the planned workflow states and record each transition. | Status: planned; Tier: MVP |
| FR-28 | The system shall let an authorised Reviewer request changes and an authorised Manager or Admin approve or reject a draft. | Status: planned; Tier: MVP |
| FR-29 | The system shall prevent AI from approving, rejecting, or publishing content. | Status: planned; Tier: MVP |

### MVP feature 6 — Revision history and audit logs

| ID | Requirement | Status / tier |
|---|---|---|
| FR-30 | The system shall keep revision history for each draft and review round. | Status: planned; Tier: MVP |
| FR-31 | The system shall write an append-only audit event for every state transition, approval, rejection, role change, and guideline change. | Status: planned; Tier: MVP |
| FR-32 | The system shall let authorised users view revision history and audit events. | Status: planned; Tier: MVP |
| FR-33 | The system shall keep audit events immutable and attributable to a user or a named system actor. | Status: planned; Tier: MVP |

## 5. Non-functional requirements

All requirements in this section are **Status: planned; Tier: MVP**.

| ID | Area | Requirement | Status / tier |
|---|---|---|---|
| NFR-01 | Explainability and traceability | Every displayed finding shall show a plain-language explanation, a span, a severity, a label, and a citation to a real rule or fact ID. | Status: planned; Tier: MVP |
| NFR-02 | Citation validity target | Target: 100% of displayed findings cite a guideline or fact ID that exists in the selected pack. This is a target, not a result. | Status: planned; Tier: MVP |
| NFR-03 | Finding accuracy targets | Precision, recall, and false-positive targets shall be set by the team. No numeric target is set in this document. Any future figure is an assumption, to be confirmed with the team. | Status: planned; Tier: MVP |
| NFR-04 | Privacy and organisation isolation | Organisation data shall be separated so that one organisation cannot read another organisation's drafts, guidelines, users, or audit records. | Status: planned; Tier: MVP |
| NFR-05 | Role-based access | Role permissions shall be enforced on the server, not only hidden in the interface. | Status: planned; Tier: MVP |
| NFR-06 | Auditability | Audit events shall be append-only, timestamped, and attributable. | Status: planned; Tier: MVP |
| NFR-07 | Accessibility of the interface | The review interface shall use readable labels, keyboard access, and clear focus states. The full accessibility target is to be confirmed with the team. Any future figure is an assumption, to be confirmed with the team. | Status: planned; Tier: MVP |
| NFR-08 | Performance expectations | Review response-time and throughput targets shall be confirmed with the team. Any future latency or throughput figure is an assumption, to be confirmed with the team. | Status: planned; Tier: MVP |
| NFR-09 | Reliability and invalid AI fallback | If AI output is unavailable, invalid, or incomplete, the system shall keep computed findings, label unresolved items needs human judgement, and avoid a confident claim. | Status: planned; Tier: MVP |
| NFR-10 | AI disclosure | The review interface shall say that AI is used for judgement and that a person makes the approval decision. | Status: planned; Tier: MVP |
| NFR-11 | Data retention | Retention periods for drafts, findings, revisions, and audit records shall be confirmed with the team. Any future figure is an assumption, to be confirmed with the team. | Status: planned; Tier: MVP |
| NFR-12 | AI output validation | AI output shall be checked against a required schema and the guideline pack before it is shown as a finding. | Status: planned; Tier: MVP |

## 6. MVP scope and explicit non-goals

### MVP scope

The MVP is planned around six feature groups.

| MVP feature | What it covers |
|---|---|
| Guidelines library | Load and browse guideline sources, rules, and approved facts. |
| Grounded review | Review a text draft against the selected pack, with computed checks first and AI judgement second. |
| Explainable findings with citations | Show findings with spans, labels, severities, explanations, and real citations. |
| Suggested fixes and Intent Lock | Suggest fixes, let a person apply or edit them, re-check them, and confirm meaning. |
| Human approval and role-based review | Use Creator, Reviewer, Manager, and Admin roles with human approval. |
| Revision history and audit logs | Keep revisions and append-only audit events. |

The base document lists five MVP bullets. This document uses six feature groups for traceability. The difference is listed in Section 11.

### Explicit non-goals

Trueline is **not** planned to:

- Generate final content.
- Review video.
- Publish directly to a CMS or social platform.
- Approve content automatically.
- Rewrite content silently.
- Replace human judgement.

Later features are listed in Section 10. They are not part of the MVP.

## 7. Assumptions and limitations

- The application is not built. This document is a plan.
- The MVP is planned for text review. Document upload formats are not defined. See Section 11.
- The demo uses one fictional brand and one fictional guideline pack.
- The data files are fictional and must not be treated as real company policy.
- The fixed evaluation date is `2026-10-23`. Fact status and expiry checks must use this date, not the system clock. OPEN: the backend-review-api branch derives fact validity from the system clock, so this requirement is not met by that code yet (see `docs/dataset-mapping.md`).
- The sample drafts and test cases are small and do not represent production traffic.
- The guideline `owner_role` values are content-governance metadata. They are not application roles.
- AI output can be incomplete, invalid, or unsupported. Human review remains necessary.
- Approval means the content is approved inside Trueline. It does not mean the content is published.
- No real user interviews, benchmarks, or production measurements are used in this document.
- Exact performance, accuracy, retention, and accessibility targets are not set here. They need team confirmation.

## 8. Risks and mitigations

Likelihood and impact are initial planning estimates, not measured results.

| ID | Risk | Likelihood | Impact | Mitigation | Status / tier |
|---|---|---|---|---|---|
| RISK-01 | False positives make reviewers distrust the review. | Medium | High | Use computed rules first, show citations, and label uncertain findings needs human judgement. | Status: planned; Tier: MVP |
| RISK-02 | False negatives let a violation pass. | Medium | High | Combine computed checks, AI review, and human review; track missed findings in test rounds. | Status: planned; Tier: MVP |
| RISK-03 | AI returns an invalid or misleading citation. | Medium | High | Validate every citation ID against the selected guideline pack and discard invalid findings. | Status: planned; Tier: MVP |
| RISK-04 | Expired or superseded facts are treated as current. | Medium | High | Use the fixed evaluation date, show fact status, and label outdated statements. | Status: planned; Tier: MVP |
| RISK-05 | A user bypasses role permissions. | Low | High | Enforce permissions on the server and log every privileged action. | Status: planned; Tier: MVP |
| RISK-06 | Audit records are edited or deleted. | Low | High | Use append-only records and restrict audit access to authorised roles. | Status: planned; Tier: MVP |
| RISK-07 | A suggested fix changes the author's intended meaning. | Medium | High | Run Intent Lock, require human confirmation, and re-check the fix. | Status: planned; Tier: MVP |
| RISK-08 | AI output is unavailable or malformed. | Medium | Medium | Keep computed findings, validate output, and label unresolved items needs human judgement. | Status: planned; Tier: MVP |
| RISK-09 | Sensitive content crosses organisation boundaries. | Low | High | Isolate organisation data and test access controls before any pilot. | Status: planned; Tier: MVP |
| RISK-10 | The documentation overclaims what the product can do. | Medium | Medium | Use planned language, separate MVP from Later features, and show no unmeasured scores. | Status: planned; Tier: MVP |

## 9. Acceptance criteria

Each criterion is written as a testable check. Where a structured test case exists in `data/evaluation-dataset.json`, it is listed. Where no structured test case exists, the row says `No NS-TC; manual test needed`.

All criteria are **Status: planned; Tier: MVP**.

| ID | Testable criterion | Checks FR | Test evidence | Rule or fact ID | Status / tier |
|---|---|---|---|---|---|
| AC-01 | Given NS-DRAFT-01, when the review runs, then the banned term "revolutionary" is a finding with a citation to NS-BAN-001 and the correct span. | FR-13, FR-14, FR-19 | NS-TC-001 | NS-BAN-001; NS-DRAFT-01-F1 | Status: planned; Tier: MVP |
| AC-02 | Given NS-DRAFT-03, when the review runs, then the missing tax sentence is a finding with a citation to NS-REQ-001. | FR-13, FR-14 | NS-TC-007 | NS-REQ-001; NS-DRAFT-03-F1 | Status: planned; Tier: MVP |
| AC-03 | Given NS-DRAFT-04, when the review runs, then the market-position claim is labelled unsupported with a citation to NS-CLAIM-001. | FR-17 | NS-TC-008 | NS-CLAIM-001; NS-DRAFT-04-F1 | Status: planned; Tier: MVP |
| AC-04 | Given NS-DRAFT-05, when the review runs, then the Starter limit statement is labelled contradicted with a citation to NS-FACT-001. | FR-18 | NS-TC-010 | NS-FACT-001; NS-DRAFT-05-F1 | Status: planned; Tier: MVP |
| AC-05 | Given NS-DRAFT-06, when the review runs, then the expired launch offer is labelled outdated with a citation to NS-FACT-003. | FR-18 | NS-TC-013 | NS-FACT-003; NS-DRAFT-06-F2 | Status: planned; Tier: MVP |
| AC-06 | Given NS-DRAFT-06, when the review runs, then the old price is labelled outdated with a citation to NS-FACT-010. | FR-18 | NS-TC-012 | NS-FACT-010; NS-DRAFT-06-F1 | Status: planned; Tier: MVP |
| AC-07 | Given NS-DRAFT-08, when the calendar wording is ambiguous, then the finding is labelled needs human judgement with a citation to NS-FACT-006. | FR-16 | NS-TC-017 | NS-FACT-006; NS-DRAFT-08-F1 | Status: planned; Tier: MVP |
| AC-08 | Given the Assist Suggestions availability text, when the wording is ambiguous, then the result is needs human judgement with a citation to NS-FACT-009. | FR-16 | NS-TC-053 | NS-FACT-009 | Status: planned; Tier: MVP |
| AC-09 | Given the positive draft cases, when findings are displayed, then every cited ID exists in the guideline pack. | FR-14, NFR-02 | NS-TC-001 through NS-TC-026 | NS-BAN-001 is one example | Status: planned; Tier: MVP |
| AC-10 | Given a test double that returns a finding with an invalid citation ID, when the finding is validated, then it is discarded or downgraded and not shown as grounded. | FR-15, NFR-09 | No NS-TC; manual test needed | Test double only | Status: planned; Tier: MVP |
| AC-11 | Given the compliant control draft NS-DRAFT-10, when the review runs, then no finding is returned. | FR-11, NFR-03 | NS-TC-027 | NS-DRAFT-10 | Status: planned; Tier: MVP |
| AC-12 | Given the revised drafts, when the review runs, then each revised draft returns no finding. | FR-11, NFR-03 | NS-TC-028 through NS-TC-036 | NS-DRAFT-01 through NS-DRAFT-09 | Status: planned; Tier: MVP |
| AC-13 | Given the edge snippets, when the review runs, then each edge input returns no finding. | FR-11, NFR-03 | NS-TC-037 through NS-TC-042 | No expected finding | Status: planned; Tier: MVP |
| AC-14 | Given a finding with a suggested fix, when the fix is applied, then a re-check raises no finding for the same rule. | FR-20, FR-22 | NS-TC-001 | NS-BAN-001; NS-DRAFT-01-F1 | Status: planned; Tier: MVP |
| AC-15 | Given a fix that changes the intended meaning, when Intent Lock runs, then the fix is blocked and the person must revise it. | FR-23, FR-24 | No NS-TC; manual test needed | Test case to be added | Status: planned; Tier: MVP |
| AC-16 | Given a draft in human review, when an authorised Manager approves it, then the state becomes Approved and an audit event is written. | FR-27, FR-28 | No NS-TC; manual test needed | Workflow test to be added | Status: planned; Tier: MVP |
| AC-17 | Given a Creator, when that user tries to approve a draft, then the action is denied. | FR-25, FR-26 | No NS-TC; manual test needed | Role test to be added | Status: planned; Tier: MVP |
| AC-18 | Given a draft ready for a decision, when AI is asked to decide, then AI cannot approve, reject, or publish it. | FR-29 | No NS-TC; manual test needed | AI boundary test to be added | Status: planned; Tier: MVP |
| AC-19 | Given a state transition, when it happens, then one append-only audit event records the actor, time, old state, and new state. | FR-31, FR-33 | No NS-TC; manual test needed | Audit test to be added | Status: planned; Tier: MVP |
| AC-20 | Given an existing audit event, when a user tries to edit or delete it, then the action is denied. | FR-32, FR-33 | No NS-TC; manual test needed | Audit test to be added | Status: planned; Tier: MVP |
| AC-21 | Given a review that mentions Assist Suggestions, when findings are shown, then the required AI disclosure is visible. | FR-19, NFR-10 | NS-TC-052 | NS-REQ-002 | Status: planned; Tier: MVP |
| AC-22 | Given a suggested fix, when the Creator has not confirmed it, then the draft text does not change. | FR-21, FR-24 | No NS-TC; manual test needed | No silent rewrite test | Status: planned; Tier: MVP |
| AC-23 | Given a draft with several review rounds, when a user opens revision history, then each round is visible in order. | FR-30, FR-32 | No NS-TC; manual test needed | Revision test to be added | Status: planned; Tier: MVP |
| AC-24 | Given a role change, when an Admin changes a user's role, then the change is recorded in the audit log. | FR-31, FR-33 | No NS-TC; manual test needed | Role audit test to be added | Status: planned; Tier: MVP |
| AC-25 | Given the security wording text, when the wording is ambiguous, then the result is needs human judgement with a citation to NS-FACT-004. | FR-16 | NS-TC-054 | NS-FACT-004 | Status: planned; Tier: MVP |

## 10. Later features (NOT MVP)

These items are **not** part of the MVP. They are planned only as possible later work.

| Later feature | Planned scope | Status / tier |
|---|---|---|
| Fact Ledger improvements | Better fact lifecycle tools, owner alerts, and richer fact history. | Status: planned; Tier: Later |
| Visual and accessibility content checks | Checks for visual content and accessibility issues in content, separate from UI accessibility in NFR-07. | Status: planned; Tier: Later |
| Guideline Insights | Summary views and trends across guideline usage and findings. | Status: planned; Tier: Later |
| Brand Precedents | A library of approved examples for reviewers, if time allows. | Status: planned; Tier: Later |
| Privacy modes | Additional privacy options, if time allows. | Status: planned; Tier: Later |

## 11. Open questions for the team

1. The base document lists five MVP bullets. This document uses six MVP feature groups. How should the team align the two documents without changing the base document?
2. Are the application roles Creator, Reviewer, Manager, and Admin final? What exact permission does each role have?
3. Can a Creator review or approve their own draft? Can a Reviewer approve, or only a Manager or Admin?
4. If a draft is Rejected, does it stay rejected, or return to Draft for another revision?
5. Does `human_review_required` mean one finding needs a person, or the whole draft must enter human review?
6. Should the docs use actual rule IDs such as NS-BAN-001, or a generic NS-RULE label? The data files use category-based rule IDs.
7. The structured test cases cover review findings well. They do not yet cover workflow, role permissions, audit, Intent Lock, or invalid-citation handling. Who will add those tests?
8. Should requirements define logical objects only, with API fields left to `docs/api-contracts.md`?
9. What are the approved targets for accuracy, latency, retention, and accessibility?
10. Is the MVP text-only, or are document uploads in scope?
11. Which Later feature, if any, has priority after the MVP?

## 12. Glossary

| Term | Beginner-friendly meaning |
|---|---|
| Finding | One specific issue in a draft. It has a span, label, severity, explanation, citation, and suggested fix. |
| Citation | The rule or fact ID and source section that supports a finding. A citation must point to a real guideline entry. |
| Intent Lock | A planned check that a suggested fix keeps the author's intended meaning and does not add a new claim. |
| Fact Ledger | The planned library of approved facts, with dates and status. Improvements to it are a Later feature in Section 10. |
| Audit log | An append-only record of who did what, when, and to which draft. |
| RAG | Retrieval-augmented generation. An AI method that uses retrieved guideline text as context instead of relying only on model memory. |
| Computed check | A deterministic rule check. The same input should produce the same result. |
| Grounded | Supported by a real rule or fact from the selected guideline pack. |
| Needs human judgement | A label for a finding that is uncertain and needs a person to decide. |
| Unsupported | A label for a claim that the approved facts do not support. |
| RBAC | Role-based access control. Permissions are tied to roles such as Creator, Reviewer, Manager, and Admin. |
