# Federated Insurance Ontology

`insurance_ontology_v1.yaml` is the active canonical root descriptor. It owns
the pack identity, version, status, shared enums, domain order, four product-
area declarations, and ordered module paths.

Concept definitions are maintained under `insurance_modules/`:

- Policy, Claims, and Billing contain functional transaction concepts;
- Shared contains reusable Party, Product, Coverage, Location, and asset concepts;
- Risk contains risk, peril, hazard, factor, occupancy, and business activity;
- Document contains metadata-only document classifications;
- Motor, Home, Commercial Property, and Pensions contain product-area concepts
  in `<domain>_concepts_v1.yaml`, with controlled vocabularies and logical
  reference shapes in a sibling `<domain>_vocabularies_v1.yaml`, registered
  in the root descriptor's `vocabulary_files:` list.

See `doc/ontology_principles.md` for why the ontology is shaped this way and
`doc/modelling_conventions.md` for concept, vocabulary, and example authoring
rules.

Pensions is an isolated retirement domain, not a P&C line. Its taxonomy and
governance are separate from the P&C LOB taxonomy. Logical reference shapes
are recommendation context and are never executable target schemas.

`insurance_modules/` is the only concept tree; there is no parallel JSON
ontology. The retired `pnc_ontology / 1.1.0` predecessor covered only Policy,
Claims, Billing, and Shared — every one of its concept IDs is preserved
unchanged inside the broader ontology (each superseding module's
`description:` notes the lineage), so no separate legacy file is kept on disk.

Every concept and vocabulary module repeats the root pack ID, version,
status, and domain. Consumers must load the root through
`governed_knowledge_foundation.knowledge_pack_io.load_federated_ontology` or
`load_knowledge_pack`. The registered SHA-256 fingerprint covers the root,
every ordered concept and vocabulary module path, and exact module bytes;
changing any module changes the bundle provenance.
