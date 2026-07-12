# MVP Run Evidence — Phase 1 Acceptance Gate

**Run ID:** `mvp_20260712T061257Z`
**Artifact Version:** `0.1.0`
**Captured At:** 2026-07-12T06:22:22Z
**Databricks Profile:** `DEV`
**Workspace:** `https://dbc-b2d72a44-d1b1.cloud.databricks.com`
**Catalog:** `workspace` | **Schema:** `agentic_insurance_mvp`
**Job Run URL:** https://dbc-b2d72a44-d1b1.cloud.databricks.com/?o=507217943166572#job/83020287731974/run/707079892867523

## Phase 1 Acceptance Gate Results

| Acceptance Criterion | Result | Evidence |
|---|---|---|
| All five Delta tables exist | ✅ PASS | `bronze_policy`, `bronze_policyholder`, `bronze_claim`, `source_observation_dictionary`, `review_queue` |
| Every dictionary row has physical type, proposed meaning, confidence, privacy class, run ID, approval state | ✅ PASS | 19/19 rows contain all required fields |
| No dictionary row is automatically approved | ✅ PASS | 0 auto-approved rows; all 19 are `PROPOSED` |
| At least one relationship entry reaches review | ✅ PASS | 2 relationship rows in review queue (`bronze_claim.policy_id`, `bronze_policy.insured_party_id`) |
| At least one privacy-relevant entry reaches review | ✅ PASS | 1 personal-data row in review queue (`bronze_policyholder.display_name`) |
| Validation notebook completes successfully | ✅ PASS | Job run `707079892867523` — `result_state: SUCCESS` |

## Table Counts

| Table | Row Count |
|---|---|
| `bronze_policy` | 2 |
| `bronze_policyholder` | 2 |
| `bronze_claim` | 2 |
| `source_observation_dictionary` | 19 |
| `review_queue` | 4 |

## Validation Summary

| Metric | Value |
|---|---|
| Dictionary rows | 19 |
| Null confidence rows | 0 |
| Auto-approved rows | 0 |
| Low-confidence rows (< 0.75) | 2 |
| Personal-data rows | 1 |
| Relationship rows | 2 |

## Domain Distribution

| Domain | Approval State | Count |
|---|---|---|
| Claims | PROPOSED | 4 |
| Policy | PROPOSED | 8 |
| Shared | PROPOSED | 7 |

## Review Queue

| Source Table | Source Column | Reviewer Role | Review Reason |
|---|---|---|---|
| bronze_claim | policy_id | DATA_ARCHITECT | Inferred relationship requires confirmation |
| bronze_policy | insured_party_id | DATA_ARCHITECT | Inferred relationship requires confirmation |
| bronze_policyholder | contact_channel | DOMAIN_STEWARD | Confidence below configured threshold |
| bronze_policyholder | display_name | PRIVACY_STEWARD | Privacy classification requires review |

## Reproducible Queries

```sql
-- Verify all tables exist
SHOW TABLES IN workspace.agentic_insurance_mvp;

-- Inspect the source observation dictionary
SELECT source_table, source_column, physical_type, key_role,
       relationship_evidence, proposed_business_name, ontology_concept_id,
       domain, confidence_score, privacy_class, approval_state,
       run_id, artifact_version
FROM workspace.agentic_insurance_mvp.source_observation_dictionary
ORDER BY source_table, ordinal_position;

-- Inspect the review queue
SELECT source_table, source_column, proposed_business_name, domain,
       ontology_concept_id, confidence_score, privacy_class,
       review_reason, recommended_reviewer_role, queue_status, run_id
FROM workspace.agentic_insurance_mvp.review_queue
ORDER BY recommended_reviewer_role, source_table, source_column;

-- Validation summary
SELECT
  COUNT(*) AS dictionary_rows,
  SUM(CASE WHEN confidence_score IS NULL THEN 1 ELSE 0 END) AS null_confidence_rows,
  SUM(CASE WHEN approval_state != 'PROPOSED' THEN 1 ELSE 0 END) AS auto_approved_rows,
  SUM(CASE WHEN confidence_score < 0.75 THEN 1 ELSE 0 END) AS low_confidence_rows,
  SUM(CASE WHEN privacy_class != 'INTERNAL' THEN 1 ELSE 0 END) AS personal_data_rows,
  SUM(CASE WHEN relationship_evidence IS NOT NULL THEN 1 ELSE 0 END) AS relationship_rows
FROM workspace.agentic_insurance_mvp.source_observation_dictionary;
```

## Machine-Readable Evidence

The full machine-readable evidence artifact is at `docs/evidence/mvp_run_evidence.json`.