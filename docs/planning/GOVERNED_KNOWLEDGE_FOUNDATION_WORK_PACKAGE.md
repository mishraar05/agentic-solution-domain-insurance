# Governed Knowledge Foundation Work Package — Governed COTS Knowledge and Insurance Ontology

**Work package ID:** `GOVERNED-KNOWLEDGE-FOUNDATION`

**Version:** `1.0.0`

**Status:** READY FOR EXECUTION

**Current execution:** `BASELINE-AUTHORIZATION` through `PACK-AUTHORING` COMPLETE FOR DEVELOPMENT;
`KNOWLEDGE-PUBLICATION` is next. The review workflow is deferred until the end-to-end solution is ready, as recorded in
[`08_knowledge_baseline_evidence_authorization.md`](../governance/08_knowledge_baseline_evidence_authorization.md)

**Prerequisite:** Source Intelligence gate `PASSED`

**Accountable roles:** Data Architect, Domain Steward, Privacy Steward

**Execution boundary:** recommendation-only; source systems remain read-only

## 1. Outcome

Build an authoritative, version-specific knowledge foundation that allows the
Source Intelligence workflow to recognize governed source patterns, propose
insurance ontology mappings, identify likely source extensions, and explain exactly
which approved knowledge-pack version and evidence produced each result.

The target statement is:

> This source structure resembles product P, module M, version V; it maps to
> these approved P&C concepts, contains these likely extensions, and was
> classified using knowledge pack K at version Y with evidence E.

Every statement remains a recommendation until the routed human reviewer
approves it.

## 2. Controlled development boundary

### Selected development baseline

| Dimension | Selection |
|---|---|
| Product | `cots_like_suite` |
| Modules | `policy_admin`, `claims_mgmt`, and `billing`, each in a separate pack |
| Version | `1.0.0` |
| Evidence source | Existing vendor-neutral synthetic reference pack |
| Domains | Policy, Claims, Billing, and Shared dependencies |
| LOB | Personal Lines taxonomy |
| Claim permitted | Synthetic COTS-like resemblance only; never a real-vendor identification |

This baseline is intentionally synthetic and vendor-neutral. It is not derived
from Guidewire, Majesco, Origami, or other licensed material. In a licensed
customer environment, the same contracts may be populated by one explicitly
approved real product/module/version pack. No result may name a real vendor
unless that exact pack and its evidence authorization are active.

### Governed ontology scope

- All concepts declared by `insurance_ontology / 1.0.0`: Policy, Claims,
  Billing, Shared, Risk, Document, Motor, Home, Commercial Property, and the
  separately governed Pensions domain.
- Product-area coverage includes Motor, Home, Commercial Property, and
  Pensions with controlled vocabularies, logical reference shapes, synthetic
  examples, and recommendation-only mapping templates.
- The narrower `pnc_ontology / 1.1.0` predecessor pack has been retired; all of
  its stable concept IDs are preserved unchanged in the broader ontology.
- All relationships whose endpoints resolve within those declared domains.
- Exact module packs remain isolated even though they resolve to one governed
  cross-domain ontology.

### Excluded from this work package

- Multiple simultaneous COTS products or versions.
- Licensed or proprietary documentation without explicit authorization.
- Client schemas, client data, PII values, credentials, or connection strings.
- Vector search, embedding retrieval, or unrestricted semantic search.
- LLM-generated confidence, invented concept IDs, or automatic approval.
- Silver/Gold DDL, transformations, ingestion, migration, or deployment code.
- Production promotion; its deferred scorecard metrics remain separate gates.

## 3. Design decisions

1. Contracts precede producers and tables.
2. Structured deterministic lookup precedes any future semantic retrieval.
3. Context selection is an exact filter over engagement, product, module,
   version, domain, LOB, effective date, and approval state.
4. No cross-version fallback is allowed. Missing or conflicting versions fail
   closed as `Unresolved`.
5. Every match records `pack_id`, `pack_version`, product, module, version,
   pattern ID, evidence reference, and deterministic confidence components.
6. Exact known patterns may be `MATCHED`; absent fields on an otherwise strong
   object match may be `LIKELY_CUSTOM_EXTENSION`; unsupported or ambiguous
   structures remain `UNRESOLVED`.
