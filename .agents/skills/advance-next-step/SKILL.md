---
name: advance-next-step
description: Router skill that determines the earliest incomplete acceptance gate and delegates to the appropriate specialist skill. Use when an agent needs to select, implement, validate, or report the next task in this repository.
---

# Advance Next Step

Router skill. Inspect repository evidence, determine the earliest incomplete gate, and delegate to the appropriate specialist skill. Do not restate specialist instructions.

## Establish current state

1. Discover and work from the repository root.
2. Read `docs/planning/IMPLEMENTATION_PLAN.md`, `docs/evidence/SOURCE_INTELLIGENCE_FOUNDATION_READINESS.md`, and the relevant code or contract before changing anything.
3. Inspect the working tree and preserve unrelated user changes.
4. Determine the earliest incomplete acceptance gate from repository evidence. Do not infer completion from an empty directory or a plan entry alone.
5. State the selected next step, expected artifact, and validation method before implementation.

## Enforce safety boundaries

- Use synthetic data and approved public learning material only.
- Never add client data, PII, claims narratives, proprietary COTS documentation, credentials, tokens, or production connection strings.
- Keep the solution recommendation-only. Do not deploy schemas, modify source systems, or run transformations against operational data.
- Treat source/Bronze tables as existing external inputs. Never create or populate them in the core workflow; synthetic setup is a separate optional demo/test process.
- Keep observations, inferred semantics, evidence, confidence components, assumptions, contradictions, reviewer decisions, run IDs, and artifact versions distinct.
- Require human review for privacy-relevant, low-confidence, relationship, key, grain, financial-measure, and ontology-extension recommendations.
- The governed Source Documentation Agent may use an LLM only for column
  descriptions and glossary proposals from prompt-eligible context. Vector
  search, semantic retrieval, and other LLM agents remain gated.

## Delegate to specialist skills

### If governance is unresolved

Invoke `$define-insurance-pilot-governance` to create or update pilot scope, evidence classification, reviewer model, confidence policy, evaluation plan, and go/no-go scorecard.

### If Source Intelligence work is needed

Invoke `$build-source-intelligence-v1` to implement contracts, metadata extraction, profiling, relationship inference, domain/privacy classification, confidence calculation, governed source documentation, review routing, and tests.

### If Phase 3+ work is requested

Stop. Governed knowledge retrieval, COTS retrieval, vector search, and target-
modelling agents are not permitted until the Source Intelligence acceptance
gate has evidence. Report what is missing. The bounded Source Documentation
Agent is the only current LLM exception.

## Verify and report

Run the narrowest relevant checks first, then the broader validation appropriate to the change. Report:

1. the completed plan step and acceptance evidence;
2. files changed and tests run;
3. unresolved decisions, risks, or required human reviews;
4. the next eligible step.

Do not claim a phase complete unless every stated acceptance condition has evidence.
