---
name: build-source-intelligence-v1
description: Implement and validate deterministic Source Intelligence Agent v1 for the agentic insurance Databricks project. Use when creating output contracts and Delta schemas, extracting approved metadata and minimized profiles, inferring relationships, classifying insurance domains and privacy, tracking source-intelligence runs, routing recommendations to review, adding synthetic fixtures and unit/validation tests, or evaluating the Phase 2 acceptance gate.
---

# Build Source Intelligence v1

Replace MVP static rules with a reusable, transparent, deterministic source-analysis service. Do not add an LLM or vector search.

## Confirm prerequisites

1. Work from `D:\agentic-solution-domain-insurance` when available.
2. Read the Phase 2 section of `docs/planning/IMPLEMENTATION_PLAN.md`, existing notebooks, contracts, tests, and governance decisions.
3. Require a defined evidence policy before profiling or retaining evidence. Stop and report missing governance rather than inventing permission.
4. Preserve Phase 1 behavior and evidence while adding the smallest complete vertical slice.

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

## Evaluate the Phase 2 gate

Pass only when:

- at least 90% of synthetic fields receive a proposed semantic classification;
- 100% retain physical metadata and evidence references;
- known primary/foreign-key relationships have expected evidence;
- low-confidence and privacy-relevant entries reach review;
- repeat runs produce controlled, idempotent results;
- tests and contract validation succeed.

Capture machine-readable results plus a concise evidence summary under `docs/evidence/`. Report files changed, commands or jobs run, acceptance evidence, unresolved governance decisions, and the next eligible phase.
