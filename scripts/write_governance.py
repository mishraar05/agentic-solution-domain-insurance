import os

GOV_DIR = r"d:\agentic-solution-domain-insurance\docs\governance"
os.makedirs(GOV_DIR, exist_ok=True)

artifacts = {}

artifacts["02_evidence_classification.md"] = """# Evidence Classification Matrix

**Artifact:** `02_evidence_classification.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** Privacy Steward (placeholder - awaiting assignment)
**Reviewer:** Platform Owner (placeholder - awaiting assignment)
**Status:** PROPOSED

## Purpose

Defines which evidence classes may be observed, profiled, retained, indexed, or used as prompt context in the Free Edition pilot. Disallowed classes are rejected before profiling, indexing, retention, or prompt construction.

## Evidence classes

| Evidence class | Permitted operations | Retention | Prompt/retrieval eligible | Minimization rule | Reviewer | Prohibition rationale |
|---|---|---|---|---|---|---|
| **Physical metadata** (table name, column name, data type, nullable, ordinal position) | Observe, profile, retain, index | Full retention | Yes | None - non-sensitive | Domain Steward | N/A - permitted |
| **Key/relationship metadata** (primary key, foreign key, naming patterns) | Observe, infer, retain | Full retention | Yes | None - structural | Data Architect | N/A - permitted |
| **Aggregate profile** (null rate, distinct count, min/max, pattern summary) | Observe, profile, retain | Full retention | Yes | Aggregate only - no individual values | Domain Steward | N/A - permitted (synthetic data) |
| **Controlled value summary** (enum/domain values, frequency counts) | Observe, profile, retain | Full retention | Yes | Frequency counts only - no individual records | Domain Steward | N/A - permitted (synthetic data) |
| **Column name patterns** (naming conventions, semantic hints) | Observe, infer, retain | Full retention | Yes | None - non-sensitive | Domain Steward | N/A - permitted |
| **Personal data indicators** (column names suggesting PII: display_name, email, phone, address, birth, ssn) | Observe name only, classify, route to review | Name + classification retained | No - not eligible for prompt context | Column name only - never inspect values | Privacy Steward | Value-level inspection prohibited; only the column name is observed |
| **Claims narratives** (free-text loss descriptions) | Prohibited | Not retained | No | N/A | Privacy Steward | Prohibited in Free Edition; not present in synthetic MVP |
| **Client/production data** | Prohibited | Not retained | No | N/A | Privacy Steward | Prohibited - Free Edition uses synthetic data only |
| **PII values** (actual email addresses, phone numbers, SSNs, names) | Prohibited | Not retained | No | N/A | Privacy Steward | Prohibited - value-level inspection of PII is never permitted |
| **Credentials / connection strings** | Prohibited | Not retained | No | N/A | Platform Owner | Prohibited - no credentials in repo or Databricks workspace |
| **Proprietary COTS documentation** | Prohibited | Not retained | No | N/A | Domain Steward | Prohibited - no licensed material in Free Edition |

## Rules

1. **Observe before infer:** Physical metadata is observed; semantic meaning is inferred and labelled as such.
2. **No value-level inspection:** The system never reads individual data values for PII columns. Only column names and aggregate statistics are observed.
3. **Reject before profile:** If a column is classified as personal data, value-level profiling is rejected before it runs.
4. **Synthetic data only:** All evidence in the Free Edition pilot comes from synthetic Bronze tables. No client data is permitted.
5. **Retention scope:** Evidence is retained in Delta tables within `workspace.agentic_insurance_mvp` only. No external retention.

## Open questions

- [ ] Who is the named privacy steward? (placeholder until assigned)
- [ ] Should aggregate profiling be permitted for personal-data columns (e.g., null rate only)?
- [ ] Is there a data retention policy beyond the Free Edition pilot?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed evidence classification matrix | Agent (Cline) |
"""