7. Knowledge lifecycle states are `Standard`, `Specialized`,
   `Source extension`, `Candidate`, and `Unresolved`.
8. Infrastructure provisioning is external. This package defines logical
   contracts and validated append-only producers, never deployment DDL.
9. Intermediate human review does not block technical construction. Every
   generated artifact remains `PROPOSED`; review-workflow design and
   authoritative activation occur only after the end-to-end solution is ready.

## 4. Deliverables

### Contracts

| Contract | Required purpose |
|---|---|
| `knowledge_document.json` | Authorized evidence metadata without embedding prohibited content |
| `knowledge_concept.json` | Versioned ontology concept with lifecycle, ownership, domain, and LOB |
| `ontology_relationship.json` | Typed, cardinality-aware relationship between governed concepts |
| `cots_structure_pattern.json` | Product/module/version-specific object and attribute recognition rule |
| `knowledge_pack_version.json` | Immutable pack identity, effective dates, approval, owner, and changelog |
| `cots_match_assessment.json` | Non-authoritative recognition result, extension assessment, provenance, confidence, and review routing |
| `knowledge_context.json` | Exact, bounded context assembled for one engagement and inference request |

Common provenance fields include `schema_version`, `pack_id`, `pack_version`,
`effective_from`, `effective_to`, `approval_state`, `owner_role`,
`evidence_references`, `created_at`, and a stable content fingerprint.

### Solution-owned tables

| Table | Producer boundary |
|---|---|
| `knowledge_document` | Approved evidence registry metadata only |
| `knowledge_concept` | Contract-valid ontology concepts |
| `ontology_relationship` | Contract-valid concept relationships |
| `cots_structure_pattern` | Exact product/module/version recognition patterns |
| `knowledge_pack_version` | Published immutable pack versions |
| `cots_match_assessment` | Run-scoped recommendations; never authoritative automatically |

The platform team provisions destinations. Workflow code may validate and
append solution-owned records but must not generate or execute provisioning
DDL.

### Reusable modules

All built modules live under `src/governed_knowledge_foundation/`, a package
separate from `src/source_intelligence/` — this work package's reusable code
is independently testable and imports nothing from the Source Intelligence
pilot; the reverse dependency (`knowledge_classifier.py` consuming
`knowledge_pack_io.py`) is the only link between the two.

| Module | Responsibility | Status |
|---|---|---|
| `knowledge_pack_io.py` | Load standalone and federated governed knowledge packs (rule packs, ontology) with fail-closed validation and fingerprinting | Built |
| `knowledge_registry.py` | Validate pack identity, approval, effective dates, and immutable versions | Built |
| `knowledge_contract_validation.py` | Cross-field and backward-compatibility validation for the seven Governed Knowledge Foundation contracts | Built |
| `ontology.py` | Resolve concepts and relationships without source-specific assumptions | Built |
| `cots_patterns.py` (implements the planned `cots_recognition.py` responsibility) | Score exact structured patterns and classify match/extension/unresolved outcomes | Built |
| `knowledge_context.py` | Assemble exact-filtered, minimized, provenance-complete context | Not built — depends on `CONTEXT-ASSEMBLY` (deferred) |
| `knowledge_lifecycle.py` | Enforce lifecycle transitions and mandatory review | Not built — depends on `REVIEW-WORKFLOW-DESIGN` (deferred) |

Names may adapt to an equivalent existing module, but responsibilities must
remain separate and independently testable.

## 5. Work breakdown

