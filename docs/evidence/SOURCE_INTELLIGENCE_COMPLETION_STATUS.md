# Source Intelligence Completion Status

**Date:** 2026-07-13
**Status:** BLOCKED_EXTERNAL — local implementation complete; release gate not passed

## Completed locally

- 154 pure-Python unit and validation tests pass.
- Source Documentation Agent tests verify prompt allow-listing, privacy blocking,
  strict structured output, stable provenance, and no auto-approval.
- The 26-record synthetic evaluation set spans snake_case, camelCase, vendor abbreviations, ambiguous tokens, and opaque names; it reaches 100% proposed-classification coverage.
- Expected semantics, privacy, keys, known relationships, contradiction routing, and review routes match 26/26 labels; ontology resolution is 84.62% because four governed cases intentionally remain unresolved.
- Naming, privacy, and type inference uses versioned packs with stable per-rule evidence provenance; the run record captures active pack versions.
- Pack selection is reproducible by source system, naming convention, priority, and effective date; ambiguous selection and token expansions fail closed.
- Contradicted confidence components remain explicit and excluded from scoring.
- Review decisions link to one queue item, require the routed reviewer role and rationale, and suppress unchanged rejected recommendations.
- A human-operated review workbench records contract-valid, idempotent decisions without selecting or approving decisions automatically.
- The Databricks bundle job uses bundle-relative notebook paths and one shared `si_job_{{job.run_id}}` context.
- Local Databricks state is excluded while `databricks.yml` remains version-controlled.

Machine-readable results: `docs/evidence/source_intelligence_local_gate.json`.

## Required external completion

Completed external checks: Databricks CLI `1.7.0`, DEV bundle validation, and
read-only discovery of READY, batch-supported endpoint
`databricks-gpt-oss-20b`. Real-time-only endpoint
`databricks-gpt-5-6-luna` was rejected after `ai_query` reported it does not
support batch inference.

Still required:

1. Execute the Source Intelligence job and Spark producer validation; capture run evidence.
2. Confirm an actual serverless `ai_query` invocation against the configured endpoint.
3. Have a Domain Steward independently assess generated documentation.
4. Have a human independently review the labelled set and complete `evals/labelled_set/INDEPENDENT_REVIEW.md`.
5. Approve or modify the 0.75 confidence threshold and component weights using independently reviewed labels.
6. Assign named Data Architect, Domain Steward, Privacy Steward, Evaluation Owner, and Sponsor roles; only humans may approve governance artifacts.

Knowledge-driven and target-modelling work remains ineligible until these external gates are evidenced.
