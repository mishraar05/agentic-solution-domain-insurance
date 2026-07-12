# Source Intelligence Workflow Entry Points

This directory contains the Databricks-executable entry points for the governed
Source Intelligence workflow. The files are numbered because execution order is
part of the contract: configuration and preflight must succeed before producers,
review routing, and final validation run.

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
| 03 | `03_create_review_queue.py` | Applies mandatory-review and confidence routing to current-run attributes, validates queue items, and appends them once | `review_queue` |
| 04 | `04_validate_phase2.py` | Checks run consistency, completeness, evidence, relationships, review routing, idempotency, and no auto-approval; then validates and appends the run record | `source_intelligence_run` |

The Databricks Asset Bundle job ends after step 04. Steps 05 and 06 are
human-operated and optional.

## Human-operated entry points

`05_record_review_decision.py` accepts an explicit human reviewer decision for
one open queue item. It verifies the routed role, requires rationale, validates
the decision contract, and appends an idempotent event. It never selects or
approves a recommendation on the reviewer's behalf.

`06_publish_data_dictionary.py` renders an Excel workbook for human use. Its
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

The workflow may write only contract-validated, solution-owned recommendation,
review, run, and reporting artifacts. It must never create, ingest, overwrite,
or populate source/Bronze inputs. Personal-data columns are detected from names
and skipped before value-level profiling.

## Failure behavior

- Missing source tables stop step 01.
- Invalid contracts stop producers before persistence.
- The Phase 1 dictionary compatibility write aligns to the existing table's
  column order without schema evolution; missing or incompatible types stop
  before the append.
- Missing or inconsistent run-scoped outputs stop step 04.
- Duplicate records for the same run violate idempotency assertions.
- Any non-`PROPOSED` recommendation created by the workflow fails validation.
- Missing mandatory key routing fails validation.
- A failed run must not be represented by a fabricated `SUCCEEDED` record.

## Idempotency and history

Outputs are append-only and scoped by `run_id`. Before appending, each producer
checks whether that output already contains records for the run. A retry skips
an existing run rather than duplicating or overwriting history.

## Configuration checklist

Edit only `00_config.py` for environment values:

1. Confirm `SOURCE_CATALOG`, `SOURCE_SCHEMA`, and `SOURCE_TABLES` identify
   existing read-only inputs.
2. Set a meaningful `SOURCE_SYSTEM` identifier.
3. Confirm `OUTPUT_CATALOG` and `OUTPUT_SCHEMA` identify the solution-owned
   recommendation destination.
4. Change versions only when the artifact or contract meaning changes.
5. Do not tune confidence weights or thresholds without governed labelled
   reviewer evidence and an explicit human decision.

## Databricks Asset Bundle mapping

`resources/source_intelligence_pipeline.yml` maps five sequential tasks to
files 00 through 04 in this directory. Paths are source-relative so the bundle
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
