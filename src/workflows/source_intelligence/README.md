# Source Intelligence Workflow Entry Points

This directory contains the Databricks-executable entry points for the governed
Source Intelligence workflow. The files are numbered because execution order is
part of the contract: configuration and preflight must succeed before producers,
LLM-assisted documentation, review routing, and final validation run.

These notebooks are orchestration adapters, not the primary home of business
logic. Reusable classification, confidence, privacy, relationship, policy,
routing, lifecycle, and evaluation logic belongs in `src/source_intelligence/`
and must remain independently testable.

## Core execution sequence

| Order | Entry point | Detailed responsibility | Persisted output |
|---|---|---|---|
| 00 | `00_config.py` | Declares the single environment, validates or creates the shared run identifier, locates the reusable Python package, provides quoted table-name helpers, and verifies that the output schema already exists | None |
| 01 | `01_validate_source_scope.py` | Lists configured source tables through read-only catalog access and verifies that every table exists with a non-empty schema | None |
| 02 | `02_build_source_dictionary.py` | Reads schemas, executes deterministic semantics/privacy/confidence rules, collects permitted aggregate profiles, validates logical records, and appends idempotent recommendation outputs | Dictionary, object and attribute observations, profile evidence, relationship candidates |
| 03 | `03_generate_source_documentation.py` | Sends only governance-eligible structural context and minimized aggregates to the configured Databricks model using strict structured output; prohibited context becomes unresolved without a model call | `source_documentation_recommendation` |
| 04 | `04_create_review_queue.py` | Applies mandatory-review and confidence routing to current-run attributes and routes every documentation recommendation to a Domain Steward | Canonical `source_intelligence_review_queue` plus aligned consumer-facing `review_queue` projection |
| 05 | `05_validate_source_intelligence.py` | Checks run consistency, completeness, evidence, documentation coverage, relationships, review routing, idempotency, and no auto-approval; then validates and appends the run record | `source_intelligence_run` |

The Databricks Asset Bundle job ends after step 05. Steps 06 and 07 are
human-operated and optional.

## Human-operated entry points

`06_record_review_decision.py` accepts an explicit human reviewer decision for
one open queue item. It verifies the routed role, requires rationale, validates
the decision contract, and appends an idempotent event. It never selects or
approves a recommendation on the reviewer's behalf.

`07_publish_data_dictionary.py` renders an Excel workbook for human use. Its
default mode includes only records already marked `APPROVED` by a human. Draft
mode is explicit and visibly watermarked. Publication never changes source or
recommendation tables and is not part of the core job.

## Shared run context

Every core job task receives the same `run_id` job parameter. Each downstream
notebook imports `00_config.py` with `%run`, so it resolves the same source
scope, output location, versions, and routing thresholds. If tasks use different
run identifiers, downstream validation intentionally fails rather than joining
artifacts from unrelated executions.

Supported identifiers are:

- `si_job_<Databricks numeric run id>` for job execution;
- `si_<YYYYMMDDTHHMMSSZ>` for interactive execution without a widget.

## Read and write boundary

The workflow may read:

- configured catalog and schema metadata;
- configured external source schemas;
- governance-permitted aggregate profiles for non-personal columns;
- solution-owned recommendation outputs from earlier tasks in the same run.

The Source Documentation Agent may send only allow-listed structural metadata,
deterministic inferences, and minimized aggregate profiles for `INTERNAL`
columns to the configured model endpoint. It never sends source row values,
personal/sensitive columns, claims narratives, credentials, or proprietary
documentation.

The workflow may write only contract-validated, solution-owned recommendation,
review, run, and reporting artifacts. It must never create, ingest, overwrite,
or populate source/Bronze inputs. Personal-data columns are detected from names
and skipped before value-level profiling.

## Failure behavior

- Missing source tables stop step 01.
- Invalid contracts stop producers before persistence.
- The consumer-facing dictionary projection aligns to the existing table's
  column order without schema evolution; missing or incompatible types stop
  before the append.
- Missing or inconsistent run-scoped outputs stop step 05.
- Model invocation errors stop step 03 before any partial documentation write.
- Every model-generated description and glossary proposal routes to a Domain
  Steward; no model output can approve itself.
- Duplicate records for the same run violate idempotency assertions.
- Any non-`PROPOSED` recommendation created by the workflow fails validation.
- Missing mandatory key routing fails validation.
- A failed run must not be represented by a fabricated `SUCCEEDED` record.

## Idempotency and history

Outputs are append-only and scoped by `run_id`. Before appending, each producer
checks whether that output already contains records for the run. A retry skips
an existing run rather than duplicating or overwriting history.

## Configuration checklist

Supply environment values through DAB variables or equivalent notebook job
parameters; do not edit the engine to introduce a source inventory:

1. Confirm `source_catalog`, `source_schema`, and `source_tables` identify
   existing read-only inputs.
2. Set a meaningful `source_system` identifier.
3. Confirm `output_catalog` and `output_schema` identify the solution-owned
   recommendation destination.
4. Change versions in `00_config.py` only when artifact or contract meaning changes.
5. Do not tune confidence weights or thresholds without governed labelled
   reviewer evidence and an explicit human decision.

## Databricks Asset Bundle mapping

`resources/source_intelligence_pipeline.yml` maps six sequential tasks to
files 00 through 05 in this directory. Paths are source-relative so the bundle
can deploy under different workspace roots without hardcoded notebook paths.
`databricks.yml` provides the bundle name, included resources, and environment
target.

## Development guidance

- Add business rules to `src/source_intelligence/` and cover them with unit
  tests.
- Keep notebook code focused on Spark extraction, contract-shaped assembly,
  physical serialization, persistence, and runtime assertions.
- Update contracts before changing producer record shape.
- Use only synthetic fixtures in local and CI tests.
- Preserve observed facts separately from inferred semantics.
- Record fresh in-workspace evidence after any producer or job-definition change.
