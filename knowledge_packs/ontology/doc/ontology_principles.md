# Ontology Principles

## Purpose

`insurance_ontology` gives the Source Intelligence workflow one shared,
business-meaningful vocabulary for insurance and pensions concepts, so that
source-system structures, documents, and downstream data products can all be
mapped back to the same governed meaning instead of drifting into
system-specific terminology.

It exists to support:

1. business understanding of source structures
2. source-to-concept mapping recommendations (never automatic mapping)
3. governed vocabulary and reference-shape lookup during classification
4. normalization into contract-valid knowledge tables for downstream tooling
5. evaluation of recommendation quality against a stable concept catalogue

## Core principles

### 1. Business meaning first, physical variants second

Every concept (`insurance_modules/*_concepts_v1.yaml`) is defined by its
business `definition:`, with `physical_name_variants:` recorded as a hint
list, not the definition itself. A concept's meaning must not change if a
new source system stores it under a different column name.

### 2. Shared before specialized

Cross-domain concepts (Party, Product, Coverage, Location, and technical
metadata) live once in `Shared`, and functional-transaction concepts live
once in `Policy`, `Claims`, or `Billing`. Product modules (`Motor`, `Home`,
`CommercialProperty`, `Pensions`) specialize or reference those concepts via
`relationships: [{type: is_a, target: ...}]` — they do not redefine them.
`Motor.MotorCoverage` `is_a` `Shared.Coverage`; it never re-declares what
coverage means.

### 3. Federated, domain-sized modules

The ontology is authored as one root descriptor
(`insurance_ontology_v1.yaml`) plus one concept module per governed domain
under `insurance_modules/`, assembled at load time by
`governed_knowledge_foundation.knowledge_pack_io.load_federated_ontology`. This keeps
each file reviewable by its owning steward while still producing one
pack identity, one bundle fingerprint, and one set of cross-domain
uniqueness guarantees (concept IDs, vocabulary IDs, shape IDs) across the
whole bundle. Loading fails closed on a missing, duplicate, cross-domain, or
path-escaping module — there is no silent partial load.

### 4. Pensions is isolated, not a P&C line

Pensions is a retirement domain governed separately from the P&C statutory
LOB taxonomy (see `knowledge_packs/lob_taxonomy/pensions_taxonomy_v1.yaml`).
Its relationships are checked (`tests/unit/test_insurance_product_area_coverage.py::test_pensions_remains_isolated_from_pnc_transaction_domains`)
to never target `Policy.*`, `Claim.*`, `Billing.*`, `Motor.*`, or `Home.*`
concepts, so retirement and P&C semantics cannot be mixed by accident.

### 5. Vocabularies and reference shapes are recommendation metadata, not schemas

Each product module's `controlled_vocabularies:` (allowed value lists) and
`reference_shapes:` (a root concept plus its required/optional related
concepts — see `insurance_modules/motor_vocabularies_v1.yaml` for an
example) describe governed *recommendation* context for the classifier and
mapping-review workflow. They are deliberately **not** compiled into an
executable target schema (no JSON Schema `additionalProperties: false`,
no enforced payload shape). This is a considered divergence from a typical
ontology deliverable: this repository's Source Intelligence workflow only
ever produces `PROPOSED` recommendations for a human reviewer, and
`src/governed_knowledge_foundation/ontology.py` normalizes concepts and relationships
into contract-valid knowledge tables (`knowledge_concept.json`,
`ontology_relationship.json`) with explicit provenance — an executable
schema would imply an authority this ontology does not have until a human
approves a mapping.

### 6. Privacy sensitivity is a first-class field, not an afterthought

Every concept declares `privacy_sensitivity: NONE | INDIRECT | DIRECT`.
This drives two things directly: the `privacy_class` written into every
normalized knowledge-concept record (see `PRIVACY_CLASS_MAP` in
`src/governed_knowledge_foundation/ontology.py`), and what may appear as a concrete
value in a synthetic example (`examples/ontology/`) — only `NONE`/`INDIRECT`
concepts get populated sample values; `DIRECT` concepts stay as opaque
`SYNTHETIC_*` reference tokens. See `modelling_conventions.md` for the
authoring rule.

### 7. Explicit, typed relationships

Relationships are structured (`relationships: [{type: is_a, target: Domain.Concept}]`),
not free-text sentences. `governed_knowledge_foundation/ontology.py::RELATIONSHIP_RULES`
maps each `type` to a normalized relationship type and cardinality pair, so
every relationship in the ontology is mechanically checked to have both
endpoints resolve to a real concept before it can be normalized.

### 8. Every concept, vocabulary, and example stays `PROPOSED`

Nothing in this ontology auto-promotes to authoritative status. Product-area
scope, reviewer roles, and the path to authoritative use are governed
separately in `docs/governance/09_insurance_ontology_scope.md`.

## Relationship to other artifacts

- **Ontology** (`knowledge_packs/ontology/`) — defines concept meaning,
  relationships, controlled vocabularies, and reference shapes.
- **Normalized knowledge tables** (`src/governed_knowledge_foundation/ontology.py`) —
  mechanical, contract-valid restatement of the ontology as one record per
  concept and one per relationship, for downstream classifiers.
- **Mapping templates** (`knowledge_packs/mapping_templates/`) — the
  recommendation-only record shape used to propose a source field maps to a
  concept; a proposal is never generated code and never auto-approved.
- **Synthetic examples** (`examples/ontology/`) — illustrative, privacy-
  governed instances showing what populated concepts look like for each
  product area; never real or realistic personal data.
