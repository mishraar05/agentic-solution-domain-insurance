# Source Intelligence Foundation Readiness Report

**Artifact:** `SOURCE_INTELLIGENCE_FOUNDATION_READINESS.md`
**Version:** 0.1.0
**Date:** 2026-07-12
**Author:** Agent (Cline)
**Status:** SUPERSEDED BY PASSED SOURCE INTELLIGENCE GATE (2026-07-13)

## Work packages completed

| WP | Description | Status |
|---|---|---|
| WP-A | Baseline and repository safety | COMPLETE |
| WP-B | Governance and planning consistency | COMPLETE |
| WP-D | Contract foundation | COMPLETE |
| WP-E | Machine-readable labelled set | COMPLETE |
| WP-F | Extract deterministic Source Intelligence core | COMPLETE |
| WP-G | Governed confidence implementation | COMPLETE |
| WP-C | Skill layer corrections | COMPLETE |
| WP-H | Expanded executable synthetic fixtures | COMPLETE |

## Work packages remaining

| WP | Description | Status |
|---|---|---|
| WP-I | Full contract and producer validation suite | PARTIAL |
| WP-J | CI and quality gates | COMPLETE |

## Schemas and versions

| Schema | Version | Purpose |
|---|---|---|
| `common.json` | 1.0.0 | Reusable definitions |
| `source_intelligence_run.json` | 1.0.0 | Run status and metrics |
| `source_object_observation.json` | 1.0.0 | Object-level observations |
| `source_attribute_observation.json` | 1.0.0 | Attribute-level observations with confidence components |
| `profile_evidence.json` | 1.0.0 | Minimized profile summaries |
| `relationship_candidate.json` | 1.0.0 | Proposed keys/relationships |
| `review_decision.json` | 1.0.0 | Reviewer decisions with rationale |
| `policy_violation_event.json` | 1.0.0 | Sanitized prohibited-evidence rejections |
| `labelled_set.schema.json` | 1.0.0 | Evaluation set schema |
| `expanded_synthetic_fixtures.schema.json` | 1.0.0 | Executable edge-case fixture schema |

## Test and CI results

- **Local tests:** 129/129 passed, including unit and validation scenarios
- **Expanded fixture validation:** dependency-free schema subset validation, positive loading, and negative required-field rejection
- **Leakage validation:** prohibited sentinel injected as source input and confirmed absent from sanitized event output and captured logs
- **CI workflow:** `.github/workflows/ci.yml` runs local-safe tests and parses every contract without Databricks credentials
- **Remaining validation gap:** Spark producers require an in-workspace run with fresh evidence

## Labelled-set coverage

- **Records:** 26 (cross-convention, vendor abbreviation, ambiguous-token, and opaque-name coverage)
- **Stratification dimensions:** domain, privacy, ambiguity, key role, relationship, pattern type, review route
- **Coverage:** fixture acceptance only - not generalization evidence. Expansion to 100+ records is a planning target.
- **Executable edge cases:** 15 scenarios with real rows and machine-readable expected outcomes; these supplement but do not enlarge the labelled calibration set.

## Deterministic core modules

| Module | Functions |
|---|---|
| `knowledge_classifier.py` | Context-resolved naming, privacy, and type packs; separator/camel/continuous token hypotheses; fail-closed ambiguity; stable rule and selection provenance |
| `relationships.py` | Runtime-metadata key-role inference, relationship discovery, evidence grouping, and strength calculation |
| `cots_patterns.py` | `match_cots_pattern()` (returns NOT_AVAILABLE until governed reference patterns exist) |
| `confidence.py` | `compute_confidence()` with 5 weighted components, evidence coverage, renormalization |
| `routing.py` | `route_review()` with mandatory triggers |
| `source_documentation.py` | Prompt allow-listing, strict model-output validation, context fingerprinting, and non-authoritative documentation recommendation assembly |

## Confidence implementation

- **Formula:** `1.0.0` - 5 weighted components (naming 0.35, type 0.20, relationship 0.25, COTS 0.10, standard 0.10)
- **Availability states:** AVAILABLE, NOT_AVAILABLE, CONTRADICTED
- **Renormalization:** over available components only
- **Evidence coverage floor:** 0.60 - below this, forced review
- **No hardcoded scores** - all confidence values computed from components

## Human approvals

| Decision | Approved reviewer identifier |
|---|---|
| Confirm Policy as first-release scope | `HUMAN_REVIEWER_01` |
| Approve evidence classification matrix | `HUMAN_REVIEWER_01` |
| Assign named reviewers | `HUMAN_REVIEWER_01` |
| Confirm confidence weights and coverage floor | `HUMAN_REVIEWER_01` |
| Assign evaluation owner | `HUMAN_REVIEWER_01` |
| Assign sponsor | `HUMAN_REVIEWER_01` |

Governance artifacts were approved on 2026-07-13. Current evidence is recorded
in `SOURCE_INTELLIGENCE_COMPLETION_STATUS.md` and
`source_intelligence_local_gate.json`.

## Decision: May Source Intelligence producers proceed?

**YES - under approved governance.** Governed Knowledge Foundation may proceed. Outputs remain
recommendations until their routed human decisions; source access remains
read-only and prohibited evidence remains prohibited.

Source Intelligence producers (Databricks notebooks that use the deterministic core) may be implemented. Their outputs must:
1. Validate against contracts before persistence
2. Record all confidence components with availability states
3. Route all uncertain/privacy-relevant items to review
4. Never auto-approve any recommendation

## Next steps

1. **Databricks validation:** Run the contract-enforced producers in-workspace and capture evidence
2. **Independent labels:** Have a human relabel the evaluation set before calibration
3. **Calibration:** Approve or modify confidence weights and the review threshold
4. **Governance:** Assign named reviewers and approve or modify the PROPOSED artifacts
