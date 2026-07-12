# Agentic Solution Domain — Insurance

A governed, recommendation-only Source Intelligence and target-modelling pilot
for property and casualty insurance. The solution runs as plain Python-backed
Databricks notebooks and jobs, while keeping deterministic business logic
independent of the notebook runtime.

## What the project does

The Phase 2 Source Intelligence workflow examines configured, existing
source-aligned/Bronze tables and produces reviewable recommendations about:

- physical source objects and attributes;
- proposed business names, domains, and ontology concepts;
- privacy classifications;
- candidate keys and relationships;
- minimized aggregate profile evidence;
- transparent confidence components and evidence coverage;
- items that require a Data Architect, Domain Steward, or Privacy Steward.

The workflow does not deploy a Silver or Gold model. It produces governed data
records that humans may approve, modify, reject, or defer.

## Non-negotiable solution boundary

- Existing source/Bronze tables are external, read-only inputs.
- The core workflow never creates, ingests, overwrites, repairs, or populates
  source data.
- Recommendation records are validated against contracts before persistence.
- Observed facts and inferred meaning remain distinguishable.
- Confidence controls review routing only; it never grants approval.
- Every recommendation starts as `PROPOSED`.
- Client data, real PII, credentials, connection strings, claims narratives,
  and licensed proprietary documentation are prohibited from this repository.
- Synthetic source creation is isolated under `examples/synthetic_bronze/` and
  is never a dependency of the core workflow.

## Architecture

```text
Configured external source tables (read only)
                  |
                  v
src/workflows/source_intelligence/     numbered Databricks entry points
                  |
                  v
src/source_intelligence/               deterministic reusable Python logic
                  |
                  v
contracts/                             validation before persistence
                  |
                  v
Solution-owned PROPOSED observations, relationships, profiles, and review work
                  |
                  v
Human review decisions                no automatic authorization
```

The separation is deliberate:

- `src/workflows/source_intelligence/` contains runtime entry points and Spark
  orchestration.
- `src/source_intelligence/` contains reusable, testable rules and services.
- `resources/` describes how Databricks Asset Bundles sequence the entry points.
- `contracts/` defines the logical records that producers must validate.

## Repository layout

| Path | Responsibility |
|---|---|
| `src/workflows/source_intelligence/` | Numbered Databricks workflow entry points and their detailed workflow README |
| `src/source_intelligence/` | Deterministic, runtime-independent Source Intelligence modules |
| `resources/` | Databricks job resource definitions; currently one sequential Source Intelligence job |
| `databricks.yml` | Databricks Asset Bundle root configuration and single `DEV` target |
| `contracts/` | JSON contracts for observations, profiles, relationships, runs, review work, and policy violations |
| `tests/unit/` | Pure-Python contract, classification, routing, lifecycle, evaluation, and reporting tests |
| `tests/validation/` | Synthetic multi-record, retry, invalidation, and prohibited-evidence scenarios |
| `evals/labelled_set/` | Machine-readable labelled synthetic attributes; still requires independent human review |
| `docs/governance/` | Proposed scope, evidence policy, reviewer model, confidence policy, evaluation plan, and scorecard |
| `docs/planning/` | Implementation plan, execution plan, reviews, and work-plan sources |
| `docs/evidence/` | Human-readable and machine-readable run and gate evidence |
| `knowledge_packs/` | Versioned synthetic ontology and authorized structured reference material for gated later phases |
| `examples/synthetic_bronze/` | Optional isolated synthetic source harness for demonstrations and integration tests |
| `scripts/` | Human-operated helpers and legacy/manual job payloads; not imported by the core workflow |
| `.agents/skills/` | Reusable agent instructions for governed project work |

## Core workflow entry points

The Databricks job is intentionally sequential. Every task receives the same
`run_id`, and every later notebook imports `00_config.py` with `%run`.

| Order | File | Reads | Produces or verifies |
|---|---|---|---|
| 00 | `00_config.py` | Job widget and declared environment settings | Shared run context, thresholds, version constants, safe table-name helpers, and import path |
| 01 | `01_validate_source_scope.py` | Catalog metadata and configured source schemas | Read-only prerequisite validation; no persisted output |
| 02 | `02_build_source_dictionary.py` | Source schemas and permitted aggregate profiles | Attribute/object observations, profile evidence, relationship candidates, and the Phase 1-compatible dictionary |
| 03 | `03_create_review_queue.py` | Current run's proposed attribute observations | Contract-valid open review items with role, reason, trigger, and priority |
| 04 | `04_validate_phase2.py` | All current-run recommendation outputs | Runtime gate assertions and one idempotent `source_intelligence_run` record |
| 05 | `05_record_review_decision.py` | One open queue item plus explicit human widget input | Contract-valid, idempotent human decision event; not part of the automated core job |
| 06 | `06_publish_data_dictionary.py` | Governed dictionary records | Optional approved-only or visibly watermarked draft Excel workbook; not part of the core job |

Detailed entry-point behavior, failure modes, and execution guidance are in
[`src/workflows/source_intelligence/README.md`](src/workflows/source_intelligence/README.md).

## Reusable Source Intelligence modules

