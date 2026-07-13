---
name: governed-work-package-router
description: Route repository work to the earliest eligible governed work package and matching specialist skill. Use when an agent needs to determine, implement, validate, or report the next repository task without bypassing acceptance gates.
---

# Governed Work Package Router

Route repository work to the earliest eligible governed work package and the
appropriate specialist skill. Do not restate specialist instructions.

## Establish current state

1. Discover and work from the repository root.
2. Read `docs/planning/IMPLEMENTATION_PLAN.md`, `docs/evidence/SOURCE_INTELLIGENCE_FOUNDATION_READINESS.md`, and the relevant code or contract before changing anything.
3. Inspect the working tree and preserve unrelated user changes.
4. Determine the earliest incomplete acceptance gate from repository evidence. Do not infer completion from an empty directory or a plan entry alone.
5. State the selected work package, expected artifact, and validation method before implementation.

## Enforce safety boundaries

- Use synthetic data and approved public learning material only.
- Never add client data, PII, claims narratives, proprietary COTS documentation, credentials, tokens, or production connection strings.
- Keep the solution recommendation-only. Do not deploy schemas, modify source systems, or run transformations against operational data.
- Treat source/Bronze tables as existing external inputs. Never create or populate them in the core workflow; synthetic setup is a separate optional demo/test process.
- Keep observations, inferred semantics, evidence, confidence components, assumptions, contradictions, reviewer decisions, run IDs, and artifact versions distinct.
- Require human review for privacy-relevant, low-confidence, relationship, key, grain, financial-measure, and ontology-extension recommendations.
- The governed Source Documentation Agent may use an LLM only for column descriptions and glossary proposals from prompt-eligible context. Vector search, semantic retrieval, and other LLM agents remain gated.

## Delegate to specialist skills

### If solution governance is unresolved

Invoke `$establish-insurance-solution-governance` to create or update governed scope, evidence controls, reviewer accountability, trust policy, evaluation controls, and promotion criteria.

### If Source Intelligence work is needed

Invoke `$build-source-intelligence-v1` to implement contracts, metadata extraction, profiling, relationship inference, domain/privacy classification, confidence calculation, governed source documentation, review routing, and tests.

### If governed knowledge work is requested

Verify the Source Intelligence gate is `PASSED`. If it is not, stop and report
the missing evidence. If it is, invoke `$build-governed-knowledge-foundation`
for ontology, COTS knowledge, recognition, or exact context assembly work.
Vector search and target-model execution remain out of scope unless a later
governed work package explicitly unlocks them.

## Verify and report

Run the narrowest relevant checks first, then the broader validation appropriate to the change. Report:

1. the completed work package and acceptance evidence;
2. files changed and tests run;
3. unresolved decisions, risks, or required human reviews;
4. the next eligible work package.

Do not claim a capability complete unless every stated acceptance condition has evidence.
