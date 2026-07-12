# Confidence Policy

**Artifact:** `04_confidence_policy.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** AI/ML Engineer (placeholder - awaiting assignment)
**Reviewer:** Data Architect (placeholder - awaiting assignment)
**Status:** PROPOSED

## Purpose

Defines how confidence scores are computed, what signals contribute, when mandatory review is triggered, and the prohibition on LLM self-rating.

## Confidence components

The overall confidence score is derived from weighted component evidence - never from LLM self-rating.

| Component | Description | Weight | Range |
|---|---|---|---|
| **Naming strength** | How strongly the column/table name matches a known semantic pattern or approved naming rule | 0.35 | 0.0 - 1.0 |
| **Type strength** | Compatibility of the physical data type with the proposed semantic concept | 0.20 | 0.0 - 1.0 |
| **Relationship strength** | Evidence of key/foreign-key relationships (naming overlap, compatible types, overlap ratios) | 0.25 | 0.0 - 1.0 |
| **COTS pattern match** | Strength of match against authorized product/module/version patterns | 0.10 | 0.0 - 1.0 |
| **Standard/rule consistency** | Consistency with enterprise standards and governed rules | 0.10 | 0.0 - 1.0 |

**Overall confidence** = Sum(component x weight)

## Threshold bands

| Band | Range | Routing | Description |
|---|---|---|---|
| **High** | >= 0.85 | No mandatory review (still PROPOSED) | Strong naming + type + relationship evidence |
| **Medium** | 0.75 - 0.84 | No mandatory review (still PROPOSED) | Good evidence but may have assumptions |
| **Low** | < 0.75 | **Mandatory review** - routed to Domain Steward | Insufficient evidence; steward validation required |

**Configured threshold:** `LOW_CONFIDENCE_THRESHOLD = 0.75` (in `src/databricks/00_config.py`)

## Mandatory review triggers

A recommendation is routed to review regardless of confidence score when any of the following are true:

| Trigger | Reviewer | Rationale |
|---|---|---|
| `privacy_class != INTERNAL` | Privacy Steward | Personal data requires privacy review |
| `relationship_evidence IS NOT NULL` | Data Architect | Inferred relationships require confirmation |
| `ontology_concept_id IS NULL` | Domain Steward | No approved ontology concept mapped |
| `key_role IN (PRIMARY_KEY_CANDIDATE, FOREIGN_KEY_CANDIDATE)` | Data Architect | Key assignments require architect confirmation |
| `contradictions IS NOT NULL` | Domain Steward | Conflicting evidence requires resolution |
| Financial measure proposed | Data Architect | Derived financial measures require review |
| Ontology extension proposed | Data Architect | New ontology concepts require review |

## Prohibitions

1. **No LLM self-rating:** The confidence score must never be derived from an LLM's own assessment of its output.
2. **No confidence inflation:** Components must reflect actual evidence - no defaulting to high scores when evidence is missing.
3. **No auto-approval:** Confidence gates workflow routing only. No score, however high, results in automatic approval.

## Testability

The confidence policy is testable via:
- Unit tests verifying that known synthetic fields produce expected confidence bands
- Validation tests verifying that low-confidence and privacy-relevant entries reach the review queue
- Repeat-run tests verifying idempotent confidence scores for the same input

## Open questions

- [ ] Are the component weights appropriate, or should they be tuned after initial review cycles?
- [ ] Should the COTS pattern match weight be increased once knowledge packs are loaded (Phase 3)?
- [ ] Should a "very high" band (>= 0.95) have different routing?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed confidence policy | Agent (Cline) |
