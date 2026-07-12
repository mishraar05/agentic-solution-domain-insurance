# Agent Instructions — agentic-solution-domain-insurance

Rules for any coding or reasoning agent working in this repo (Codex, Claude, GLM, Databricks assistants). Read once; do not restate in outputs.

## Project

Agentic Target Modeling solution on Databricks (currently a proof of concept; will scale to a full customer environment). Recommendation-only system: analyzes existing source-aligned/Bronze metadata and recommends Silver ODS / Gold models, ontology mappings, and STTMs for P&C insurance. The optional synthetic Bronze harness is isolated under `examples/synthetic_bronze/` and is never part of the core job. Canonical docs: `docs/design/` (architecture v0.2), `docs/planning/` (blueprint v0.1 + Excel work plan = task source of truth). Run evidence lives in `docs/evidence/`.

## Hard rules (never violate)

1. Recommendation-only: never generate deployment DDL, ingestion, transformation-execution, or migration code. Structure recommendations are data records, not executable schemas.
2. Agent tool surface is read/query/retrieval only. No write, deploy, execute, credential, or ingest capability in any agent tool binding.
3. No client data, PII, licensed COTS documentation, credentials, or connection strings anywhere in this repo.
4. Separate observed facts from inferred meaning in every artifact; unresolved stays unresolved — never invent semantics.
5. Confidence gates workflow routing only; human approval is required before any artifact is authoritative.
6. Existing source/Bronze tables are external read-only inputs. Never create, ingest, overwrite, or populate them in the core solution. Synthetic source creation belongs only in the isolated demo/test harness.

## Layout and ownership

- `contracts/` — JSON output contracts per agent. Build first; all agent outputs must validate against them.
- `prompts/` — versioned agent system prompts (one file per agent, `NN_agent_name.md`).
- `knowledge_packs/` — synthetic ontology, COTS-like references, standards, rules.
- `evals/` — judges and labelled reviewer-decision set.
- `src/workflows/source_intelligence/` — numbered workflow entry-point notebooks (`NN_purpose.py`).
- `examples/synthetic_bronze/` — optional demo/test fixture creation; separate job, never a core dependency.
- `tests/unit`, `tests/validation` — validation covers retry/invalidation scenarios.
- `.agents/skills/` — reusable task skills; check for a matching skill before improvising a workflow.

## Conventions

- Naming: `snake_case` files, numbered execution order (`00_`, `01_`), no tool-specific names or folders. Everything must run from plain Databricks notebooks/jobs — no vendor-specific agent framework assumed.
- Python: PEP 8, stdlib + PySpark + Databricks SDK only unless a dependency already exists in the repo.
- Config: single environment; DAB/job parameters supply source and output scope, and `src/workflows/source_intelligence/00_config.py` validates them and owns governed versions/thresholds. No hardcoded catalog/schema names elsewhere.
- Platform neutrality: design for the full Databricks platform; never bake current PoC-environment quotas (warehouse size, job concurrency, endpoint counts) into designs, contracts, or documentation. Runtime quotas are handled operationally (parameters, sequential scheduling), not architecturally.
- Rule changes are expected while building. When a governing rule changes, add a dated one-line entry to `docs/planning/RULES_LOG.md` (what changed, why, decided by whom) — then move on.

## Token economy

Be brief. Read `contracts/` and the relevant schema extract instead of parsing .docx/.pptx/.xlsx. Do not regenerate unchanged files; edit in place. No summaries of what you just did beyond one line.