| ID | Work package | Owner | Depends on | Exit evidence |
|---|---|---|---|---|
| `BASELINE-AUTHORIZATION` | Baseline and evidence authorization (`COMPLETE FOR DEVELOPMENT`) | Data Architect + Privacy Steward | Source Intelligence gate | Baseline record and permitted-evidence register |
| `KNOWLEDGE-CONTRACTS` | Contract foundation (`COMPLETE`) | Data Architect | `BASELINE-AUTHORIZATION` | Seven schemas with positive, negative, and compatibility tests |
| `ONTOLOGY-NORMALIZATION` | Initial ontology normalization (`COMPLETE`) | Domain Steward | `KNOWLEDGE-CONTRACTS` | Scoped concepts and relationships validate with unique IDs |
| `PACK-AUTHORING` | Versioned knowledge-pack authoring (`COMPLETE`) | Domain Steward + Data Architect | `KNOWLEDGE-CONTRACTS`, `ONTOLOGY-NORMALIZATION` | Immutable Policy Admin, Claims Management, and Billing packs for `cots_like_suite/1.0.0` |
| `KNOWLEDGE-PUBLICATION` | Knowledge-table producers | Platform Engineer | `PACK-AUTHORING` | Idempotent contract-valid persistence into pre-provisioned outputs |
| `COTS-RECOGNITION` | Deterministic COTS recognition | Data Architect | `PACK-AUTHORING` | Known, extension, mismatch, and ambiguity outcomes with provenance |
| `CONTEXT-ASSEMBLY` | Governed context assembly | Privacy Steward | `PACK-AUTHORING`, `COTS-RECOGNITION` | Exact-filter context; unauthorized/cross-version content rejected |
| `REVIEW-WORKFLOW-DESIGN` | Human-review workflow design (`DEFERRED`) | Domain Steward | End-to-end technical solution | Review design covering all proposed outputs |
| `KNOWLEDGE-INTEGRATION` | Workflow integration and validation | Platform Engineer + Evaluation Owner | `KNOWLEDGE-PUBLICATION`–`CONTEXT-ASSEMBLY` | Local suite, Databricks run, contracts, and retry evidence pass |
| `AUTHORITATIVE-GATE` | Human acceptance and Governed Knowledge Foundation authoritative gate (`DEFERRED`) | Sponsor | `REVIEW-WORKFLOW-DESIGN`, `KNOWLEDGE-INTEGRATION` | Pack approvals, reviewer evidence, and machine-readable gate record |

## 6. Task details

### BASELINE-AUTHORIZATION — Baseline and authorized evidence

- Register separate `cots_like_suite / 1.0.0` development baselines for
  `policy_admin`, `claims_mgmt`, and `billing`.
- Record source classification, authorization basis, retention class,
  prompt/retrieval eligibility, owner, reviewer, and content fingerprint.
- Reject proprietary documents and raw document bodies before persistence.
- Define the controlled substitution process for a future licensed baseline.

**Acceptance:** the three module baselines are active for development; zero
real-vendor claims or prohibited documents exist; all evidence records have an
owner and approval state; one inference context cannot mix module scopes.

### KNOWLEDGE-CONTRACTS — Contracts

- Use JSON Schema Draft 2020-12 and shared definitions from `common.json`.
- Require exact pack and evidence provenance on concepts, patterns, contexts,
  and match assessments.
- Require `PROPOSED` approval state on generated match assessments.
- Detect breaking compatibility and invalid lifecycle states.

**Acceptance:** valid fixtures pass; missing version/evidence/approval fields,
cross-version records, invalid lifecycle values, and unauthorized documents
fail for the intended reason.

**Execution evidence:** seven Draft 2020-12 contracts, shared provenance and
scope definitions, cross-field version-isolation validation, and compatibility
checks pass in `tests/unit/test_knowledge_foundation_contracts.py`.

### ONTOLOGY-NORMALIZATION — Ontology

- Reconcile the existing `pnc_ontology` IDs with the bounded knowledge scope.
- Separate concepts from relationships instead of relying only on nested
  relationship arrays.
- Preserve definitions, synonyms, physical variants, concept type, privacy,
  temporality, LOB applicability, owner, and lifecycle state.
- Treat missing mappings as `Unresolved`, never as a default concept.

**Acceptance:** IDs are unique; every relationship endpoint resolves; lifecycle
states are valid; out-of-scope concepts cannot enter assembled context.

**Execution evidence:** domain-driven normalization emits 124 concepts and 167
relationships with unique stable IDs and resolved endpoints across ten
readable modules. The bundle includes 15 controlled vocabularies and 10 logical
reference shapes. Explicit domain subsets remain supported and report cross-
boundary relationships as exclusions. The active canonical bundle is rooted
at `knowledge_packs/ontology/insurance_ontology_v1.yaml` with fingerprint
`ceb57a00b1798a2bad273780c776157bdc0626e6457745867e229b4089e8a87d`.
Tests reject missing, duplicate-domain, cross-domain, path-escaping, and cross-
version modules, unresolved shape references, and module-content drift.