artifacts["03_reviewer_model.md"] = """# Reviewer Model and RACI

**Artifact:** `03_reviewer_model.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** Architecture Lead (placeholder - awaiting assignment)
**Reviewer:** Sponsor (placeholder - awaiting assignment)
**Status:** PROPOSED

## Reviewer roles

| Role | Responsibility | Decision rights | Turnaround target | Backup |
|---|---|---|---|---|
| **Data Architect** | Approves key/relationship candidates, target grain, Silver entity structure, and ontology extensions | APPROVE, MODIFY, REJECT, DEFER | 3 business days | Enterprise Architect (placeholder) |
| **Domain Steward** | Approves semantic mappings, business names, domain classifications, and COTS pattern matches | APPROVE, MODIFY, REJECT, DEFER | 3 business days | Product SME (placeholder) |
| **Privacy Steward** | Approves privacy classifications, evidence-class decisions, and personal-data routing | APPROVE, MODIFY, REJECT, DEFER | 2 business days | Security/Legal (placeholder) |

## RACI matrix

| Decision type | Data Architect | Domain Steward | Privacy Steward | Sponsor | Agent |
|---|---|---|---|---|---|
| Pilot scope | A | C | C | I | R |
| Evidence classification | I | C | A | I | R |
| Key/relationship candidates | A | C | I | - | R |
| Semantic mapping | C | A | I | - | R |
| Privacy classification | I | C | A | - | R |
| Target grain (Silver/Gold) | A | C | I | I | R |
| Financial measures | A | C | C | I | R |
| Ontology extension | A | C | C | I | R |
| Go/no-go promotion | C | C | C | A | R |

*Legend: R = Responsible, A = Accountable, C = Consulted, I = Informed*

## Service-level targets

| Metric | Target | Measurement |
|---|---|---|
| Reviewer turnaround (median) | <= 3 business days (architect/steward), <= 2 business days (privacy) | Time from queue_status = OPEN to queue_status = CLOSED |
| Reviewer throughput | 100% of open items addressed within 1 sprint | Count of open vs. closed items per sprint |
| Override rate | Track and understand; reduce by iteration | Materially changed/rejected / reviewed recommendations |

## Rules

1. **No auto-approval:** The agent never marks any recommendation as APPROVED. All material recommendations start as PROPOSED.
2. **Reviewer rationale required:** Every decision (APPROVE, MODIFY, REJECT, DEFER) must include a rationale.
3. **No silent reappearance:** Rejected or modified recommendations retain their rationale and do not silently reappear unchanged in subsequent runs.
4. **Targeted invalidation:** When a material decision changes, only downstream dependent artifacts are invalidated - not the entire pipeline.
5. **Role placeholders:** All roles are placeholders until named humans accept assignment.

## Open questions

- [ ] Who fills each reviewer role? (all three are placeholders)
- [ ] Is the 3-business-day turnaround target realistic for the pilot?
- [ ] Should the backup roles be formalized or remain ad-hoc?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed reviewer model and RACI | Agent (Cline) |
"""

artifacts["04_confidence_policy.md"] = """# Confidence Policy

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

**Configured threshold:** `LOW_CONFIDENCE_THRESHOLD = 0.75` (in `src/workflows/source_intelligence/00_config.py`)

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
"""

