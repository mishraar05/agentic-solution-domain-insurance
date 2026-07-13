---
name: build-source-intelligence-v1
description: Implement and validate governed Source Intelligence for the agentic insurance Databricks project. Use when consuming configured existing source tables through read-only access, creating output contracts, extracting approved metadata and minimized profiles, inferring relationships, classifying domains and privacy, generating LLM-assisted source documentation from permitted context, tracking runs, routing recommendations to review, adding isolated synthetic test fixtures, or evaluating the Source Intelligence release gate.
---

# Build Source Intelligence v1

Build a reusable source-analysis service with deterministic observation and
routing logic plus a separately governed Source Documentation Agent. LLM calls
may generate column descriptions and business-glossary proposals only from
prompt-eligible context; do not add vector search.

## Confirm prerequisites

 1. Discover and work from the repository root.
2. Read the Source Intelligence section of `docs/planning/IMPLEMENTATION_PLAN.md`, existing notebooks, contracts, tests, and governance decisions.
3. Require a defined evidence policy before profiling or retaining evidence. Stop and report missing governance rather than inventing permission.
4. Preserve existing consumer projections and evidence while adding a minimal viable product that includes all necessary features for functionality.
5. Treat source/Bronze tables as external read-only inputs. Never create, ingest, overwrite, or populate them. Keep synthetic setup in the isolated `examples/synthetic_bronze/` harness.

## Define contracts before producers

Create machine-validatable contracts for:

- `source_intelligence_run`;
- `source_object_observation`;
- `source_attribute_observation`;
- `profile_evidence`;
- `relationship_candidate`.

Require run ID, artifact version, source scope, observed facts, inferred values, evidence references, confidence components, assumptions, contradictions, privacy class, approval state, and timestamps where applicable. Keep observed and inferred fields separate.

## Implement deterministic capabilities

Build pure or narrowly scoped functions for:

1. read-only metadata extraction from approved catalog metadata;
2. minimized profiling: null rate, distinct count, patterns, min/max, and controlled summaries only when permitted;
3. relationship inference from key naming, compatible types, overlap evidence, and documented constraints;
4. Policy, Claims, Billing, Party, Product, Coverage, and Reference Data classification;
5. privacy classification from transparent rules without exposing values;
6. run creation, idempotent persistence, metrics, failure state, and reproducible version context.

## Generate source documentation with an LLM

Use a separate, versioned prompt and output contract. Send only allow-listed
physical metadata, deterministic inferences, and permitted minimized aggregate
profiles. Reject personal/sensitive columns before prompt construction. Require
strict structured output containing a column description and business-glossary
proposal, retain prompt/model provenance and the context fingerprint, assign no
LLM-derived confidence, keep every result `PROPOSED` or `UNRESOLVED`, and route
every result to a Domain Steward.

Place reusable code under `src/`, contracts under `contracts/`, synthetic fixtures under `data/synthetic/`, and tests under `tests/`. Validate every output against its contract before persistence.

## Route review explicitly

Route low-confidence, privacy-relevant, relationship, conflicting, incomplete, and disallowed-evidence cases to the appropriate human role. Do not auto-approve any recommendation. Preserve reviewer rationale and prevent rejected outputs from silently reappearing unchanged.

## Test the service

Add tests for:

- known synthetic domain and privacy classifications;
- expected primary/foreign-key candidates;
- missing metadata and incomplete profiles;
- conflicting identifiers and incompatible types;
- rejection of disallowed evidence before profiling;
- repeat-run idempotency;
- contract failures at write boundaries;
- low-confidence and privacy routing.

Use synthetic data only. Keep tests independent of production connections and secrets.

## Evaluate the Source Intelligence gate

Pass only when:

- at least 90% of synthetic fields receive a proposed semantic classification;
- 100% retain physical metadata and evidence references;
- known primary/foreign-key relationships have expected evidence;
- low-confidence and privacy-relevant entries reach review;
- repeat runs produce controlled, idempotent results;
- tests and contract validation succeed.

Capture machine-readable results plus a concise evidence summary under `docs/evidence/`. Report files changed, commands or jobs run, acceptance evidence, unresolved governance decisions, and the next eligible workstream.
