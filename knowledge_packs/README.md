# Knowledge Packs (Phase 3)

Versioned, governed knowledge consumed by agents through the context-engineering
layer. All packs are `PROPOSED` until the named owner role approves them.

- `ontology/` — standardized P&C ontology: Policy Administration, Claims Management, Billing, Shared (50 concepts). Concept IDs align with the Source Intelligence classifier.
- `cots_reference/` — vendor-NEUTRAL, synthetic COTS-like structures for recognition. No licensed Guidewire/Origami/Majesco content may ever be added to this repo; real vendor packs load only in a licensed customer environment (D-02).
- `lob_taxonomy/` — operational segment → LOB taxonomy (20 LOBs across Personal / Commercial / Specialty) with aliases, typical products/coverages, and NAIC line-name mappings; anchored to `Shared.LineOfBusiness`.
- `kpi_catalog/` — standard P&C analytical KPIs (22) with formulas, required ontology concepts, grain, and direction; guides Gold data-product completeness.
- `standards/`, `rules/` — enterprise modeling standards and business-rule corpus (pending).
- `manifest.json` — pack registry; its versions populate `knowledge_pack_versions` in run records.

Validated by `tests/unit/test_knowledge_packs.py`: JSON parses, IDs unique, KPI
and COTS concept references resolve against the ontology.