artifacts["05_evaluation_plan.md"] = """# Evaluation Plan

**Artifact:** `05_evaluation_plan.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** Evaluation Owner (placeholder - awaiting assignment)
**Reviewer:** AI/ML Engineer (placeholder - awaiting assignment)
**Status:** PROPOSED

## Purpose

Defines how recommendation quality is measured using a labelled reviewer-decision set, precision/recall, override rate, throughput, reliability, cost/latency, and sensitive-evidence compliance.

## Labelled evaluation set

A labelled set of known-correct semantic mappings for the synthetic Bronze tables will be maintained in `evals/labelled_set/`.

| Source table | Source column | Expected business name | Expected ontology concept | Expected domain | Expected privacy class |
|---|---|---|---|---|---|
| bronze_policy | policy_id | Policy Identifier | Policy.Identifier | Policy | INTERNAL |
| bronze_policy | policy_number | Policy Number | Policy.PolicyNumber | Policy | INTERNAL |
| bronze_policy | policy_status | Policy Status | Policy.Status | Policy | INTERNAL |
| bronze_policy | effective_date | Policy Effective Date | Policy.EffectiveDate | Policy | INTERNAL |
| bronze_policy | expiration_date | Policy Expiration Date | Policy.ExpirationDate | Policy | INTERNAL |
| bronze_policy | product_code | Insurance Product Code | Product.Code | Shared | INTERNAL |
| bronze_policy | insured_party_id | Insured Party Identifier | Party.Identifier | Shared | INTERNAL |
| bronze_policy | source_updated_ts | Source Updated Timestamp | Technical.SourceUpdatedTimestamp | Shared | INTERNAL |
| bronze_policyholder | party_id | Party Identifier | Party.Identifier | Shared | INTERNAL |
| bronze_policyholder | party_type | Party Type | Party.Type | Shared | INTERNAL |
| bronze_policyholder | display_name | Display Name | (unresolved) | Shared | PERSONAL_DATA |
| bronze_policyholder | contact_channel | Contact Channel | (unresolved) | Shared | INTERNAL |
| bronze_policyholder | source_updated_ts | Source Updated Timestamp | Technical.SourceUpdatedTimestamp | Shared | INTERNAL |
| bronze_claim | claim_id | Claim Identifier | Claim.Identifier | Claims | INTERNAL |
| bronze_claim | policy_id | Policy Identifier | Policy.Identifier | Policy | INTERNAL |
| bronze_claim | loss_date | Loss Date | Claim.LossDate | Claims | INTERNAL |
| bronze_claim | claim_status | Claim Status | Claim.Status | Claims | INTERNAL |
| bronze_claim | claimed_amount | Claimed Amount | Claim.ClaimedAmount | Claims | INTERNAL |
| bronze_claim | source_updated_ts | Source Updated Timestamp | Technical.SourceUpdatedTimestamp | Shared | INTERNAL |

## Metrics

| Metric | How to measure | Target direction | Baseline |
|---|---|---|---|
| **Semantic classification coverage** | % of synthetic fields receiving a proposed classification | >= 90% | 100% (MVP) |
| **Mapping precision** | Correct mappings / total proposed mappings | Improve against baseline | To be measured |
| **Mapping recall** | Correct mappings / total labelled correct mappings | Improve against baseline | To be measured |
| **Reviewer override rate** | Materially changed/rejected / reviewed recommendations | Understand and reduce by iteration | To be measured |
| **Reviewer throughput** | Median time from recommendation to final decision | <= 3 business days (architect/steward), <= 2 business days (privacy) | To be measured |
| **Workflow reliability** | Failed/retried runs and targeted-reprocessing success rate | Demonstrate controlled recovery | 0 failures (MVP) |
| **Cost and latency** | Compute usage and elapsed time per source object and workflow stage | Meet pilot budget | ~2 min (MVP run) |
| **Sensitive-evidence compliance** | Inputs passing evidence-classification controls | 100% | 100% (MVP) |

## Reviewer-decision capture

Each review decision is captured with:
- `source_table`, `source_column` (what was reviewed)
- `recommended_reviewer_role` (who should review)
- `review_reason` (why it was routed)
- `queue_status` (OPEN, CLOSED)
- Reviewer decision: APPROVED, MODIFIED, REJECTED, DEFERRED
- `review_rationale` (why the reviewer made their decision)
- Timestamp of decision

## Evidence sources

| Evidence source | Location |
|---|---|
| MVP run evidence | `docs/evidence/mvp_run_evidence.json` |
| MVP evidence summary | `docs/evidence/MVP_RUN_EVIDENCE.md` |
| Labelled set | `evals/labelled_set/` (to be created) |
| Review queue | `workspace.agentic_insurance_mvp.review_queue` (Databricks) |
| Job run history | Databricks job run API |

## Open questions

- [ ] Who is the named evaluation owner?
- [ ] Should the labelled set be a JSON file or a Delta table?
- [ ] What is the acceptable precision/recall baseline for Source Intelligence?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed evaluation plan | Agent (Cline) |
"""

artifacts["06_go_no_go_scorecard.md"] = """# Go/No-Go Scorecard

**Artifact:** `06_go_no_go_scorecard.md`
**Version:** 0.1.0
**Decision Date:** 2026-07-12
**Owner:** Sponsor (placeholder - awaiting assignment)
**Reviewer:** Architecture Lead (placeholder - awaiting assignment)
**Status:** PROPOSED

## Purpose

Defines the metrics, baselines, targets, and decision rules for the go/no-go promotion decision at the end of the pilot.

## Scorecard

| Metric | Baseline | Target | Evidence source | Owner | Status | Decision rule |
|---|---|---|---|---|---|---|
| **Evidence completeness** | 100% (MVP) | 100% | `docs/evidence/mvp_run_evidence.json` | Data Architect | PROPOSED | Go only if 100% of material recommendations have all required fields |
| **Semantic classification coverage** | 100% (MVP, 19/19 fields) | >= 90% | `source_observation_dictionary` table | Domain Steward | PROPOSED | Go only if >= 90% of fields have a proposed classification |
| **Mapping precision** | To be measured | Improve against baseline | Labelled set comparison | Evaluation Owner | DEFERRED | Go only if precision meets agreed baseline (TBD) |
| **Mapping recall** | To be measured | Improve against baseline | Labelled set comparison | Evaluation Owner | DEFERRED | Go only if recall meets agreed baseline (TBD) |
| **Reviewer override rate** | To be measured | Understand and reduce by iteration | Review queue decisions | Architecture Lead | DEFERRED | Go only if override rate is understood and trending down |
| **Reviewer throughput** | To be measured | <= 3 business days (architect/steward), <= 2 business days (privacy) | Review queue timestamps | Architecture Lead | DEFERRED | Go only if median turnaround meets SLA |
| **Workflow reliability** | 0 failures (MVP) | Demonstrate controlled recovery | Job run history | Platform Engineer | PROPOSED | Go only if failed/retried runs demonstrate targeted reprocessing |
| **Cost and latency** | ~2 min (MVP run) | Meet pilot budget | Databricks job metrics | Platform Engineer | PROPOSED | Go only if within pilot budget |
| **Sensitive-evidence compliance** | 100% (MVP) | 100% | Evidence classification checks | Privacy Steward | PROPOSED | Go only if 100% of inputs pass evidence-classification controls |
| **No auto-approval** | 0 auto-approved (MVP) | 0 | `source_observation_dictionary.approval_state` | Data Architect | PROPOSED | Go only if zero records are auto-approved |

## Promotion criteria

Before moving from Free Edition to a business trial or paid Databricks workspace:

1. A named business sponsor and data owner are assigned.
2. An approved security, privacy, retention, and access-control design exists.
3. Controlled source connectivity and service identities are designed.
4. A reviewed model-serving, AI Search, and monitoring design exists.
5. A documented incident, rollback, and support model exists.
6. All scorecard metrics with PROPOSED status are confirmed by the responsible owner.
7. All DEFERRED metrics have been measured and meet their targets.

## Current status summary

- **MVP foundation:** Complete - all acceptance gate criteria passed
- **Phase 0 (Governance):** PROPOSED - all artifacts created, awaiting human review and assignment
- **Source Intelligence v1:** Not started - blocked until pilot governance is reviewed

## Open questions

- [ ] Who is the named sponsor?
- [ ] What are the acceptable precision/recall baselines for mapping quality?
- [ ] What is the pilot budget for cost and latency?
- [ ] What constitutes a "controlled recovery" for workflow reliability?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed go/no-go scorecard | Agent (Cline) |
"""

