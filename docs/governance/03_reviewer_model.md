# Reviewer Model and RACI

**Artifact:** `03_reviewer_model.md`
**Version:** 1.0.0
**Decision Date:** 2026-07-13
**Owner:** `HUMAN_REVIEWER_01` (Sponsor)
**Reviewer:** `HUMAN_REVIEWER_01` (Sponsor)
**Status:** APPROVED

## Reviewer roles

| Role | Responsibility | Decision rights | Turnaround target | Backup |
|---|---|---|---|---|
| **Data Architect** | Approves key/relationship candidates, target grain, Silver entity structure, and ontology extensions | APPROVE, MODIFY, REJECT, DEFER | 3 business days | Enterprise Architect (placeholder) |
| **Domain Steward** | Approves semantic mappings, business names, source-column descriptions, glossary proposals, domain classifications, and COTS pattern matches | APPROVE, MODIFY, REJECT, DEFER | 3 business days | Product SME (placeholder) |
| **Privacy Steward** | Approves privacy classifications, evidence-class decisions, and personal-data routing | APPROVE, MODIFY, REJECT, DEFER | 2 business days | Security/Legal (placeholder) |

## RACI matrix

| Decision type | Data Architect | Domain Steward | Privacy Steward | Sponsor | Agent |
|---|---|---|---|---|---|
| Pilot scope | A | C | C | I | R |
| Evidence classification | I | C | A | I | R |
| Key/relationship candidates | A | C | I | - | R |
| Semantic mapping | C | A | I | - | R |
| Source documentation and glossary proposal | C | A | C | - | R |
| Privacy classification | I | C | A | - | R |
| Target grain (Silver/Gold) | A | C | I | I | R |
| Financial measures | A | C | C | I | R |
| Ontology extension | A | C | C | I | R |
| Go/no-go promotion | C | C | C | A | R |

*Legend: R = Responsible, A = Accountable, C = Consulted, I = Informed*

## Service-level targets

| Metric | Target | Measurement |
|---|---|---|
| Reviewer turnaround (median) | <= 3 business days (architect/steward), <= 2 business days (privacy) | Time from queue_status = OPEN to queue_status = CLOSED |
| Reviewer throughput | 100% of open items addressed within 1 sprint | Count of open vs. closed items per sprint |
| Override rate | Track and understand; reduce by iteration | Materially changed/rejected / reviewed recommendations |

## Rules

1. **No auto-approval:** The agent never marks any recommendation as APPROVED. All material recommendations start as PROPOSED.
2. **Reviewer rationale required:** Every decision (APPROVE, MODIFY, REJECT, DEFER) must include a rationale.
3. **No silent reappearance:** Rejected or modified recommendations retain their rationale and do not silently reappear unchanged in subsequent runs.
4. **Targeted invalidation:** When a material decision changes, only downstream dependent artifacts are invalidated - not the entire pipeline.
5. **Role assignments:** Primary roles are accepted by non-PII reviewer identifier
   `HUMAN_REVIEWER_01`; backup-role placeholders remain operational follow-up.

## Open questions

- [x] Primary reviewer roles accepted by `HUMAN_REVIEWER_01`.
- [ ] Is the 3-business-day turnaround target realistic for the pilot?
- [ ] Should the backup roles be formalized or remain ad-hoc?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed reviewer model and RACI | Agent (Cline) |
| 1.0.0 | 2026-07-13 | Reviewer roles accepted under a non-PII human identifier | `HUMAN_REVIEWER_01` |
