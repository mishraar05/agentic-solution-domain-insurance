# Source Intelligence Completion Status

**Date:** 2026-07-13
**Status:** BLOCKED_EXTERNAL — local implementation complete; release gate not passed

## Completed locally

- 129 pure-Python unit and validation tests pass.
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

1. Install/use Databricks CLI v2; the installed legacy CLI has no `bundle` command.
2. Confirm serverless `ai_query` access to the configured Databricks-hosted model endpoint.
3. Run `databricks bundle validate -t DEV`, deploy, and execute the Source Intelligence job.
4. Execute the Spark producer validation in workspace and capture the run ID, output counts, contract results, documentation generation/routing, key/privacy routing, idempotent retry, and job URL under `docs/evidence/`.
5. Have a Domain Steward independently assess the generated descriptions and glossary proposals; unresolved and incorrect output must remain review work.
6. Have a human independently review the labelled set and complete `evals/labelled_set/INDEPENDENT_REVIEW.md`.
7. Approve or modify the 0.75 confidence threshold and component weights using independently reviewed labels.
8. Assign named Data Architect, Domain Steward, Privacy Steward, Evaluation Owner, and Sponsor roles in `docs/governance/07_source_intelligence_approval_record.md`; only humans may approve governance artifacts.

Knowledge-driven and target-modelling work remains ineligible until these external gates are evidenced.
