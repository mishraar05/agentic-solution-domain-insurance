# Consolidated Review Recommendations — Codex · GLM 5.2 · Claude

Status: PROPOSED · Date: 2026-07-12 · Supersedes individual tool reviews.
Shared conclusion: architecture and governance principles are sound; executable foundations (contracts, labelled data, testable functions) must catch up before Governed Knowledge Foundation agentic development.

> Superseded in part on 2026-07-13: the bounded Source Documentation Agent is
> now an approved implementation direction. It may use an LLM only over
> prompt-eligible structural context and must route every result to human
> review. The older blanket LLM deferral below is retained as review history.

## 1. Fix the skill layer
- Replace the legacy next-step helper with `governed-work-package-router`; make it a lightweight router invoking `$establish-insurance-solution-governance`, `$build-source-intelligence-v1`, or `$build-governed-knowledge-foundation` according to acceptance-gate evidence; remove duplicated instructions.
- Replace hardcoded `D:\...` paths with "discover and work from the repository root"; replace tool-specific "Codex" wording with agent-neutral language.
- State in both build skills: LLMs and vector search become eligible in Governed Knowledge Foundation and later capabilities only after the deterministic gate passes.
- Add a capability sequence ↔ WP1–5 mapping to `IMPLEMENTATION_PLAN.md`; skills reference it.
- Add authorized COTS recognition to Source Intelligence v1 or document its deferral explicitly.

## 2. Resolve governance inconsistencies
- One rule: contracts, synthetic fixtures, and tests may proceed under `PROPOSED` governance; profiling, persisted recommendations, and gate completion require approved evidence and reviewer policies; nothing becomes authoritative without human approval.
- Assign named humans: Data Architect, Domain Steward, Privacy Steward, Architecture Lead, Evaluation Owner, Sponsor. Everything stays `PROPOSED` until the relevant person approves.
- [Claude] Review-queue contract must capture decision, rationale, and reviewer role from day one — reviewer decisions are the future calibration set and cannot be reconstructed retroactively.

## 3. Contracts before Source Intelligence producers
- Five JSON Schemas: `source_intelligence_run`, `source_object_observation`, `source_attribute_observation`, `profile_evidence`, `relationship_candidate`.
- Shared definitions in one `common.json` via `$ref`: run/artifact identifiers, source scope and version context, observed-vs-inferred, evidence references, confidence components, assumptions/contradictions, privacy classification, approval/reviewer state, timestamps/lifecycle.
- [Claude] Every schema carries `schema_version`; additive-only changes within a compatible contract generation. Pin the idempotency-key composition (scope + evidence snapshot + knowledge versions + task contract, blueprint Table 8) in the run contract.
- Every producer validates output before persistence.

## 4. Machine-readable evaluation
- Move the labelled set from Markdown to version-controlled JSON with its own schema, stable record IDs, and expected: domain, business meaning, ontology concept, privacy class, key role, relationship target, review routing. Markdown remains human summary only.
- Automated precision, recall, coverage, and routing calculations.
- [Claude] 19 rows cannot support a 90% gate or precision/recall — expand to 100+ labelled attributes stratified by domain and privacy class alongside fixture expansion, or downgrade the Source Intelligence gate to "directional" and say so.

## 5. Governed confidence scoring
- Formula: confidence = 0.35·naming + 0.20·type + 0.25·relationship + 0.10·cots_match + 0.10·standard_consistency. Persist component values and calculation version with every recommendation. Confidence routes review only; never grants approval.
- Unavailable components: record `NOT_AVAILABLE`. [Claude recommendation] renormalize over available components with an evidence-coverage floor — below ~60% of total weight available, force review. Zero-with-penalty conflates absent evidence with negative evidence. Record the chosen method in governance.
- [Claude] Weights are `PROPOSED` until validated against the labelled set. Record a v1→target component mapping (design doc §19.1: retrieval fit, COTS match, rule consistency, contradiction checks, reviewer history) so Governed Knowledge Foundation calibration inherits v1 history.

