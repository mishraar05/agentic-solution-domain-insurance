---
name: establish-insurance-solution-governance
description: Establish and maintain scalable governance for the insurance recommendation solution across domains and operating contexts. Use when defining governed scope, permitted evidence, reviewer accountability, confidence and mandatory-review policy, evaluation controls, production-readiness criteria, or domain-specific governance for Policy, Claims, Billing, Party, Coverage, Product, or a newly added domain.
---

# Establish Insurance Solution Governance

Create version-controlled governance decisions without inventing approvals or
coupling the controls to one insurance domain.

## Establish context

1. Discover and work from the repository root.
2. Read `docs/planning/IMPLEMENTATION_PLAN.md`, relevant run evidence, and existing governance records.
3. Identify the requested domain, line of business, source family, product/module/version scope, and evidence classes. Document any unknown scope and flag it for future review.
4. Inspect the working tree and preserve unrelated changes.

## Load only relevant references

- For Policy work, read [references/policy-governance.md](references/policy-governance.md).
- For Claims work, read [references/claims-governance.md](references/claims-governance.md).
- For Billing work, read [references/billing-governance.md](references/billing-governance.md).
- For Motor work, read [references/motor-governance.md](references/motor-governance.md).
- For Home work, read [references/home-governance.md](references/home-governance.md).
- For Commercial Property work, read [references/commercial-property-governance.md](references/commercial-property-governance.md).
- For Pensions work, read [references/pensions-governance.md](references/pensions-governance.md).
- For production-readiness or controlled organizational-data decisions, read [references/operational-readiness.md](references/operational-readiness.md).
- For another domain, use [references/domain-governance-template.md](references/domain-governance-template.md) to create a peer reference before recording domain-specific decisions.
- For cross-domain work, load each affected domain reference and record boundary ownership explicitly.

## Create or update the governance package

Maintain separately reviewable records by creating these records in order:

1. **Governed scope record:** source family, product/module/version, domain, line of business, included objects, excluded objects, jurisdiction where relevant, and rationale.
2. **Evidence controls record:** classification, permitted operation, retention, prompt/retrieval eligibility, minimization, reviewer, and prohibition rationale.
3. **Accountability record:** data architect, domain steward, privacy steward, accountable owner, backup, decision rights, and service target.
4. **Trust policy record:** evidence components, threshold bands, contradictions, mandatory-review triggers, and prohibition on LLM self-rating.
5. **Evaluation controls record:** labelled examples, reviewer outcomes, precision/recall, override rate, throughput, reliability, cost/latency, and sensitive-evidence compliance.
6. **Promotion and operational controls record:** authorization evidence, access, retention, monitoring, change control, support, incident response, rollback, revalidation, and decision criteria.

Use `PROPOSED`, `APPROVED`, `MODIFIED`, `REJECTED`, or `DEFERRED`
consistently. Record version, effective date, owner, reviewer, rationale,
superseded decision, and open questions. Never mark an item approved without
explicit human evidence.

## Enforce non-negotiable boundaries

- Use synthetic data and approved public learning material in this repository.
- Never add client data, PII, claims narratives, proprietary COTS material, secrets, connection strings, or licensed source extracts.
- Keep the system recommendation-only and read-only toward source systems.
- Require review for privacy, relationships, keys, target grain, financial measures, low confidence, contradictions, and ontology extensions.
- Reject disallowed evidence before profiling, indexing, retention, retrieval, or prompt construction.
- Treat an operational-readiness design as evidence for a human promotion decision, never as automatic authorization.

## Validate governance coverage

Treat the requested governance scope as complete only when:

- its boundaries, exclusions, domain reference, and accountable owner are explicit;
- every evidence class has a permitted or prohibited decision;
- reviewer roles and decision rights are defined;
- trust thresholds and mandatory-review rules are testable;
- evaluation and operational evidence sources are named;
- unresolved items have owners and do not masquerade as approval;
- any promotion decision cites explicit human authorization.

Report changed records, applicable domain references, validation performed,
unresolved decisions, and the next governed gate.
