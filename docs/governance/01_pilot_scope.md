# Pilot Scope Decision Record

**Artifact:** `01_pilot_scope.md`
**Version:** 1.0.0
**Decision Date:** 2026-07-13
**Owner:** `HUMAN_REVIEWER_01` (Data Architect)
**Reviewer:** `HUMAN_REVIEWER_01` (Sponsor)
**Status:** APPROVED

## Decision

**Pilot domain:** Policy (first-release scope)
**Alternative considered:** Claims (deferred to second release)

## Source family

| Attribute | Value |
|---|---|
| Source system | `synthetic_insurance_source` |
| Product | Personal Auto / Homeowners (synthetic) |
| Module | Policy Administration |
| Version | Synthetic v0.1.0 |
| Domain | P&C Insurance |
| Line of business | Personal Lines |

## Included objects

| Object | Purpose |
|---|---|
| `bronze_policy` | Policy source-aligned records (policy ID, status, dates, product, insured party) |
| `bronze_policyholder` | Party/policyholder records (party ID, type, display name, contact channel) |
| `bronze_claim` | Claims records - included for relationship inference only |

## Excluded objects

| Exclusion | Rationale |
|---|---|
| Billing / Payment tables | Not in synthetic MVP scope; deferred to Governed Knowledge Foundation and later capabilities |
| Coverage / Endorsement tables | Not yet synthesized; deferred |
| Underwriting / Rating tables | Not in scope for recommendation-only MVP |
| External source systems | The synthetic pilot does not use external sources |

## Rationale

Policy is selected as the first-release scope because:
1. Policy is the root entity in P&C insurance - Claims, Billing, and Coverage all depend on it.
2. The synthetic Bronze tables already contain policy, policyholder, and claim data with clear relationships.
3. Policy scope is bounded enough for a vertical slice while still exercising relationship inference, privacy classification, and review routing.
4. Claims is deferred because it adds loss-narrative complexity and privacy sensitivity.

## Open questions

- [ ] Who is the named data architect owner?
- [ ] Should Claims be included as a read-only relationship target for Source Intelligence?
- [ ] Are additional synthetic objects needed for Source Intelligence evaluation?

## Change log

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1.0 | 2026-07-12 | Initial proposed pilot scope | Agent (Cline) |
| 1.0.0 | 2026-07-13 | Approved unchanged for the governed pilot | `HUMAN_REVIEWER_01` |
