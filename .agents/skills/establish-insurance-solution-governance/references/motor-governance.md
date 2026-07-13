# Motor Governance Reference

Use this reference for personal or commercial motor ontology and recommendation
work. It defines controls and ownership boundaries, not authoritative product
semantics.

## Scope dimensions

Record jurisdiction, personal/commercial segment, vehicle class, driver and
operator model, policy product/version, coverage basis, rating period, and
claim handling scope. Separate vehicle, driver, assignment, coverage, accident,
damage, liability, and discount grains.

## Boundary decisions

- Policy owns the contract and term; Motor owns vehicle/driver specializations.
- Party owns people and organizations; Motor owns driver and operator roles.
- Claims owns claim financials; Motor owns accident and vehicle-damage meaning.
- Billing owns invoices and receipts; Motor premium characteristics remain Policy evidence.

## Evidence and mandatory review

Use structural metadata and minimized profiles only. Treat VIN, registration,
driver identifiers, licence details, and garaging address as personal or
linkable evidence. Require Domain Steward review for coverage and vehicle-use
semantics, Data Architect review for vehicle/driver grain and relationships,
and Privacy Steward review for any value-level evidence.

## Evaluation coverage

Test personal and commercial motor, ambiguous vehicle/driver roles, multi-car
policies, coverage variants, unsupported telematics, privacy routing, and
source-version mismatch. All extensions remain `PROPOSED`.
