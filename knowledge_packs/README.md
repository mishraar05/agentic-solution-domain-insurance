# Governed Knowledge Packs

Versioned, governed knowledge consumed by agents through the context-engineering
layer. All packs are `PROPOSED` until the named owner role approves them.

- `ontology/insurance_ontology_v1.yaml` — active federated insurance ontology with readable Policy, Claims, Billing, Shared, Risk, Document, Motor, Home, Commercial Property, and isolated Pensions modules (124 concepts, 167 relationships, 15 controlled vocabularies, and 10 logical reference shapes). The governed loader validates and fingerprints the complete ordered bundle. It is the sole ontology tree; the narrower `pnc_ontology / 1.1.0` predecessor (Policy, Claims, Billing, Shared only) has been retired, and every one of its stable concept IDs is preserved unchanged within this bundle.
- `cots_reference/` — vendor-NEUTRAL, synthetic COTS-like structures for recognition. No licensed Guidewire/Origami/Majesco content may ever be added to this repo; real vendor packs load only in a licensed customer environment (D-02).
- `lob_taxonomy/` — operational segment → LOB taxonomy (20 LOBs across Personal / Commercial / Specialty) with aliases, typical products/coverages, and NAIC line-name mappings; anchored to `Shared.LineOfBusiness`.
- `lob_taxonomy/pensions_taxonomy_v1.yaml` — separate retirement taxonomy; Pensions is not inserted into the P&C statutory taxonomy.
- `mapping_templates/` — recommendation-only source-field and authorized document-term mapping templates with closed candidates, provenance, and unresolved behavior.
- `kpi_catalog/` — standard P&C analytical KPIs (22) with formulas, required ontology concepts, grain, and direction; guides Gold data-product completeness.
- `rule_packs/` — versioned naming, privacy, and type inference rules consumed by `knowledge_classifier.py`, selected per source system/naming convention via `capability` and `priority`; supersede the embedded Python rules retired 2026-07-13 (see `docs/planning/RULES_LOG.md`).
- `standards/`, `rules/` — enterprise modeling standards and business-rule corpus (pending); distinct from `rule_packs/` above, which is the active inference-rule registry.
- `manifest.json` — pack registry; its versions populate `knowledge_pack_versions` in run records.
- `cots_reference/cots_like_reference_v1.json` — immutable vendor-neutral authoring evidence spanning synthetic product modules.
- `cots_reference/cots_like_policy_admin_v1.json` — contract-valid, exact-scope `cots_like_suite / policy_admin / 1.0.0` development pack with stable pattern IDs and authorized evidence provenance.
- `cots_reference/cots_like_claims_mgmt_v1.json` — contract-valid, exact-scope `cots_like_suite / claims_mgmt / 1.0.0` development pack.
- `cots_reference/cots_like_billing_v1.json` — contract-valid, exact-scope `cots_like_suite / billing / 1.0.0` development pack.

Validated by `tests/unit/test_knowledge_packs.py`: governed files parse, IDs unique, KPI
and COTS concept references resolve against the ontology.

The development baseline and its evidence eligibility are governed separately
in [`docs/governance/08_knowledge_baseline_evidence_authorization.md`](../docs/governance/08_knowledge_baseline_evidence_authorization.md).
The synthetic baseline is active only for non-authoritative development.
Human-review workflow design and authoritative activation are deferred until
the end-to-end solution is technically complete.
