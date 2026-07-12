---
name: insurance-lake-next-steps
description: Advance the agentic insurance domain solution after repository, VS Code, and Databricks synchronization setup. Use when Codex needs to select, implement, validate, or report the next MVP task in this repository, including running the synthetic Databricks notebooks, capturing an evidence pack, recording pilot governance decisions, building deterministic source-intelligence capabilities, creating contracts and tests, or progressing through implementation-plan phases.
---

# Insurance Lake Next Steps

Advance the project one governed, reviewable vertical slice at a time. Treat Git, VS Code, repository layout, and Databricks synchronization as complete unless direct evidence shows otherwise.

## Establish current state

1. Work from the repository root `D:\agentic-solution-domain-insurance` when available.
2. Read `docs/planning/IMPLEMENTATION_PLAN.md`, the root `README.md`, and the relevant code or contract before changing anything.
3. Inspect the working tree and preserve unrelated user changes.
4. Determine the earliest incomplete acceptance gate from repository evidence. Do not infer completion from an empty directory or a plan entry alone.
5. State the selected next step, expected artifact, and validation method before implementation.

## Enforce safety boundaries

- Use synthetic data and approved public learning material only.
- Never add client data, PII, claims narratives, proprietary COTS documentation, credentials, tokens, or production connection strings.
- Keep the solution recommendation-only. Do not deploy schemas, modify source systems, or run transformations against operational data.
- Keep observations, inferred semantics, evidence, confidence components, assumptions, contradictions, reviewer decisions, run IDs, and artifact versions distinct.
- Require human review for privacy-relevant, low-confidence, relationship, key, grain, financial-measure, and ontology-extension recommendations.
- Do not introduce an LLM, vector search, or value-level inspection before deterministic controls and evidence classification are proven.

## Execute the next delivery step

Follow this priority order unless the user explicitly selects another plan item.

### 1. Complete and evidence the Free Edition MVP

Use `src/databricks/00_config.py` through `04_validate_mvp.py` in numeric order. Confirm:

- the three synthetic Bronze tables, source observation dictionary, and review queue exist;
- every dictionary record contains physical type, proposed meaning, confidence, privacy class, run ID, and approval state;
- no record is automatically approved;
- at least one relationship and one privacy-relevant entry reaches review;
- the validation notebook succeeds.

Record table counts, validation output, run ID, artifact version, and reproducible queries in a repository evidence artifact. Screenshots may supplement but must not replace machine-readable results.

### 2. Capture pilot governance decisions

Create version-controlled decision records for:

- Policy versus Claims first-release scope;
- permitted evidence classes and prohibited inputs;
- architect, domain-steward, and privacy-steward reviewer roles;
- confidence threshold and mandatory-review rules;
- reviewer turnaround target and pilot scorecard.

Mark unknown decisions as unresolved with an owner. Never invent approval.

### 3. Build deterministic Source Intelligence v1

Implement the smallest end-to-end slice covering metadata extraction, minimized profiling, relationship inference, domain classification, privacy classification, and run tracking. Define contracts before producers. Validate outputs at write boundaries.

Add unit tests for known synthetic fields, privacy patterns, missing metadata, conflicting key patterns, incomplete profiles, disallowed evidence, and repeat-run idempotency. Route uncertain and privacy-relevant results to review.

### 4. Progress later phases only after gates pass

Proceed in order: governed knowledge packs and ontology; ontology/Silver/Gold recommendations; STTM and trust evaluation; evaluation and promotion. Use the acceptance gates in `docs/planning/IMPLEMENTATION_PLAN.md` as completion criteria.

## Implementation conventions

- Put Databricks implementation code in `src/databricks/`, schemas in `contracts/`, tests in `tests/`, synthetic fixtures in `data/synthetic/`, and evidence or decisions under `docs/` in a clearly named subfolder.
- Prefer deterministic functions with explicit inputs and outputs.
- Make writes idempotent and scoped by run ID and artifact version.
- Validate structured outputs against contracts before persistence.
- Avoid duplicating constants across notebooks; use the shared configuration.
- Update the root README when commands, layout, or operator workflow changes.
- Do not commit generated data, secrets, local environments, or Databricks credentials.

## Verify and report

Run the narrowest relevant checks first, then the broader validation appropriate to the change. Report:

1. the completed plan step and acceptance evidence;
2. files changed and tests run;
3. unresolved decisions, risks, or required human reviews;
4. the next eligible step.

Do not claim a phase complete unless every stated acceptance condition has evidence.
