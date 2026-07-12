# Agentic Solution Domain — Insurance

A governed, recommendation-only Source Intelligence and target-modelling solution for P&C insurance on Databricks.

## Solution boundary

The solution starts from existing source-aligned/Bronze tables provisioned by the client or platform data pipeline. It does not create, ingest, overwrite, or populate Bronze data.

The core workflow performs read-only source preflight and metadata analysis, then writes only solution-owned recommendation and review artifacts.

An optional synthetic demonstration harness lives in `examples/synthetic_bronze/`. It is a separate process and is never a dependency of the core Source Intelligence job.

## Layout

| Path | Contents |
|---|---|
| `src/databricks/` | Core read-only source analysis and recommendation notebooks |
| `src/source_intelligence/` | Testable deterministic Source Intelligence logic |
| `examples/synthetic_bronze/` | Optional isolated demo/test source setup |
| `contracts/` | Machine-readable output and governance contracts |
| `tests/` | Unit and validation tests |
| `evals/` | Labelled evaluation data and judges |
| `docs/` | Architecture, governance, planning, and evidence |
| `knowledge_packs/` | Authorized ontology, standards, rules, and COTS-like patterns |
| `prompts/` | Versioned agent prompts for later gated phases |
| `.agents/skills/` | Reusable project workflows |

## Core execution

Configure the existing source scope in `src/databricks/00_config.py`, then use `scripts/run_source_intelligence_job.json` or run the numbered notebooks in order. The first executable step validates that configured source tables exist; it never attempts to create them.

## Rules of the road

- Recommendation-only: no source deployment, ingestion, migration, or Bronze creation in the core solution.
- Source access is read/query/retrieval only.
- Observed facts remain separate from inferred meaning.
- Structured outputs validate against contracts before persistence.
- Confidence routes review but never grants approval.
- Free Edition development uses synthetic data only; organizational data requires approved governance and a controlled environment.
