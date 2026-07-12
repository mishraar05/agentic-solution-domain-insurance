# insurance-lake

Agentic Target Modeling MVP on Databricks Free Edition — a governed, recommendation-only system that analyzes Bronze metadata and recommends trusted Silver ODS / Gold models for P&C insurance. **Learning build only** (synthetic data, non-commercial); scale-up happens in a customer environment.

Companion documents: `docs/design/` (Architecture Design v0.2), `docs/planning/` (Pilot Blueprint v0.1, Excel work plan — see its *Free Edition Fit* sheet).

## Layout

| Path | Contents | Built by |
|---|---|---|
| `docs/architecture/` | Solution architecture deck (agents, harness, memory, guardrails) | — |
| `docs/planning/` | Work plan (43 tasks, 5 work packages), blueprint, implementation plan | — |
| `docs/design/` | Approved design document | — |
| `contracts/` | Structured output contracts (JSON schema) per agent — build these first (task 2.6) | Claude |
| `prompts/` | Versioned agent system prompts (Orchestrator + 6 specialists) | Claude |
| `knowledge_packs/` | Ontology, COTS-like references, standards, rules (synthetic/open only) | Claude exemplars, Codex volume |
| `evals/` | MLflow judges + labelled reviewer-decision set | Claude |
| `src/databricks/` | Numbered MVP notebooks (00 config → 04 validate) | Codex |
| `scripts/` | Document generators and utilities | Codex |
| `config/` | Single environment config (Free Edition = one workspace; env split deferred) | Codex |
| `tests/` | `unit/` + `validation/` (recovery & invalidation scenarios, task 4.7) | Codex |
| `data/synthetic/` | Generated synthetic Bronze source data | Codex |
| `notebooks/exploration/` | Ad-hoc exploration and demos | either |

## Rules of the road

- Recommendation-only: no DDL, no deployment, no ingestion code anywhere in this repo (design decision D-04).
- Agents get read/query/retrieval tools only (D-08); enforced in code on Free Edition.
- Every agent output must validate against its contract in `contracts/` before it lands in the recommendation repository.
- `agentic-solution-domain-insurance/` is a separate nested git repo — register as a submodule or fold into `knowledge_packs/`.
