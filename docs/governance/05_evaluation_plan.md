# Evaluation Plan

**Artifact:** `05_evaluation_plan.md`
**Version:** 1.0.0
**Decision Date:** 2026-07-13
**Owner:** `HUMAN_REVIEWER_01` (Evaluation Owner)
**Reviewer:** `HUMAN_REVIEWER_01` (Domain Steward)
**Status:** APPROVED

## Purpose

Defines how recommendation quality is measured using a labelled reviewer-decision set, precision/recall, override rate, throughput, reliability, cost/latency, and sensitive-evidence compliance.

## Labelled evaluation set

A labelled set of known-correct semantic mappings for the synthetic Bronze tables will be maintained in `evals/labelled_set/`.

| Source table | Source column | Expected business name | Expected ontology concept | Expected domain | Expected privacy class |
|---|---|---|---|---|---|
| bronze_policy | policy_id | Policy Identifier | Policy.Identifier | Policy | INTERNAL |
| bronze_policy | policy_number | Policy Number | Policy.PolicyNumber | Policy | INTERNAL |
| bronze_policy | policy_status | Policy Status | Policy.Status | Policy | INTERNAL |
| bronze_policy | effective_date | Policy Effective Date | Policy.EffectiveDate | Policy | INTERNAL |
| bronze_policy | expiration_date | Policy Expiration Date | Policy.ExpirationDate | Policy | INTERNAL |
| bronze_policy | product_code | Insurance Product Code | Product.Code | Shared | INTERNAL |
| bronze_policy | insured_party_id | Insured Party Identifier | Party.Identifier | Shared | INTERNAL |
| bronze_policy | source_updated_ts | Source Updated Timestamp | Technical.SourceUpdatedTimestamp | Shared | INTERNAL |
| bronze_policyholder | party_id | Party Identifier | Party.Identifier | Shared | INTERNAL |
| bronze_policyholder | party_type | Party Type | Party.Type | Shared | INTERNAL |
| bronze_policyholder | display_name | Display Name | (unresolved) | Shared | PERSONAL_DATA |
| bronze_policyholder | contact_channel | Contact Channel | (unresolved) | Shared | INTERNAL |
| bronze_policyholder | source_updated_ts | Source Updated Timestamp | Technical.SourceUpdatedTimestamp | Shared | INTERNAL |
| bronze_claim | claim_id | Claim Identifier | Claim.Identifier | Claims | INTERNAL |
| bronze_claim | policy_id | Policy Identifier | Policy.Identifier | Policy | INTERNAL |
| bronze_claim | loss_date | Loss Date | Claim.LossDate | Claims | INTERNAL |
| bronze_claim | claim_status | Claim Status | Claim.Status | Claims | INTERNAL |
| bronze_claim | claimed_amount | Claimed Amount | Claim.ClaimedAmount | Claims | INTERNAL |
| bronze_claim | source_updated_ts | Source Updated Timestamp | Technical.SourceUpdatedTimestamp | Shared | INTERNAL |

## Metrics

| Metric | How to measure | Target direction | Baseline |
|---|---|---|---|
| **Semantic classification coverage** | % of synthetic fields receiving a proposed classification | >= 90% | 100% (MVP) |
| **Mapping precision** | Correct mappings / total proposed mappings | Improve against baseline | To be measured |
| **Mapping recall** | Correct mappings / total labelled correct mappings | Improve against baseline | To be measured |
| **Reviewer override rate** | Materially changed/rejected / reviewed recommendations | Understand and reduce by iteration | To be measured |
| **Reviewer throughput** | Median time from recommendation to final decision | <= 3 business days (architect/steward), <= 2 business days (privacy) | To be measured |
| **Workflow reliability** | Failed/retried runs and targeted-reprocessing success rate | Demonstrate controlled recovery | 0 failures (MVP) |
| **Cost and latency** | Compute usage and elapsed time per source object and workflow stage | Meet pilot budget | ~2 min (MVP run) |
| **Sensitive-evidence compliance** | Inputs passing evidence-classification controls | 100% | 100% (MVP) |

## Reviewer-decision capture

Each review decision is captured with:
- `source_table`, `source_column` (what was reviewed)
- `recommended_reviewer_role` (who should review)
- `review_reason` (why it was routed)
- `queue_status` (OPEN, CLOSED)
- Reviewer decision: APPROVED, MODIFIED, REJECTED, DEFERRED
- `review_rationale` (why the reviewer made their decision)
- Timestamp of decision

## Evidence sources

| Evidence source | Location |
|---|---|
| MVP run evidence | `docs/evidence/mvp_run_evidence.json` |
| MVP evidence summary | `docs/evidence/MVP_RUN_EVIDENCE.md` |
| Labelled set | `evals/labelled_set/` (to be created) |
| Review queue | Configured output schema table `source_intelligence_review_queue` (Databricks) |
| Job run history | Databricks job run API |

## Open questions

- [ ] Who is the named evaluation owner?
- [ ] Should the labelled set be a JSON file or a Delta table?
- [ ] What is the acceptable precision/recall baseline for Source Intelligence?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed evaluation plan | Agent (Cline) |
| 1.0.0 | 2026-07-13 | Approved with the independently reviewed 26-record labelled set | `HUMAN_REVIEWER_01` |
