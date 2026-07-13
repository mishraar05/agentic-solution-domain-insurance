# Claims Governance Reference

Use this reference only when Claims is within the governed scope. It defines
review questions and boundary controls, not authoritative ontology semantics.

## Scope dimensions

Record the applicable line of business, jurisdiction, claim handling segment,
source product/module/version, financial scope, and included claim objects.
Make explicit whether the scope includes claim, loss event, exposure, claimant,
incident, reserve, payment, recovery, litigation, and subrogation structures.

## Boundary decisions

- Treat the related policy and coverage as governed cross-domain references.
- Assign Party ownership for claimants, insureds, witnesses, vendors, and legal entities while preserving Claims-specific roles.
- Separate claim financial recommendations from Billing receivables and disbursement operations.
- Distinguish claim, exposure, incident, reserve, payment, and recovery grain.
- Record source-specific extensions separately from standard Claims concepts.

## Evidence and review controls

- Prohibit claim narratives, medical details, legal notes, injury descriptions, and direct identifiers unless a separately approved policy explicitly permits minimized use.
- Require Privacy Steward review for any sensitive or value-level evidence.
- Require Domain Steward review for claim and exposure status, loss and report dates, cause/type classifications, party roles, and coverage applicability.
- Require Data Architect review for claim identifiers, policy/coverage links, financial grain, reserve/payment/recovery relationships, and source extensions.
- Require explicit provenance for product/module/version recognition.

## Evaluation coverage

Include positive, ambiguous, contradictory, and unresolved examples across
identifiers, dates, statuses, policy links, parties, incidents, exposures,
reserves, payments, and recoveries. Test privacy routing independently from
semantic accuracy and stratify results by line of business and source version.

## Completion evidence

Record the approved scope and exclusions, evidence policy, accountable Claims
steward, cross-domain owners, financial-review rules, labelled-set coverage,
and unresolved concepts.
