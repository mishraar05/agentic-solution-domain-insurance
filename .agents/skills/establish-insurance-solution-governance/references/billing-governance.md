# Billing Governance Reference

Use this reference only when Billing is within the governed scope. It defines
review questions and boundary controls, not authoritative ontology semantics.

## Scope dimensions

Record the applicable line of business, jurisdiction, billing model, source
product/module/version, accounting boundary, and included billing objects.
Make explicit whether the scope includes account, payment plan, invoice,
installment, charge, payment, disbursement, delinquency, and balance structures.

## Boundary decisions

- Treat policy, insured, payer, and producer identifiers as governed cross-domain references.
- Keep premium semantics owned by Policy while Billing owns invoices, installments, receivables, payments, and disbursements.
- Separate claim payments and recoveries from policyholder billing transactions.
- Distinguish account, invoice, installment, charge, payment, disbursement, and balance grain.
- Record source-specific extensions separately from standard Billing concepts.

## Evidence and review controls

- Minimize payer identity, payment method, bank, address, collection, and delinquency evidence.
- Prohibit credentials, full account numbers, payment tokens, and unmasked financial identifiers.
- Require Privacy Steward review for sensitive or value-level billing evidence.
- Require Domain Steward review for invoice status, payment allocation, delinquency, balance, and payment-plan semantics.
- Require Data Architect review for account/policy links, financial grain, transaction relationships, and source extensions.
- Require explicit provenance for product/module/version recognition.

## Evaluation coverage

Include positive, ambiguous, contradictory, and unresolved examples across
accounts, invoices, installments, charges, payments, disbursements,
delinquencies, balances, and cross-domain references. Test financial-review
routing separately from semantic accuracy and stratify results by source version.

## Completion evidence

Record the approved scope and exclusions, evidence policy, accountable Billing
steward, cross-domain owners, financial-review rules, labelled-set coverage,
and unresolved concepts.
