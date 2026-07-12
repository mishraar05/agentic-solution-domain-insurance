# Rules Change Log

Rules evolve while we build. Each change gets one dated line: what changed, why, decided by whom. This is the audit trail that replaces heavyweight change control during the PoC; it carries forward into the customer environment.

| Date | Rule changed | New position | Why | Decided by |
|---|---|---|---|---|
| 2026-07-13 | "No LLM before Phase 2 gate passes" | LLM permitted for one bounded capability: Source Documentation Agent over prompt-eligible structural context only. Vector search, knowledge retrieval, auto-approval, and LLM-derived confidence remain prohibited. | Documentation is the lowest-risk, highest-learning first LLM use; exercises the full agent harness early. | Sponsor (ratified in chat, 2026-07-13) |
| 2026-07-13 | Free Edition treated as a design constraint | Free Edition quotas are runtime/ops concerns only; all design, contracts, and documentation stay platform-complete for customer scale-up. | PoC will definitely scale up; FE-specific design would create rework. | Sponsor |
| 2026-07-13 | Profiling evidence sources | Lakehouse Monitoring added as a second governed profile-evidence producer via `lakehouse_monitoring_adapter.py`: privacy gate applied post-computation, k-anonymity rule (cardinality <= 20, value count >= 5) for value summaries, LAKEHOUSE_MONITORING producer tag in minimization_rule. Custom governed queries remain the primary producer. | Platform-native profiling wanted for scale-up; adapter keeps evidence policy enforcement in our code. | Sponsor |
