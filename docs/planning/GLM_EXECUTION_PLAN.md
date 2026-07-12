# GLM 5.2 Execution Plan

**Status:** READY FOR EXECUTION  
**Repository:** discover from the current Git working tree; never hardcode a machine path  
**Controlling input:** `docs/planning/CONSOLIDATED_RECOMMENDATIONS.md`  
**Objective:** close the gap between the approved architecture and the executable deterministic foundation before Phase 3 agentic work begins.

## 1. Operating rules

1. Read `AGENTS.md`, this plan, `CONSOLIDATED_RECOMMENDATIONS.md`, the governance Markdown, and relevant source files before editing.
2. Use synthetic data only. Never add client data, real PII, licensed COTS material, credentials, or production connection strings.
3. Keep outputs recommendation-only. Do not create deployment DDL, ingestion, migration, or operational transformation code.
4. Keep observed facts, inferred meaning, evidence, confidence, assumptions, contradictions, and approvals separate.
5. Never mark a governance artifact or recommendation `APPROVED`; only named humans may approve.
6. Preserve unrelated work. Inspect the working tree before each work package.
7. Implement one work package at a time. Run its acceptance checks before starting the next package.
8. Keep shared configuration in `src/workflows/source_intelligence/00_config.py`. Remove business-logic coupling between notebooks, not the shared configuration entry point.
9. LLMs, prompts, vector search, and semantic retrieval are eligible only in Phase 3+ after the deterministic Phase 2 gate passes.
10. Use semantic versioning for schemas: patch for clarification, minor for backward-compatible additions, major for breaking changes. Add compatibility tests.
11. Treat existing source/Bronze tables as external read-only inputs. Bronze creation, ingestion, and population are outside the solution and must remain in a separate optional demo/test harness.

## 2. Execution order

```text
Baseline and safety audit
  -> Governance rule and plan mapping
  -> Skill corrections
  -> Contract foundation
  -> Machine-readable labelled set
  -> Testable deterministic core
  -> Governed confidence calculation
  -> Expanded synthetic fixtures
  -> Unit and validation tests
  -> Pure-Python CI
  -> Documentation and Phase 2 readiness report
```

Contracts, synthetic fixtures, and tests may proceed while governance is `PROPOSED`. Synthetic profiling and non-authoritative development artifacts may also proceed. Organizational data, authoritative publication, production promotion, and human approval are prohibited until the applicable governance artifacts are approved.

## 3. Work packages

### WP-A — Baseline and repository safety

**Actions**

- Record current branch, remote tracking state, recent commits, and working-tree status.
- Inspect the untracked root item named `d`. Report its type, size, and content. Remove it only when it is demonstrably an accidental empty artifact and the user authorizes deletion.
- Validate that Phase 1 evidence remains present and unchanged.
- Confirm all existing skills pass the skill validator before editing.

**Acceptance**

- Baseline is recorded in the execution report.
- No unrelated or user-owned file is changed.
- The unexplained `d` item has a documented disposition.

### WP-B — Governance and planning consistency

**Files**

- `docs/governance/00_phase0_gate_validation.md`
- `docs/governance/06_go_no_go_scorecard.md`
- `docs/governance/04_confidence_policy.md`
- `docs/planning/IMPLEMENTATION_PLAN.md`
- `docs/planning/CONSOLIDATED_RECOMMENDATIONS.md`

**Actions**

1. Replace contradictory Phase 2 permission language with one rule:
   - synthetic development, profiling, fixtures, contracts, and tests may proceed under `PROPOSED` governance;
   - outputs remain non-authoritative;
   - organizational data, publication, promotion, and approval require approved governance.
2. Add a Phase 0–6 to WP1–5 crosswalk to `IMPLEMENTATION_PLAN.md`. If a phase spans multiple work packages, state that explicitly.
3. Clarify confidence handling for unavailable components:
   - store component state as `AVAILABLE`, `NOT_AVAILABLE`, or `CONTRADICTED`;
   - renormalize over available weights;
   - calculate evidence coverage as available weight divided by total weight;
   - force review when evidence coverage is below `0.60`;
   - keep weights and the coverage floor `PROPOSED` until calibrated.