artifacts["00_phase0_gate_validation.md"] = """# Phase 0 Governance Gate Validation

**Artifact:** `00_phase0_gate_validation.md`
**Version:** 0.1.0
**Validation Date:** 2026-07-12
**Validator:** Agent (Cline)
**Status:** PROPOSED - gate criteria structurally met; awaiting human review

## Gate criteria

| Criterion | Met? | Evidence |
|---|---|---|
| One pilot scope and its exclusions are explicit | YES | `01_pilot_scope.md` - Policy scope, included/excluded objects, rationale |
| Every evidence class has a permitted/prohibited decision | YES | `02_evidence_classification.md` - 11 evidence classes with decisions |
| All three reviewer roles and decision rights are defined | YES | `03_reviewer_model.md` - Data Architect, Domain Steward, Privacy Steward with RACI |
| Threshold and mandatory-review rules are testable | YES | `04_confidence_policy.md` - 5 components, 3 bands, 7 mandatory triggers, testability section |
| Evaluation metrics and evidence sources are named | YES | `05_evaluation_plan.md` - 8 metrics, labelled set, evidence sources |
| Unresolved items have an owner and do not masquerade as approval | YES | All artifacts are PROPOSED; open questions listed with owner placeholders |

## Artifacts created

| File | Artifact | Status |
|---|---|---|
| `01_pilot_scope.md` | Pilot scope decision record | PROPOSED |
| `02_evidence_classification.md` | Evidence classification matrix | PROPOSED |
| `03_reviewer_model.md` | Reviewer model and RACI | PROPOSED |
| `04_confidence_policy.md` | Confidence policy | PROPOSED |
| `05_evaluation_plan.md` | Evaluation plan | PROPOSED |
| `06_go_no_go_scorecard.md` | Go/no-go scorecard | PROPOSED |

## Decisions still awaiting humans

| Decision | Owner (placeholder) | Artifact |
|---|---|---|
| Confirm Policy as first-release scope | Data Architect | `01_pilot_scope.md` |
| Approve evidence classification matrix | Privacy Steward | `02_evidence_classification.md` |
| Assign named reviewers to all three roles | Architecture Lead | `03_reviewer_model.md` |
| Confirm confidence component weights and threshold | AI/ML Engineer | `04_confidence_policy.md` |
| Assign evaluation owner and set precision/recall baselines | Evaluation Owner | `05_evaluation_plan.md` |
| Assign sponsor and confirm pilot budget | Sponsor | `06_go_no_go_scorecard.md` |

## Validation result

The Phase 0 governance gate is **structurally complete** - all six required artifact types exist with the required content. However, all artifacts carry PROPOSED status because no human has reviewed or approved them. Per the hard rules in AGENTS.md (rule 5), these artifacts cannot be treated as authoritative until human review occurs.

**Source Intelligence may proceed in a PROPOSED capacity** - contracts and code can be developed against these proposed governance decisions, but no output may be treated as authoritative until the governance artifacts are reviewed and approved by the named human reviewers.

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial Phase 0 gate validation | Agent (Cline) |
"""

for filename, content in artifacts.items():
    path = os.path.join(GOV_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {filename}")

print(f"\nAll {len(artifacts)} governance artifacts written.")
