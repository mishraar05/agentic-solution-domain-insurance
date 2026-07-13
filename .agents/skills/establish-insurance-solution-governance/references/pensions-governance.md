# Pensions Governance Reference

Use this reference for pension and retirement-arrangement ontology work.
Pensions is adjacent to, but not part of, P&C insurance and must remain a
separate governed module.

## Scope dimensions

Record jurisdiction, scheme type, sponsor, administrator, member/account grain,
contribution basis, investment holdings, valuation date, benefit type,
beneficiary role, retirement event, and projection assumptions. Jurisdiction-
specific tax and regulatory concepts remain unresolved until explicitly scoped.

## Boundary decisions

- Party owns person and organization identity; Pensions owns member, employer,
  beneficiary, trustee, and administrator roles.
- Pensions owns schemes, accounts, contributions, holdings, valuations,
  benefits, and retirement events.
- Generic Billing concepts must not be reused for pension contributions or benefit payments.
- P&C Policy and Claims concepts must not be coerced onto pension arrangements.

## Evidence and mandatory review

Prohibit member names, dates of birth, tax identifiers, account values, health
details, beneficiary details, and free text unless separately authorized and
minimized. Require Pensions Domain Steward review for all scheme, contribution,
benefit, valuation, and projection semantics; Data Architect review for grain
and temporal relationships; Privacy Steward review for all member-level evidence.

## Evaluation coverage

Test defined-benefit and defined-contribution structures, employer/member
contributions, multiple holdings, beneficiary roles, retirement events,
ambiguous projections, unsupported jurisdiction-specific rules, privacy
routing, and version mismatch. All content remains `PROPOSED` pending a named
Pensions steward.
