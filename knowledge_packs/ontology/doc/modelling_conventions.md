# Modelling Conventions

Conventions for authoring or extending `knowledge_packs/ontology/`. See
`ontology_principles.md` for the reasoning behind these rules.

## Concept IDs

- Format: `Domain.ConceptName` (e.g. `Policy.Policy`, `Motor.Driver`,
  `CommercialProperty.BusinessInterruptionCoverage`). `Domain` must exactly
  match one entry in the root descriptor's `domains:` list and the
  concept's own `domain:` field — `load_federated_ontology` rejects a
  module containing a concept whose `domain` doesn't match the declared
  module domain.
- `ConceptName` is PascalCase, singular, business-meaningful — not a table
  or column name (that belongs in `physical_name_variants:`).
- IDs are stable once published. `insurance_modules/*.yaml` preserve every
  ID inherited from the retired `pnc_ontology/1.1.0` pack unchanged; do not
  rename an existing ID to "clean it up" — add a new concept instead if the
  meaning has actually changed.

## Required concept fields

Every entry under `concepts:` needs, at minimum:

```yaml
- concept_id: Domain.ConceptName
  name: Human Readable Name
  domain: Domain
  definition: One clear sentence of business meaning, not a repeat of the name.
  synonyms: [alternate business term, ...]
  physical_name_variants: [snake_case_column_guess, ...]
  relationships:
  - type: is_a | has_many | references | belongs_to | describes | identifies | measures | derives_from | precedes | reduces | groups
    target: Domain.OtherConceptId
  lifecycle_state: Standard | Specialized
  concept_type: ENTITY | ATTRIBUTE | MEASURE | STATUS | DATE | CODE | EVENT
  lob_applicability: ALL | [LOB_ID, ...]
  privacy_sensitivity: NONE | INDIRECT | DIRECT
  temporality: STATIC | SCD2 | EVENT | SNAPSHOT
```

`relationships.type` must be one of the keys in
`source_intelligence/ontology.py::RELATIONSHIP_RULES` — an unrecognized type
fails normalization, not just loading. Relationship `target` must resolve to
a real `concept_id` somewhere in the bundle (checked by
`load_federated_ontology` and again by `normalize_governed_ontology`).

## Privacy sensitivity governs what examples may show

`privacy_sensitivity` is not decorative — it is the boundary between what a
synthetic example (`examples/ontology/*_example_v1.yaml`) may populate with
a concrete illustrative value versus what must stay an opaque
`SYNTHETIC_<NAME>_<NNN>` reference token:

- `NONE` / `INDIRECT` — a concrete, clearly-synthetic sample value is fine
  (vehicle make, cover basis, construction type, no-claims years, scheme
  type). These never resolve to a real individual on their own.
- `DIRECT` — identity- or account-level concepts (`Shared.Party` in an
  insured/driver role, `Pensions.Member`, `Pensions.Account`, ...). Examples
  must not fabricate a name, DOB, address, or account value for these — use
  a `SYNTHETIC_*` token only, exactly as the existing Pensions example does.

This is stricter than illustrative examples in comparable public ontologies,
which commonly populate a realistic-looking name and date of birth. That
style is deliberately not used here; see `ontology_principles.md` §6.

## Controlled vocabularies and reference shapes

Domains that need governed value lists or a "what's typically attached to
this concept" shape declare a sibling `*_vocabularies_v1.yaml` file (e.g.
`motor_concepts_v1.yaml` + `motor_vocabularies_v1.yaml`), registered in the
root descriptor's `vocabulary_files:` list alongside `module_files:`. Six
domains have one today (Motor, Home, CommercialProperty, Pensions, Risk,
Document); Policy, Claims, Billing, and Shared currently have none — only
add a vocabulary file when a domain actually needs one, don't create an
empty placeholder.

```yaml
# insurance_modules/<domain>_vocabularies_v1.yaml
schema_version: 1.0.0
pack_id: insurance_ontology
pack_version: 1.0.0
status: PROPOSED
domain: <Domain>          # must match the vocabulary_files declaration
description: ...
controlled_vocabularies:
- vocabulary_id: <DOMAIN>_<NAME>       # unique across the whole bundle
  name: Human Readable Name
  values: [ENUM_VALUE, ...]
  steward_note: Why this list is scoped the way it is, or what's out of scope.
reference_shapes:
- shape_id: <DOMAIN>_<NAME>_SHAPE      # unique across the whole bundle
  root_concept_id: Domain.ConceptId
  required_concept_ids: [Domain.ConceptId, ...]
  optional_concept_ids: [Domain.ConceptId, ...]
```

Every `root_concept_id`/`required_concept_ids`/`optional_concept_ids` entry
must resolve to a real concept in the bundle — checked at load time.

## File and naming conventions

- Module files: `insurance_modules/<domain>_concepts_v1.yaml` (concepts) and
  `insurance_modules/<domain>_vocabularies_v1.yaml` (vocabularies/shapes,
  where present). Lowercase snake_case domain name matching the product
  area, `_v1` suffix bumps only on a breaking structural change — additive
  concept/vocabulary growth stays on the same file version.
- `pack_id`, `pack_version`, and `status` must be identical across the root
  descriptor and every concept/vocabulary module — `load_federated_ontology`
  rejects any module that doesn't repeat them exactly.
- Synthetic example files: `examples/ontology/<product_area>_example_v1.yaml`,
  lowercase snake_case product area matching `product_area:` in the file.

## Before adding or changing a concept

1. Does this meaning already exist under a different name? Check
   `synonyms:`/`physical_name_variants:` across the domain first.
2. Is it truly product-specific, or should it live in `Shared`, `Risk`, or
   `Document` so every product can reference it?
3. Does every relationship target resolve, and does the relationship type
   exist in `RELATIONSHIP_RULES`?
4. Is `privacy_sensitivity` set to the most restrictive value that's
   actually true, not the most convenient one?
5. Does the change need a controlled vocabulary or reference shape, and if
   so does the owning domain already have a `*_vocabularies_v1.yaml` file to
   add it to?
6. Does an example need a new `sample_instance` entry, or does an existing
   one now reference a renamed/removed concept?