| Module | Responsibility |
|---|---|
| `confidence.py` | Computes reproducible weighted confidence, availability states, contradiction states, and evidence coverage |
| `contract_validation.py` | Loads contracts, resolves cross-file references, and validates logical records before writes |
| `cots_patterns.py` | Represents authorized deterministic COTS-pattern matching; unavailable evidence stays explicit |
| `dictionary_export.py` | Builds the governed Excel data-dictionary report consumed by the optional publication workflow |
| `evaluation.py` | Compares deterministic predictions and review routes with the labelled synthetic set |
| `naming.py` | Proposes business names, ontology concepts, and domains from transparent naming rules |
| `policy.py` | Rejects prohibited evidence before profiling and creates sanitized violation events |
| `persistence.py` | Validates safe column-order and type alignment for append-only compatibility writes without schema evolution |
| `privacy.py` | Classifies privacy from transparent column-name rules without exposing source values |
| `quality.py` | Supplies deterministic fixture-quality and idempotency helpers |
| `relationships.py` | Infers key roles and known candidate relationships from naming and compatibility evidence |
| `review_lifecycle.py` | Creates role-authorized human decisions and suppresses unchanged rejected recommendations |
| `routing.py` | Routes privacy, key, relationship, contradiction, unmapped, incomplete, and low-confidence items |
| `types.py` | Scores compatibility between physical types and proposed semantics |

Business rules belong in these modules. Workflow notebooks should contain only
Spark-facing extraction, serialization, sequencing, and runtime assertions.

## Contracts and solution-owned outputs

The core producer validates logical records before converting nested objects or
timestamps into physical Spark representations.

| Output | Contract | Purpose |
|---|---|---|
| `source_object_observation` | `source_object_observation.json` | Object-level physical facts and inferred domain/privacy summary |
| `source_attribute_observation` | `source_attribute_observation.json` | Attribute metadata, evidence, proposed semantics, confidence, privacy, and approval state |
| `profile_evidence` | `profile_evidence.json` | Minimized, governance-permitted aggregate profile results |
| `relationship_candidate` | `relationship_candidate.json` | Proposed relationships with naming/type evidence and confidence |
| `source_intelligence_run` | `source_intelligence_run.json` | Run scope, versions, status, idempotency key, timestamps, and metrics |
| `review_queue` | `review_queue_item.json` | Open human review work with a stable queue-item identifier |
| Review decisions | `review_decision.json` | Human decision, rationale, exact queue link, and invalidation impact |
| Policy violations | `policy_violation_event.json` | Sanitized record of prohibited evidence rejected before profiling |

`source_observation_dictionary` remains as a Phase 1 compatibility output. It
is not a deployment schema and is never automatically authoritative.

## Configuration

All environment-specific workflow settings are centralized in
`src/workflows/source_intelligence/00_config.py`:

- `SOURCE_CATALOG`, `SOURCE_SCHEMA`, and `SOURCE_TABLES` identify external,
  read-only inputs;
- `SOURCE_SYSTEM` identifies the configured source family;
- `OUTPUT_CATALOG` and `OUTPUT_SCHEMA` identify the solution-owned destination;
- `ARTIFACT_VERSION` and `SCHEMA_VERSION` provide traceability;
- `LOW_CONFIDENCE_THRESHOLD` and `EVIDENCE_COVERAGE_FLOOR` govern routing.

The output schema must already exist as a platform prerequisite. The core
workflow checks it but does not provision infrastructure.

The job supplies `run_id: si_job_{{job.run_id}}` to every core task. Interactive
runs without a widget use a UTC timestamp identifier. The run-ID pattern is
validated before processing begins.

## Databricks Asset Bundle execution

The bundle root is `databricks.yml`; the job definition is
`resources/source_intelligence_pipeline.yml`. Notebook paths are relative to
the resource file and point into `src/workflows/source_intelligence/`.

A human operator with an approved Databricks CLI v2 profile performs bundle
validation, deployment, and job execution. The agent implementation surface
does not hold deploy, execute, credential, ingestion, or source-write tools.

Before a run:

1. Confirm the configured external source tables exist.
2. Confirm the solution-owned output schema exists.
3. Confirm governance permits the intended metadata and aggregate evidence.
4. Validate the bundle and inspect the resolved five-task sequence.
5. Run the job and capture its run URL and output evidence under `docs/evidence/`.

The optional publication notebook is deliberately excluded from the core job.

## Local verification

Pure-Python checks require no Databricks connection:

```powershell
python -m compileall -q src tests
python -m pytest -q
```

CI runs the same local-safe test suite, parses every JSON contract, and requires
no Databricks credentials. Spark producer validation remains a manual
in-workspace gate and must be captured as evidence.

## Governance and review

Governance artifacts are currently `PROPOSED`. They define the intended Policy
pilot, permitted evidence, reviewer decision rights, confidence policy,
evaluation metrics, and go/no-go scorecard. Named humans must approve or modify
them before any recommendation becomes authoritative.

Mandatory review includes privacy-relevant attributes, keys, relationships,
contradictions, unmapped concepts, inadequate evidence coverage, and low
confidence. Rejections retain a fingerprint so the same recommendation cannot
silently reappear unchanged.

## Current Phase 2 status

Local implementation evidence is recorded in:

- `docs/evidence/PHASE2_COMPLETION_STATUS.md`;
- `docs/evidence/phase2_local_gate.json`;
- `docs/evidence/PHASE2_FOUNDATION_READINESS.md`.

The overall Phase 2 gate remains incomplete until fresh Databricks runtime
evidence, independent human relabelling and confidence calibration, and named
governance approvals exist. Phase 3 agentic, retrieval, and knowledge-driven
capabilities remain ineligible until that gate is evidenced.

## Newcomer starting path

1. Read this README and `AGENTS.md` for boundaries and conventions.
2. Read `src/workflows/source_intelligence/README.md` for execution behavior.
3. Read the relevant contract before changing a producer.
4. Put deterministic rules in `src/source_intelligence/`, not in notebooks.
5. Add synthetic tests for every rule or routing change.
6. Run the local verification commands.
7. Update evidence honestly; unresolved human or runtime decisions stay open.
