# Governed Knowledge Authoring Rules

## Canonical sources

| Concern | Canonical source |
|---|---|
| Work order and acceptance | `docs/planning/GOVERNED_KNOWLEDGE_FOUNDATION_WORK_PACKAGE.md` |
| Evidence eligibility | `docs/governance/08_knowledge_baseline_evidence_authorization.json` |
| Record shapes | `contracts/knowledge_*.json`, `contracts/ontology_relationship.json`, `contracts/cots_*.json` |
| Cross-field invariants | `src/governed_knowledge_foundation/knowledge_contract_validation.py` |
| Canonical ontology source | Federated bundle rooted at `knowledge_packs/ontology/insurance_ontology_v1.yaml` |
| COTS-like source | `knowledge_packs/cots_reference/cots_like_reference_v1.json` |
| Registered versions | `knowledge_packs/manifest.json` |

## Ontology normalization

- Author common pack metadata, enums, domain order, and module references only
  in the canonical root YAML. Author concepts in the matching functional,
  shared, risk, document, or product-area module under
  `knowledge_packs/ontology/insurance_modules/`.
- Each module must repeat the root pack ID, version, status, and declared
  domain. A module cannot contain concepts owned by another domain.
- Load and fingerprint the complete ordered bundle through
  `knowledge_pack_io.py`; never fingerprint only the root descriptor.
- Do not maintain a parallel hand-edited JSON ontology; compatibility
  representations, if ever required, must be generated and verified from the
  canonical federated YAML bundle.
- Preserve stable `concept_id` values; do not rename IDs to improve aesthetics.
- Emit concepts and relationships as separate records.
- Select concepts by governed domain, never by a hardcoded concept-ID list.
  The synthetic development baseline includes Policy, Claims, Billing, Shared,
  Risk, Document, Motor, Home, Commercial Property, and an isolated Pensions
  domain. Pensions must never be presented as a P&C line.
- Map source `name` to `concept_name`; retain definitions, synonyms, physical
  variants, concept type, lifecycle, privacy, temporality, LOB, and steward
  notes when their contracts permit them.
- Map privacy values explicitly: `NONE` to `INTERNAL`, `INDIRECT` and `DIRECT`
  to `PERSONAL_DATA`, and `SENSITIVE` to `SENSITIVE`.
- Convert each nested source relationship into one stable relationship record.
  Reject missing endpoints; never synthesize the missing concept.
- Keep unsupported relationship semantics unresolved until a governed mapping
  exists.

## Pack and context isolation

- Use one scope tuple per pack: product, module, product version, domain, and
  LOB. A suite may register multiple module packs, but one inference context
  must never mix their scope tuples.
- Treat `pack_id` and `pack_version` as immutable identity, not descriptive text.
- Match item scope and pack identity exactly to the selected context.
- Reject not-yet-effective, expired, ambiguous, or mixed-version items.
- Development contexts may use `PROPOSED` synthetic knowledge; authoritative
  contexts require `APPROVED` knowledge and the deferred human-review gate.

## Template policy

Use the seven JSON contracts as executable record templates. Do not maintain a
parallel set of hand-authored JSON skeletons. Add a bundled asset only if
`PACK-AUTHORING` reveals a repeated multi-record authoring bundle that the
contracts cannot represent without duplication.