## 6. Refactor the deterministic MVP
- Extract naming, type, privacy, relationship, and confidence logic into testable functions; notebooks become orchestration entry points; reduce hidden `%run` coupling; replace exact-name lookups with transparent rule sets.
- Separate: physical extraction · profile evidence · semantic classification · relationship inference · privacy classification · confidence calculation · review routing.

## 7. Expand synthetic coverage
Add cases: null/empty, duplicate identifiers, missing PKs, orphan FKs, incompatible relationship types, conflicting naming signals, unknown columns, ambiguous mappings, personal-data patterns, prohibited evidence, date/amount boundaries, repeat-run idempotency, changed-input versioning, failure/retry. Synthetic only.

## 8. Tests before functionality
- Unit: domain classification, privacy classification, type compatibility, relationship inference, confidence components/weighting, review routing, contract accept/reject, prohibited-evidence rejection.
- Validation: idempotency, artifact versioning, missing metadata, incomplete profiles, conflicting keys, targeted invalidation, no auto-approval, evidence completeness.

## 9. Prohibited-evidence handling
Detect → stop before profiling/retention → record sanitized policy-violation event → route only the exception decision to a human. No prohibited value in logs, prompts, evidence tables, or review payloads.
[Claude] The violation event gets its own contract schema; add a scan test that plants prohibited values in fixtures and greps every persisted artifact and log for leakage.

## 10. Agent-readable documentation
Office files remain presentation artifacts; Markdown counterparts hold canonical decisions, boundaries, schemas, and workflows. Contracts/schemas are the authoritative implementation interface. Agents never parse .docx/.pptx/.xlsx. Add the capability-to-work-package mapping.

## 11. Deliberate deferral and order
Deferred (not blockers): agent prompts, LLM orchestration, vector search, full ontology packs, COTS retrieval, Silver/Gold agents, CI/CD.
Order: governance resolution → contracts → labelled-set JSON → testable deterministic functions → expanded fixtures → unit/validation tests → Source Intelligence acceptance evidence → Governed Knowledge Foundation knowledge + agentic capabilities → CI/CD.
[Claude] CI uses GitHub Actions for pure-Python unit tests only, with no Databricks connection; workspace validation remains a separately governed runtime check.

## Execution backlog (with lanes for token economy)

Lane rule: deterministic code and bulk fixtures → Codex/GLM. Schemas, judges, governance wording, reviews → Claude (small, high-leverage artifacts only). Humans approve.

| Priority | Work item | Lane | Completion condition |
|---|---|---|---|
| IMMEDIATE | Resolve governance contradiction | Claude draft, human approve | One unambiguous PROPOSED-work rule |
| GOVERNANCE-SKILLS | Correct the three skills | Claude | Router delegates; portable paths; capability-to-work-package mapping; LLM expiry |
| IMMEDIATE | Five JSON contracts + common.json | Claude schema, Codex wiring | Valid schemas, shared defs, schema_version, idempotency key |
| IMMEDIATE | Labelled-set JSON + schema | Claude schema, Codex conversion | Machine-validatable fixture; expansion plan to 100+ |
| NEXT | Governed confidence formula | Codex, Claude review | Score traceable from components; NOT_AVAILABLE method recorded |
| NEXT | Extract deterministic logic | Codex/GLM | Notebooks orchestrate; functions tested |
| NEXT | Expand synthetic fixtures | Codex/GLM | §7 cases represented |
| NEXT | Unit + validation tests | Codex/GLM | §8 suites pass |
| FOLLOW-UP | Named human assignments | Human | Governance reviewed by named people |
| FOLLOW-UP | CI (pure-Python only) | Codex | Checks run on push |
| Deferred | Prompts + agentic layer | Claude | Only after deterministic Source Intelligence gate passes |

Cleanup: inspect untracked root file `d`; remove only if confirmed accidental.
