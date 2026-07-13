---
name: build-governed-knowledge-foundation
description: Build and validate the governed insurance ontology and version-specific COTS knowledge for this Databricks recommendation solution. Use when normalizing ontology concepts and relationships, authoring or publishing knowledge packs, creating knowledge-table producers, recognizing COTS structures and extensions, assembling exact product/module/version context, or validating Governed Knowledge Foundation gates.
---

# Build Governed Knowledge Foundation

Build the Governed Knowledge Foundation as a contract-first, version-isolated
knowledge service. Keep all development outputs non-authoritative and
recommendation-only.

## Establish the active work package

1. Read `docs/planning/GOVERNED_KNOWLEDGE_FOUNDATION_WORK_PACKAGE.md`.
2. Verify `docs/evidence/source_intelligence_local_gate.json` records the Source
   Intelligence gate as `PASSED` and governed knowledge work as unlocked.
3. Read the seven governed knowledge contracts and
   `src/governed_knowledge_foundation/knowledge_contract_validation.py` before
   changing a producer or pack.
4. Read [knowledge_authoring_rules.md](references/knowledge_authoring_rules.md)
   for `ONTOLOGY-NORMALIZATION`, `PACK-AUTHORING`, `COTS-RECOGNITION`, or
   `CONTEXT-ASSEMBLY` work.
5. Select the earliest incomplete technical work package.
   `REVIEW-WORKFLOW-DESIGN` and `AUTHORITATIVE-GATE` stay
   deferred until the end-to-end technical solution is ready.

## Preserve the evidence boundary

- Use the development baseline named in
  `docs/governance/08_knowledge_baseline_evidence_authorization.json`.
- Permit repository-authored synthetic knowledge and explicitly authorized
  public material only. Never retain licensed COTS text in this repository.
- Require exact product, module, product version, pack ID, pack version,
  evidence references, and content fingerprints.
- Reject cross-version fallback, mixed baselines, raw document bodies,
  unapproved evidence, client data, PII, credentials, and connection strings.
- Keep source systems read-only. Never create source fixtures in the core job.
- Keep every generated mapping or match assessment `PROPOSED`; never promote it
  automatically or identify a real vendor without an exact active licensed
  pack.
- Do not add vector search, deployment DDL, ingestion, or target-model execution.

## Execute the technical sequence

1. Normalize the governed insurance ontology into contract-valid concept and relationship
   records without changing stable concept IDs.
2. Author one immutable COTS pack per governed product/module/version scope;
   each pack's patterns must resolve to the normalized ontology and its exact
   authorized evidence.
3. Add idempotent producers only for pre-provisioned solution-owned tables.
4. Implement transparent recognition outcomes: `MATCHED`,
   `LIKELY_CUSTOM_EXTENSION`, or `UNRESOLVED`.
5. Assemble minimized context by exact engagement, source, product, module,
   version, domain, LOB, effective date, approval state, and usage mode.
6. Integrate and validate locally before recording Databricks runtime evidence.

## Validate each package

- Validate records through `validate_knowledge_records` before persistence.
- Test unique IDs, relationship endpoints, lifecycle enums, evidence
  authorization, pack/version identity, cross-version rejection, effective
  dates, and repeat-run idempotency.
- Run focused tests first, then `python -m pytest -q`.
- Update the Governed Knowledge Foundation work package only after the package
  acceptance checks pass.
- Do not mark the knowledge foundation authoritative or complete from unit
  tests alone.
