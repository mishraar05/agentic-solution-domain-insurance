# Phase 2 Critical Review — Consolidated (Codex + Claude) with Fix Status

Date: 2026-07-12 · Claude independently verified every Codex finding against the code before consolidation. Phase 2 gate remains **NOT PASSED** (items marked Deferred below are gate-blocking).

## Codex findings — all 16 verified, none refuted

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | Each notebook task generated its own RUN_ID (`%run 00_config` per task) | Critical | **FIXED** — `run_id` job parameter shared across tasks (`si_job_{{job.run_id}}` in job JSON); interactive fallback generates one; pattern-validated at startup |
| 2 | Run IDs (`si_`) violated contract pattern (`mvp_`) | Critical | **FIXED** — contract standardized to `^si_(\d{8}T\d{6}Z\|job_\d+)$`; config validates against it |
| 3 | `common.json` malformed (`""` instead of `$id`, no `$schema`) | Critical | **FIXED** — and now exercised by a standards-shaped resolver |
| 4 | Notebooks bypassed the deterministic core (duplicate embedded logic) | Critical | **FIXED** — 02/03 now import `source_intelligence.*` exclusively; embedded rules deleted |
| 5 | Confidence hardcoded; `naming_strength` derived from confidence; formula never invoked | Critical | **FIXED** — `compute_confidence()` invoked per attribute; all 5 component states, evidence coverage, formula version persisted |
| 6 | `mode("overwrite")` destroyed version history | Critical | **FIXED** — append-only, run-scoped persistence in 02/03/04 |
| 7 | No contract validation before persistence | Critical | **FIXED** — `contract_validation.py` (cross-file $ref resolver); 02 validates every record, 04 validates the run record; write aborts on violation |
| 8 | Core performed `CREATE SCHEMA` DDL | High | **FIXED** — config asserts the output schema exists; provisioning is a platform step |
| 9 | Key candidates not always routed for review | High | **FIXED** — mandatory KEY_CANDIDATE trigger → DATA_ARCHITECT in `routing.py`; 04 asserts every key candidate is queued |
| 10 | Review reason and reviewer could disagree | High | **FIXED** — atomic routing decision (trigger, reason, reviewer, priority); notebook 03 consumes it |
| 11 | No reviewer-decision lifecycle | High | **PARTIAL** — deterministic decision creation, role/rationale enforcement, exact queue linkage, and unchanged-rejection suppression are implemented; human workbench integration remains external |
| 12 | "Approved MVP naming rule" not backed by approval | High | **FIXED** — renamed "Deterministic candidate rule (not steward-approved)" |
| 13 | Labelled set circular (derived from the classifier's own lookup) | High | **OPEN** — requires independent human relabelling; cannot be fixed by code (see C8) |
| 14 | Improvements uncommitted | Medium | **OPEN** — commit is yours to make; suggested message below |
| 15 | No producer-level Spark tests | High | **DEFERRED** — needs a Spark runtime; next Databricks run should capture fresh evidence (12 in Codex sequence) |
| 16 | No CI | Medium | **FIXED** — `.github/workflows/ci.yml`: pytest + contract parse/validation check (pure Python, no Databricks) |

## Claude additional findings

| # | Finding | Status |
|---|---|---|
| C1 | `routing.py` accepted `key_role` but never used it — the *tested core itself* lacked mandatory key review, not just the notebook | FIXED (with #9) |
| C2 | The in-repo schema validator resolved only local `#/` refs — the five main contracts were **unvalidatable by any repo tooling**, making finding 7 structurally unfixable until now | FIXED — `contract_validation.py` |
| C3 | `policy.py` hardcoded a literal `mvp_…` run_id inside violation events (would fail the corrected contract) | FIXED — `run_id`/`source_system` parameters |
| C4 | `confidence.py` labelled `None` core components as `AVAILABLE` — misreporting evidence availability metadata | FIXED |
| C5 | `LOW_CONFIDENCE_THRESHOLD` duplicated in config and routing module (drift risk) | FIXED — threshold passed as parameter from config |
| C6 | `engagement_id` hardcoded inside notebook 02, violating the repo's own single-config convention | FIXED — moved to `00_config` |
| C7 | **Calibration finding:** with renormalized weights, typical known non-key columns score ≈0.71–0.74, below the 0.75 threshold — most rows will route to review. Formula and threshold were never co-calibrated. Deliberately NOT silently tuned: threshold must be set from labelled reviewer data (governance R-04, work plan 5.3) | OPEN — governance decision |
| C8 | Labelled set contradicted governance on PK rows (L001/L009/L014 expected `NONE`; policy mandates architect review of key candidates) — corrected as a policy-derived label fix. All other label/implementation disagreements retained untouched as genuine eval signal | PARTIAL — independent relabelling still required (F13) |
| C9 | Untracked root file `d` does not exist — stale finding, no action | CLOSED |

## What the fixes did NOT do

No LLM, vector search, or knowledge packs introduced (Phase 3 gate unchanged). No reviewer-decision producer invented without a workbench. No threshold tuning without labelled data. Confidence still gates routing only.

## Remaining gate-blocking sequence

1. Run the full job on Databricks with the shared `run_id` parameter; capture fresh evidence in `docs/evidence/` (validates fixes 1, 6, 7, 9 at runtime).
2. Producer-level Spark checks in `tests/validation/` executed in-workspace.
3. Independent human relabelling of the eval set (F13) → then calibrate threshold/weights (C7).
4. Reviewer-decision lifecycle via the workbench (F11).
5. Named human approvals of governance artifacts.
6. Commit. Suggested: `fix(phase2): single run context, contract enforcement at write, versioned persistence, atomic routing with mandatory key review, wired deterministic core, CI`
