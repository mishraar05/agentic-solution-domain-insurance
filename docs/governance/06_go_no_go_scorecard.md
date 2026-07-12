# Go/No-Go Scorecard

**Artifact:** `06_go_no_go_scorecard.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** Sponsor (placeholder - awaiting assignment)
**Reviewer:** Architecture Lead (placeholder - awaiting assignment)
**Status:** PROPOSED

## Purpose

Defines the metrics, baselines, targets, and decision rules for the go/no-go promotion decision at the end of the pilot.

## Scorecard

| Metric | Baseline | Target | Evidence source | Owner | Status | Decision rule |
|---|---|---|---|---|---|---|
| **Evidence completeness** | 100% (MVP) | 100% | `docs/evidence/mvp_run_evidence.json` | Data Architect | PROPOSED | Go only if 100% of material recommendations have all required fields |
| **Semantic classification coverage** | 100% (MVP, 19/19 fields) | >= 90% | `source_observation_dictionary` table | Domain Steward | PROPOSED | Go only if >= 90% of fields have a proposed classification |
| **Mapping precision** | To be measured | Improve against baseline | Labelled set comparison | Evaluation Owner | DEFERRED | Go only if precision meets agreed baseline (TBD) |
| **Mapping recall** | To be measured | Improve against baseline | Labelled set comparison | Evaluation Owner | DEFERRED | Go only if recall meets agreed baseline (TBD) |
| **Reviewer override rate** | To be measured | Understand and reduce by iteration | Review queue decisions | Architecture Lead | DEFERRED | Go only if override rate is understood and trending down |
| **Reviewer throughput** | To be measured | <= 3 business days (architect/steward), <= 2 business days (privacy) | Review queue timestamps | Architecture Lead | DEFERRED | Go only if median turnaround meets SLA |
| **Workflow reliability** | 0 failures (MVP) | Demonstrate controlled recovery | Job run history | Platform Engineer | PROPOSED | Go only if failed/retried runs demonstrate targeted reprocessing |
| **Cost and latency** | ~2 min (MVP run) | Meet pilot budget | Databricks job metrics | Platform Engineer | PROPOSED | Go only if within pilot budget |
| **Sensitive-evidence compliance** | 100% (MVP) | 100% | Evidence classification checks | Privacy Steward | PROPOSED | Go only if 100% of inputs pass evidence-classification controls |
| **No auto-approval** | 0 auto-approved (MVP) | 0 | `source_observation_dictionary.approval_state` | Data Architect | PROPOSED | Go only if zero records are auto-approved |

## Promotion criteria

Before moving from Free Edition to a business trial or paid Databricks workspace:

1. A named business sponsor and data owner are assigned.
2. An approved security, privacy, retention, and access-control design exists.
3. Controlled source connectivity and service identities are designed.
4. A reviewed model-serving, AI Search, and monitoring design exists.
5. A documented incident, rollback, and support model exists.
6. All scorecard metrics with PROPOSED status are confirmed by the responsible owner.
7. All DEFERRED metrics have been measured and meet their targets.

## Current status summary

- **Phase 1 (MVP):** Complete - all acceptance gate criteria passed
- **Phase 0 (Governance):** PROPOSED - all artifacts created, awaiting human review and assignment
- **Phase 2 (Source Intelligence v1):** Not started - blocked until Phase 0 governance is reviewed

## Open questions

- [ ] Who is the named sponsor?
- [ ] What are the acceptable precision/recall baselines for mapping quality?
- [ ] What is the pilot budget for cost and latency?
- [ ] What constitutes a "controlled recovery" for workflow reliability?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed go/no-go scorecard | Agent (Cline) |
