# Insurance Ontology Scope Record

**Version:** 1.0.0  
**Status:** PROPOSED  
**Effective date:** 2026-07-14  
**Owner roles:** Domain Steward and Data Architect  
**Required reviewers before authoritative use:** Policy, Claims, Billing,
Motor, Home, Commercial Property, and Pensions stewards; Privacy Steward

**Canonical pack:** `insurance_ontology / 1.0.0`  
**Bundle path:** `knowledge_packs/ontology/insurance_ontology_v1.yaml`  
**Bundle SHA-256:** `ceb57a00b1798a2bad273780c776157bdc0626e6457745867e229b4089e8a87d`

## Governed scope

The repository-authored synthetic ontology covers Policy, Claims, Billing,
Shared, Risk, and Document plus four separately governed product-area modules:

| Product area | Governed LOB values | Scope |
|---|---|---|
| Motor | `PERS_AUTO`, `COMM_AUTO`, `MOTORCYCLE_RV` | Vehicle, driver, assignments, coverages, accidents, damage, liability, discount, and garaging concepts |
| Home | `HOMEOWNERS`, `RENTERS_CONDO`, `DWELLING_FIRE` | Residential building, contents, occupancy, tenure, construction, coverage, valuable items, and alternative accommodation |
| Commercial Property | `COMM_PROPERTY`, `BOP` | Premises, buildings, occupancy, business activity, construction, property coverage, stock/equipment, valuation, and business interruption |
| Pensions | `PENSIONS` | Scheme, employer, member, account, contributions, holdings, valuations, benefits, beneficiaries, retirement events, and projections |

Pensions is not a P&C line. It is included as an isolated retirement domain so
its semantics, privacy rules, lifecycle, and stewardship cannot be confused
with P&C Policy, Claims, or Billing.

## Evidence decision

All authored content is `SYNTHETIC_GOVERNED_KNOWLEDGE`, created independently
for this repository. No external ontology definitions, examples, schemas,
vocabularies, or mappings are copied or retained here.

Permitted operations are version-controlled structured lookup, validation,
normalization, and recommendation context assembly. Raw client data, PII,
licensed COTS text, credentials, unrestricted retrieval, and automatic
authoritative promotion remain prohibited.

## Boundary and review decisions

- Stable existing P&C concept IDs are preserved.
- Product-area modules specialize or reference functional-domain concepts;
  they do not redefine those concepts.
- Controlled vocabularies and logical reference shapes are recommendation
  metadata, not executable target schemas.
- Every new concept and mapping remains `PROPOSED`.
- Pensions requires a named Pensions Domain Steward before authoritative use.
- Jurisdiction-specific regulatory, tax, and policy-form semantics remain
  unresolved until an authorized scope and evidence pack exist.

## Evaluation requirements

Each product area requires positive, ambiguous, unsupported, privacy, extension,
and version-mismatch cases. Metrics must be stratified by product area and
source version; passing one product area cannot be reported as coverage of
another.
