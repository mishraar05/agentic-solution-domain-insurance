# Source Intelligence — Databricks workflow

The core workflow analyzes existing source-aligned/Bronze tables. Source creation, ingestion, and population are outside the solution boundary.

## Core run order

1. `00_config.py` — configure existing source scope and recommendation output.
2. `01_validate_source_scope.py` — verify configured inputs through read-only metadata access.
3. `02_build_source_dictionary.py` — produce proposed source observations and semantics.
4. `03_create_review_queue.py` — route uncertain and governed items.
5. `04_validate_mvp.py` — validate solution-owned recommendation outputs.

The production job is `scripts/run_source_intelligence_job.json`. It never creates or overwrites source tables.

## Configuration

Set `SOURCE_CATALOG`, `SOURCE_SCHEMA`, `SOURCE_TABLES`, `SOURCE_SYSTEM`, `OUTPUT_CATALOG`, and `OUTPUT_SCHEMA` in `00_config.py`.

Source tables are read-only prerequisites. The solution owns only its recommendation artifacts, including `source_observation_dictionary` and `review_queue`.

## Optional demo

`examples/synthetic_bronze/` contains a separate synthetic fixture workflow for demonstrations and integration tests. The core job never depends on it.

## Safety boundary

Do not use client data, real PII, claims narratives, proprietary COTS material, credentials, or production connection strings in the Free Edition learning environment. All recommendations remain `PROPOSED` until human review.