4. Clarify COTS sequencing:
   - Phase 2 permits deterministic matching against small authorized structured patterns;
   - Phase 3 introduces governed retrieval and semantic search.
5. Replace the arbitrary “100+” labelled-set rule with stratified coverage criteria. Retain 100+ only as a planning target, not a statistical guarantee.

**Acceptance**

- Governance documents no longer disagree about permitted work.
- Phase and work-package references are navigable and unambiguous.
- Confidence missing-evidence behavior is explicit and testable.
- COTS recognition and retrieval are clearly separated.

### WP-C — Correct and simplify the skill layer

**Actions**

1. Rename `.agents/skills/insurance-lake-next-steps/` to `.agents/skills/advance-next-step/`.
2. Update its frontmatter, heading, and `agents/openai.yaml`.
3. Make `advance-next-step` a short router:
   - inspect repository evidence and determine the earliest incomplete gate;
   - invoke `$define-insurance-pilot-governance` for unresolved governance;
   - invoke `$build-source-intelligence-v1` for deterministic Phase 2 work;
   - stop before Phase 3 unless the Phase 2 gate has evidence.
4. Remove duplicated specialist instructions from the router.
5. Replace hardcoded paths and tool-specific wording in all skills with repository-root discovery and agent-neutral wording.
6. Add the Phase 3+ expiry condition for the LLM/vector-search restriction.
7. Add deterministic, authorized COTS-pattern matching to the Source Intelligence skill or explicitly cite its Phase 2 deferral decision.
8. Ensure the Source Intelligence skill distinguishes prohibited-content rejection from routing a sanitized exception decision.
9. Validate every skill using the standard skill validator.

**Acceptance**

- Exactly three non-overlapping skills exist.
- Router delegates rather than restating specialist logic.
- No skill contains a hardcoded local path or tool-specific trigger description.
- All skills validate successfully.

### WP-D — Contract foundation

**Target files**

```text
contracts/common.json
contracts/source_intelligence_run.json
contracts/source_object_observation.json
contracts/source_attribute_observation.json
contracts/profile_evidence.json
contracts/relationship_candidate.json
contracts/review_decision.json
contracts/policy_violation_event.json
contracts/labelled_set.schema.json
```

**Actions**

1. Use JSON Schema Draft 2020-12 and stable `$id` values.
2. Put reusable definitions in `common.json` and reference them with `$ref`.
3. Require `schema_version` in every root artifact.
4. Model identifiers, source scope, run context, artifact version, evidence references, observation/inference state, confidence components, assumptions, contradictions, privacy, lifecycle, approval, reviewer decisions, and timestamps.
5. Define the run idempotency key from normalized scope, evidence snapshot, knowledge versions, and task-contract version.
6. Make `review_decision` preserve decision, reviewer role, rationale, timestamps, prior recommendation version, and invalidation impact.
7. Ensure `policy_violation_event` contains sanitized metadata only and cannot contain prohibited values.
8. Add a lightweight validation utility using an already available dependency. If none is available, document the required validator rather than silently adding an unapproved dependency.
9. Add positive, negative, and compatibility fixtures for each schema.

**Acceptance**

- All schemas parse and resolve `$ref` successfully.
- Valid fixtures pass; invalid fixtures fail for the intended reason.
- Review and violation records cannot omit governance-critical fields.
- Breaking compatibility is detectable.

### WP-E — Machine-readable labelled set

**Target files**

```text
evals/labelled_set/source_attributes_v1.json
evals/labelled_set/README.md or concise Markdown summary
```

Do not create a README merely to describe a skill; this is a project evaluation dataset, so a short dataset description is appropriate.

**Actions**

