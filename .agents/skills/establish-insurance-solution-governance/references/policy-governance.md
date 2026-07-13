# Policy Governance Reference

Use this reference only when Policy is within the governed scope. It defines
review questions and boundary controls, not authoritative ontology semantics.

## Scope dimensions

Record the applicable line of business, jurisdiction, product family, policy
lifecycle interval, source product/module/version, and included policy objects.
Make explicit whether the scope includes policy term/period, insured parties,
risks, coverages, limits, deductibles, premium, forms, and producer roles.

## Boundary decisions

- Assign Party ownership for people and organizations referenced by a policy.
- Assign Product ownership for reusable product definitions and eligibility rules.
- Separate policy premium recommendations from Billing transactions and balances.
- Treat a Claim link as a cross-domain relationship, not a Policy-owned claim record.
- Record source-specific extensions separately from standard Policy concepts.

## Evidence and review controls

- Minimize names, addresses, contact details, underwriting responses, and risk-location evidence.
- Require Privacy Steward review before any value-level evidence is permitted.
- Require Domain Steward review for policy status, transaction type, effective/expiration dates, cancellation or reinstatement meaning, and coverage semantics.
- Require Data Architect review for policy identifiers, term grain, party roles, coverage relationships, and source extensions.
- Require explicit provenance for product/module/version recognition.

## Evaluation coverage

Include positive, ambiguous, contradictory, and unresolved examples across
identifiers, dates, status, party roles, risk, coverage, limits, deductibles,
and premium. Stratify results by line of business and source version; do not
claim coverage for an untested combination.

## Completion evidence

Record the approved scope and exclusions, evidence policy, accountable Policy
steward, cross-domain owners, mandatory-review rules, labelled-set coverage,
and unresolved concepts.
