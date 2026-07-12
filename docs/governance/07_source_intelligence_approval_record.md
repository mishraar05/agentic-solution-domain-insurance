# Source Intelligence Human Approval Record

**Version:** 0.1.0  
**Status:** PROPOSED — awaiting named human decisions  
**Decision date:** Pending

This record captures the human assignments and decisions that an automated
agent is prohibited from inventing. Completing the fields does not authorize
source writes or deployment DDL; the solution remains recommendation-only.

## Named assignments

| Role | Named human | Accepted assignment? | Date |
|---|---|---|---|
| Data Architect | Pending | Pending | Pending |
| Domain Steward | Pending | Pending | Pending |
| Privacy Steward | Pending | Pending | Pending |
| Evaluation Owner | Pending | Pending | Pending |
| Sponsor | Pending | Pending | Pending |

## Governance decisions

| Artifact or decision | Accountable role | Decision | Rationale | Date |
|---|---|---|---|---|
| Policy first-release scope | Data Architect | Pending | Pending | Pending |
| Evidence classification matrix | Privacy Steward | Pending | Pending | Pending |
| Reviewer model and service levels | Sponsor | Pending | Pending | Pending |
| Confidence component weights | Evaluation Owner | Pending | Pending | Pending |
| Low-confidence threshold (`0.75`) | Evaluation Owner | Pending | Pending | Pending |
| Evidence-coverage floor (`0.60`) | Evaluation Owner | Pending | Pending | Pending |
| Independently reviewed labelled set | Domain Steward | Pending | Pending | Pending |
| Source Documentation prompt and context policy | Privacy Steward | Pending | Pending | Pending |
| Source Documentation quality acceptance | Domain Steward | Pending | Pending | Pending |
| Source Intelligence gate decision | Sponsor | Pending | Pending | Pending |

Permitted decisions are `APPROVED`, `MODIFIED`, `REJECTED`, or `DEFERRED`.
Every decision requires a rationale. If a value is modified, update the owning
governance artifact and its version before recording the release gate as passed.

## Gate declaration

**Source Intelligence gate:** NOT PASSED  
**Knowledge-driven work eligibility:** LOCKED

Only the named Sponsor may change the gate declaration after all runtime,
evaluation, calibration, and governance evidence is complete.