### PACK-AUTHORING — Pack authoring and publication

- Convert the existing synthetic reference into explicit object-pattern and
  attribute-pattern records with stable pattern IDs.
- Attach exact product, module, version, concept, evidence reference, expected
  physical family, required/optional status, and expected confidence evidence.
- Publish an immutable pack-version record and manifest entry.
- A new effective version creates a new pack; it never mutates history.

**Acceptance:** every pattern points to an existing concept and authorized
evidence; the manifest and pack content versions agree.

**Execution evidence:** three immutable module packs contain 52 contract-valid
patterns and six extension markers: `cots_like_policy_admin / 1.0.0` (20),
`cots_like_claims_mgmt / 1.0.0` (20), and `cots_like_billing / 1.0.0` (12).
The Policy pack retains two historical exclusions from its original authorized
scope; Claims and Billing cover every source mapping. Every concept-bearing
pattern resolves to the governed ontology and every record cites authorized
synthetic evidence. Manifest fingerprints are
`7b1ccb9731fd4e7e200a9b9e1041ec2f5ea938318149324b91f38117eef5022f`,
`875c9d7519053e9d21539a88d97ec77b17d58acff77a62575c2cc1dc77feea04`,
and `09dd58d5669db9f16fe5e40e22c6ff4470f1875729a6021703c7d94a3b0e2769`.
Focused pack-authoring coverage passed 47/47, expanded ontology and product-
area coverage passed 103/103, and the current full local suite passed 226/226,
including module-evidence isolation checks.

### KNOWLEDGE-PUBLICATION — Knowledge-table producers

- Add human-operated or controlled workflow entry points under `src/workflows/`
  for validated publication of repository-approved packs.
- Keep reusable validation and serialization in `src/` modules.
- Append idempotently by stable identity and version.
- Stop on incompatible existing table schemas; do not enable uncontrolled
  schema merging.

**Acceptance:** repeated publication creates no duplicates; invalid records are
rejected before writes; no source/Bronze object is mutated.

### COTS-RECOGNITION — Recognition

- Compare observed source objects and attributes with only the selected pack.
- Score transparent evidence: object-name match, required-attribute coverage,
  type compatibility, relationship shape, and known extension markers.
- Return `MATCHED`, `LIKELY_CUSTOM_EXTENSION`, or `UNRESOLVED`.
- Keep deterministic confidence separate from approval.

**Acceptance:** all outcomes include exact pattern and pack provenance; unknown
patterns cannot be coerced into the nearest concept.

### CONTEXT-ASSEMBLY — Context assembly

- Require engagement, product, module, version, domain, LOB, effective date,
  and approval state as explicit inputs.
- Select only `APPROVED` pack records valid for the requested effective date.
- Fail closed for no pack, multiple equal-precedence packs, version conflicts,
  expired evidence, disallowed retention, or disallowed prompt eligibility.
- Return minimized structured records, never raw documents.

**Acceptance:** version-isolation and authorization-negative tests pass; context
contains no unrelated product/module/version records.

### REVIEW-WORKFLOW-DESIGN — Human-review workflow design (deferred)

- Start only after the end-to-end technical solution is ready.
- Design one useful consolidated workflow across ontology, COTS recognition,
  extensions, privacy, and unresolved recommendations.
- Define lifecycle transitions, reviewer roles, rationale capture, rejection
  fingerprints, targeted invalidation, and operational review views.
- Keep `Candidate`, `Source extension`, and `Unresolved` non-authoritative.

**Acceptance:** the Sponsor accepts the review design; no lifecycle state
approves itself; invalid transitions fail; review events are append-only and
idempotent.

### KNOWLEDGE-INTEGRATION — Integration and validation

- Add the Governed Knowledge Foundation workflow after Source Intelligence without making the core
  source workflow depend on synthetic fixtures.