1. Convert the existing 19 Markdown rows into JSON validated by `labelled_set.schema.json`.
2. Assign stable record IDs.
3. Include expected domain, business name, ontology concept, privacy class, key role, relationship target, and review routing.
4. Mark unresolved expected values explicitly; do not convert them to null without a lifecycle state.
5. Define stratification dimensions: domain, privacy, ambiguity, key role, relationship, known/unknown pattern, and expected review route.
6. Add an expansion manifest describing missing strata and planned synthetic cases.
7. Implement deterministic coverage, precision, recall, and routing calculations. Label results from the initial 19-record census as fixture acceptance, not generalization evidence.

**Acceptance**

- The labelled set validates against its schema.
- Metrics run deterministically.
- Reports clearly separate fixture correctness from broader calibration claims.

### WP-F — Extract the deterministic Source Intelligence core

**Suggested structure**

```text
src/source_intelligence/
  __init__.py
  models.py
  naming.py
  types.py
  privacy.py
  relationships.py
  cots_patterns.py
  confidence.py
  routing.py
  validation.py
```

Adapt names to existing repository conventions if an equivalent structure already exists.

**Actions**

1. Extract logic from `02_build_source_dictionary.py` and `03_create_review_queue.py` into deterministic functions with explicit inputs and outputs.
2. Keep notebooks as orchestration entry points.
3. Replace exact-name-only behavior with transparent rules while retaining approved exact patterns as one evidence source.
4. Separate physical metadata extraction, minimized profile evidence, semantic classification, relationship inference, privacy classification, authorized structured COTS matching, confidence, and review routing.
5. Validate structured outputs against contracts before persistence.
6. Reject prohibited evidence before profiling or retention. Persist only a sanitized violation event and route only the exception decision.
7. Preserve run ID, artifact version, evidence references, assumptions, contradictions, and approval state.

**Acceptance**

- Core rules are importable and testable without executing a Databricks notebook.
- Notebooks contain orchestration rather than embedded rule tables.
- Existing Phase 1 outputs remain reproducible or documented migrations explain changes.

### WP-G — Governed confidence implementation

**Actions**

1. Calculate confidence from versioned components:

```text
0.35 * naming_strength
+ 0.20 * type_strength
+ 0.25 * relationship_strength
+ 0.10 * cots_match_strength
+ 0.10 * standard_consistency
```

2. Record component value, availability state, evidence reference, weight, formula version, evidence coverage, raw weighted sum, normalized score, and routing reason.
3. Renormalize only over available components.
4. Force human review below the evidence-coverage floor or when any mandatory trigger applies.
5. Distinguish absent evidence from contradictory evidence.
6. Never use confidence to approve a recommendation.
7. Add a v1-to-Phase-3 component mapping for retrieval fitness, governed rules, contradiction checks, and reviewer-history calibration.

**Acceptance**

- No final confidence score is hardcoded in a lookup table.
- Recomputing from persisted components reproduces the score.
- Missing and contradictory evidence produce different outcomes.
- Coverage-floor and mandatory-review tests pass.

### WP-H — Expand synthetic fixtures

**Actions**

Synthetic fixture generation belongs under `examples/` or `tests/fixtures/` and must run as a separate process. It must never become a dependency of the core Source Intelligence job.

Add synthetic cases for:

- null and empty values;
- duplicate and missing identifiers;
- orphan foreign keys;
- incompatible relationship types;
- conflicting naming and type signals;
- unknown and ambiguous attributes;
- personal-data naming patterns;
- prohibited-evidence rejection fixtures containing unmistakably fake sentinel strings;
- date and amount boundaries;
- changed-input versioning;
- repeat-run idempotency;
- controlled failure and retry.

Never use realistic credentials or real personal information. Use obvious sentinels such as `FORBIDDEN_TEST_SENTINEL`.

**Acceptance**

- Every required stratum has at least one fixture.
- Fixtures remain synthetic and safe to commit.
- The expansion manifest shows no unaddressed P0 strata.

