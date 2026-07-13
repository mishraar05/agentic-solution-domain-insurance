# Source Intelligence Human Approval Record

**Version:** 1.0.0
**Status:** APPROVED
**Decision date:** 2026-07-13

This record captures the human assignments and decisions that an automated
agent is prohibited from inventing. Completing the fields does not authorize
source writes or deployment DDL; the solution remains recommendation-only.

## Named assignments

| Role | Named human | Accepted assignment? | Date |
|---|---|---|---|
| Data Architect | `HUMAN_REVIEWER_01` | YES | 2026-07-13 |
| Domain Steward | `HUMAN_REVIEWER_01` | YES | 2026-07-13 |
| Privacy Steward | `HUMAN_REVIEWER_01` | YES | 2026-07-13 |
| Evaluation Owner | `HUMAN_REVIEWER_01` | YES | 2026-07-13 |
| Sponsor | `HUMAN_REVIEWER_01` | YES | 2026-07-13 |

## Governance decisions

| Artifact or decision | Accountable role | Decision | Rationale | Date |
|---|---|---|---|---|
| Policy first-release scope | Data Architect | APPROVED | Approved unchanged for the governed pilot. | 2026-07-13 |
| Evidence classification matrix | Privacy Steward | APPROVED | Approved unchanged; prohibited evidence remains prohibited. | 2026-07-13 |
| Reviewer model and service levels | Sponsor | APPROVED | Roles and decision rights accepted for the pilot. | 2026-07-13 |
| Confidence component weights | Evaluation Owner | APPROVED | Existing 0.35/0.20/0.25/0.10/0.10 weights approved. | 2026-07-13 |
| Low-confidence threshold (`0.75`) | Evaluation Owner | APPROVED | Threshold approved unchanged. | 2026-07-13 |
| Evidence-coverage floor (`0.60`) | Evaluation Owner | APPROVED | Coverage floor approved unchanged. | 2026-07-13 |
| Independently reviewed labelled set | Domain Steward | APPROVED | All 26 labels confirmed; four remain intentionally unresolved. | 2026-07-13 |
| Source Documentation prompt and context policy | Privacy Steward | APPROVED | Prompt allow-list and privacy exclusions approved. | 2026-07-13 |
| Source Documentation quality acceptance | Domain Steward | APPROVED | Generated documentation reviewed and approved. | 2026-07-13 |
| Source Intelligence gate decision | Sponsor | APPROVED | Runtime and human gates accepted; Governed Knowledge Foundation authorized. | 2026-07-13 |

Permitted decisions are `APPROVED`, `MODIFIED`, `REJECTED`, or `DEFERRED`.
Every decision requires a rationale. If a value is modified, update the owning
governance artifact and its version before recording the release gate as passed.

## Gate declaration

**Source Intelligence gate:** PASSED
**Knowledge-driven work eligibility:** UNLOCKED FOR GOVERNED KNOWLEDGE FOUNDATION

Only the named Sponsor may change the gate declaration after all runtime,
evaluation, calibration, and governance evidence is complete.