- Persist match assessments and exact knowledge versions in run evidence.
- Validate contracts before every write and capture controlled retry evidence.
- Keep AI Search and vector retrieval disabled in this package.

**Acceptance:** local and Databricks validation pass with no auto-approval,
prohibited evidence, duplicates, or cross-version contamination.

### AUTHORITATIVE-GATE — Human authoritative gate (deferred)

- Domain Steward approves ontology concepts and definitions.
- Data Architect approves COTS patterns and extension classifications.
- Privacy Steward approves evidence authorization and context policy.
- Evaluation Owner confirms the recognition test set and results.
- Sponsor records the Governed Knowledge Foundation gate decision.

**Acceptance:** all required decisions have non-PII reviewer identifiers,
rationales, dates, and evidence references. No automated process marks the gate
passed.

## 7. Test matrix

| Scenario | Expected result |
|---|---|
| Exact known object and required attributes in each module | `MATCHED` with exact module pack and pattern IDs |
| Known object plus `_ext` attribute | `LIKELY_CUSTOM_EXTENSION`; extension remains proposed |
| Same names under a different version | `UNRESOLVED`; no cross-version fallback |
| Unknown object or opaque field | `UNRESOLVED` with open question |
| Ambiguous patterns at equal precedence | `UNRESOLVED` with contradiction |
| Pattern references missing concept | Contract/publication failure |
| Unapproved or expired knowledge pack | Context assembly rejection |
| Proprietary or disallowed evidence class | Rejected before retention or retrieval |
| Repeated publication/run | No duplicate pack or assessment records |
| Generated match with high confidence | Still `PROPOSED`; human review remains required |

Minimum test layers:

- contract parse, reference, negative, and compatibility tests;
- ontology and pack integrity tests;
- recognition and version-isolation unit tests;
- context-authorization and leakage tests;
- lifecycle and review-routing tests;
- persistence idempotency tests;
- one in-workspace synthetic runtime validation.

## 8. Evidence package

Create the following only when execution produces real evidence:

- `docs/evidence/governed_knowledge_local_gate.json`;
- `docs/evidence/GOVERNED_KNOWLEDGE_COMPLETION_STATUS.md`;
- Databricks run and task identifiers;
- pack manifest and content fingerprints;
- counts of concepts, relationships, patterns, matched structures, extensions,
  unresolved structures, review items, and policy violations;
- reviewer decisions and unresolved issues.

Do not mark Governed Knowledge Foundation complete from unit tests alone.

## 9. Definition of done

Governed Knowledge Foundation is complete only when:

1. The five knowledge tables and match-assessment output have contract-valid,
   idempotent producers against pre-provisioned solution destinations.
2. Every COTS match records product, module, version, pack ID, pack version,
   pattern ID, and authorized evidence references.
3. The selected baseline recognizes known synthetic structures with expected
   concepts and relationships.
4. Likely extensions are visibly distinct from standard concepts.
5. Cross-version, unsupported, ambiguous, and unauthorized cases remain
   unresolved or rejected, never guessed.
6. Lifecycle states are enforced and all material recommendations reach the
   correct human reviewer.
7. Local tests, Databricks runtime checks, idempotency checks, and leakage
   checks pass.
8. Domain, architecture, privacy, evaluation, and Sponsor approvals are
   recorded with rationales.

Completion does not authorize target-model deployment. It only makes the
approved knowledge context eligible for target-model recommendation agents.

## 10. Execution order

```text
BASELINE-AUTHORIZATION baseline/evidence (complete for development)
  -> KNOWLEDGE-CONTRACTS contracts
  -> ONTOLOGY-NORMALIZATION ontology
  -> PACK-AUTHORING pack authoring (complete)
  -> KNOWLEDGE-PUBLICATION persistence
  -> COTS-RECOGNITION recognition
  -> CONTEXT-ASSEMBLY context assembly
  -> KNOWLEDGE-INTEGRATION integration/evidence

After the end-to-end technical solution is ready:
  REVIEW-WORKFLOW-DESIGN review-workflow design
    -> AUTHORITATIVE-GATE human authoritative gate
```

Execute one task group at a time and run its acceptance checks before starting
the next. Preserve unrelated working-tree changes and never substitute model
memory for missing authorized evidence.
