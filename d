---
name: define-insurance-pilot-governance
description: Create and maintain the governed pilot-inception artifacts for the agentic insurance domain solution. Use when selecting the Policy or Claims pilot boundary, defining permitted evidence, assigning architect/domain/privacy reviewers, setting confidence and mandatory-review rules, defining reviewer service levels, establishing a labelled evaluation set or pilot scorecard, and checking the Phase 0 governance gate before Source Intelligence development.
---

# Define Insurance Pilot Governance

Turn unresolved pilot choices into version-controlled decision records without inventing approvals.

## Establish context

1. Discover and work from the repository root.
2. Read `docs/planning/IMPLEMENTATION_PLAN.md`, `docs/evidence/MVP_RUN_EVIDENCE.md`, and existing governance artifacts.
3. Confirm Phase 1 evidence remains complete and the working tree is understood.
4. Reuse existing document conventions; place new records under `docs/governance/`.

## Create the governance package

Create concise, separately reviewable artifacts covering:

1. **Pilot scope:** source family, product, module, version, domain, line of business, included objects, excluded objects, and rationale.
2. **Evidence classification:** evidence class, permitted operations, retention, prompt/retrieval eligibility, minimization, reviewer, and prohibition rationale.
3. **Reviewer model:** data architect, domain steward, privacy steward, accountable owner, backup, decision rights, and turnaround target. Use role placeholders until people approve assignments.
4. **Confidence policy:** component signals, threshold bands, mandatory-review triggers, and prohibition on LLM self-rating.
5. **Evaluation plan:** labelled examples, reviewer-decision capture, precision/recall, override rate, throughput, reliability, cost/latency, and sensitive-evidence compliance.
6. **Go/no-go scorecard:** metric, baseline, target, evidence source, owner, status, and decision rule.

Use `PROPOSED`, `APPROVED`, `MODIFIED`, `REJECTED`, or `DEFERRED` consistently. Record decision date, version, owner, reviewer, rationale, and open questions. Never mark an item approved without explicit human evidence.

## Enforce non-negotiable boundaries

- Permit synthetic data and approved public learning material only in Free Edition.
- Prohibit client data, PII, claims narratives, proprietary COTS material, secrets, and production connection strings.
- Keep the system recommendation-only and read-only toward source systems.
- Require review for privacy, relationships, keys, target grain, financial measures, low confidence, contradictions, and ontology extensions.
- Reject disallowed evidence before profiling, indexing, retention, or prompt construction.

## Validate the gate

Treat the governance gate as passed only when:

- one pilot scope and its exclusions are explicit;
- every evidence class has a permitted/prohibited decision;
- all three reviewer roles and decision rights are defined;
- threshold and mandatory-review rules are testable;
- evaluation metrics and evidence sources are named;
- unresolved items have an owner and do not masquerade as approval.

Report created files, decisions still awaiting humans, validation performed, and whether Phase 2 may begin.