# Evidence Classification Matrix

**Artifact:** `02_evidence_classification.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** Privacy Steward (placeholder - awaiting assignment)
**Reviewer:** Platform Owner (placeholder - awaiting assignment)
**Status:** PROPOSED

## Purpose

Defines which evidence classes may be observed, profiled, retained, indexed, or used as prompt context in the Free Edition pilot. Disallowed classes are rejected before profiling, indexing, retention, or prompt construction.

## Evidence classes

| Evidence class | Permitted operations | Retention | Prompt/retrieval eligible | Minimization rule | Reviewer | Prohibition rationale |
|---|---|---|---|---|---|---|
| **Physical metadata** (table name, column name, data type, nullable, ordinal position) | Observe, profile, retain, index | Full retention | Yes | None - non-sensitive | Domain Steward | N/A - permitted |
| **Key/relationship metadata** (primary key, foreign key, naming patterns) | Observe, infer, retain | Full retention | Yes | None - structural | Data Architect | N/A - permitted |
| **Aggregate profile** (null rate, distinct count, min/max, pattern summary) | Observe, profile, retain | Full retention | Yes | Aggregate only - no individual values | Domain Steward | N/A - permitted (synthetic data) |
| **Controlled value summary** (enum/domain values, frequency counts) | Observe, profile, retain | Full retention | Yes | Frequency counts only - no individual records | Domain Steward | N/A - permitted (synthetic data) |
| **Column name patterns** (naming conventions, semantic hints) | Observe, infer, retain | Full retention | Yes | None - non-sensitive | Domain Steward | N/A - permitted |
| **Personal data indicators** (column names suggesting PII: display_name, email, phone, address, birth, ssn) | Observe name only, classify, route to review | Name + classification retained | No - not eligible for prompt context | Column name only - never inspect values | Privacy Steward | Value-level inspection prohibited; only the column name is observed |
| **Claims narratives** (free-text loss descriptions) | Prohibited | Not retained | No | N/A | Privacy Steward | Prohibited in Free Edition; not present in synthetic MVP |
| **Client/production data** | Prohibited | Not retained | No | N/A | Privacy Steward | Prohibited - Free Edition uses synthetic data only |
| **PII values** (actual email addresses, phone numbers, SSNs, names) | Prohibited | Not retained | No | N/A | Privacy Steward | Prohibited - value-level inspection of PII is never permitted |
| **Credentials / connection strings** | Prohibited | Not retained | No | N/A | Platform Owner | Prohibited - no credentials in repo or Databricks workspace |
| **Proprietary COTS documentation** | Prohibited | Not retained | No | N/A | Domain Steward | Prohibited - no licensed material in Free Edition |

## Rules

1. **Observe before infer:** Physical metadata is observed; semantic meaning is inferred and labelled as such.
2. **No value-level inspection:** The system never reads individual data values for PII columns. Only column names and aggregate statistics are observed.
3. **Reject before profile:** If a column is classified as personal data, value-level profiling is rejected before it runs.
4. **Synthetic data only:** All evidence in the Free Edition pilot comes from synthetic Bronze tables. No client data is permitted.
5. **Retention scope:** Evidence is retained in Delta tables within `workspace.agentic_insurance_mvp` only. No external retention.

## Open questions

- [ ] Who is the named privacy steward? (placeholder until assigned)
- [ ] Should aggregate profiling be permitted for personal-data columns (e.g., null rate only)?
- [ ] Is there a data retention policy beyond the Free Edition pilot?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed evidence classification matrix | Agent (Cline) |