### WP-I — Unit and validation tests

**Unit tests**

- Schema parsing, `$ref`, positive/negative fixtures, and compatibility.
- Domain and privacy classification.
- Type compatibility and relationship inference.
- Authorized structured COTS-pattern matching.
- Confidence calculation, availability, contradiction, coverage floor, and weighting.
- Review routing and no auto-approval.
- Prohibited-evidence rejection and sanitized violation events.

**Validation tests**

- Repeat-run idempotency.
- Artifact and schema versioning.
- Missing metadata and incomplete profiles.
- Conflicting keys and relationships.
- Evidence completeness.
- Targeted invalidation.
- Labelled-set metrics.
- Leakage scan across generated artifacts and captured logs for `FORBIDDEN_TEST_SENTINEL`.

**Acceptance**

- All local pure-Python tests pass.
- Databricks-dependent checks have a documented manual command or job and captured evidence.
- A deliberate prohibited sentinel never appears in persisted output or logs.

### WP-J — CI and quality gates

**Actions**

1. Add GitHub Actions for pure-Python tests, schema validation, labelled-set validation, and leakage scanning.
2. Do not connect CI to Databricks Free Edition or store Databricks credentials in GitHub.
3. Keep Databricks validation manual and capture evidence under `docs/evidence/`.
4. Fail CI on contract errors, unit-test failures, invalid labelled data, or prohibited sentinel leakage.

**Acceptance**

- Pull requests and pushes run the local-safe checks.
- The workflow requires no external secrets.
- CI failure messages identify the violated contract or invariant.

### WP-K — Documentation and readiness report

**Actions**

1. Add Markdown extracts for implementation-critical architecture information currently available only in Office files.
2. State that agents should not need Office parsing for routine implementation; contracts and Markdown extracts are authoritative implementation interfaces.
3. Update `README.md`, `AGENTS.md`, and the implementation plan only where behavior or navigation changed.
4. Produce `docs/evidence/PHASE2_FOUNDATION_READINESS.md` with:
   - work packages completed;
   - schemas and versions;
   - test and CI results;
   - labelled-set coverage;
   - remaining human approvals;
   - explicit decision on whether Phase 2 producers may proceed.
5. Do not declare the Phase 2 acceptance gate passed until deterministic producers run and all gate evidence exists.

**Acceptance**

- An agent can implement routine work without parsing binary Office files.
- Readiness claims link to machine-readable evidence.
- Remaining human decisions are explicit and owned.

## 4. Commit checkpoints

Use focused commits after each accepted checkpoint:

1. `Align governance, plans, and skills`
2. `Add source intelligence contracts and fixtures`
3. `Add machine-readable labelled evaluation set`
4. `Extract deterministic source intelligence core`
5. `Implement governed confidence and routing`
6. `Expand synthetic fixtures and tests`
7. `Add local-safe CI and readiness evidence`

Do not combine unrelated work. Do not push a checkpoint with failing checks. Do not rewrite published history.

## 5. Human decision points

Stop and request human direction when:

- deleting or replacing an unexplained user file;
- assigning named reviewers or changing an artifact to `APPROVED`;
- choosing a dependency not already permitted by `AGENTS.md`;
- changing confidence weights or the evidence-coverage floor from their proposed values;
- using any non-synthetic or externally sourced data;
- introducing LLMs, vector search, prompts, or semantic retrieval;
- changing the recommendation-only boundary.

## 6. Final completion criteria

This execution plan is complete when:

- governance and planning language is consistent;
- the three skills are portable, non-duplicative, and valid;
- all nine contract/schema artifacts exist and validate;
- the labelled set is machine-readable and measurable;
- deterministic logic is importable and contract-validated;
- confidence is reproducible from governed components;
- synthetic edge cases and prohibited-evidence tests exist;
- unit, validation, and local-safe CI checks pass;
- implementation-critical documentation is agent-readable;
- a readiness report identifies remaining human approvals and the next permitted phase.
