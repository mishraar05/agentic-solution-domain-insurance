# Operational Readiness Reference

Use this reference when assessing controlled organizational-data use or a
production promotion decision. It creates review evidence; it never authorizes
promotion automatically.

## Required control areas

1. **Authorization:** named sponsor, data owner, domain owner, privacy owner, and explicit approval scope.
2. **Data protection:** classification, minimization, retention, deletion, residency, legal basis, and prohibited evidence.
3. **Access:** least-privilege identities, separation of duties, source read-only enforcement, secret management, and periodic access review.
4. **Model and retrieval:** approved endpoints, prompt/retrieval eligibility, model/version inventory, output validation, cost limits, and fallback behavior.
5. **Operations:** service objectives, monitoring, alerting, runbooks, support ownership, dependency health, and capacity assumptions.
6. **Change control:** versioned contracts, knowledge packs, prompts, rules, compatibility policy, rollback, and targeted downstream invalidation.
7. **Reliability:** retry and idempotency evidence, backup/recovery expectations, continuity plan, and failure-mode testing.
8. **Assurance:** security/privacy review, evaluation thresholds, reviewer override monitoring, audit retention, and periodic revalidation.
9. **Promotion:** signed decision, approved scope, effective date, conditions, exceptions, expiry/review date, and rollback authority.

## Fail-closed conditions

Do not recommend promotion when authorization is missing, source write access is
possible, prohibited evidence can enter prompts or persistence, material outputs
can bypass human review, versions are not traceable, rollback is undefined, or
monitoring cannot detect control failure.

## Required evidence package

Record each control, owner, status, evidence reference, reviewer, decision date,
exception, remediation, and next review date. Unmet controls remain `PROPOSED`,
`REJECTED`, or `DEFERRED`; readiness must not be inferred from successful tests
alone.
