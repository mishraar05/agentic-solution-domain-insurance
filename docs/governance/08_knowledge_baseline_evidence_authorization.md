# Governed Knowledge Foundation Baseline and Evidence Authorization

**Artifact:** `08_knowledge_baseline_evidence_authorization`

**Version:** 1.0.0

**Work package:** `BASELINE-AUTHORIZATION`

**Decision date:** 2026-07-13

**Owner:** Sponsor

**Reviewer:** Deferred until the end-to-end solution is technically complete

**Status:** DEVELOPMENT BUILD COMPLETE; AUTHORITATIVE USE DEFERRED

Machine-readable record:
[`08_knowledge_baseline_evidence_authorization.json`](08_knowledge_baseline_evidence_authorization.json).

## Selected candidate

| Dimension | Value |
|---|---|
| Product | `cots_like_suite` |
| Modules | `policy_admin`, `claims_mgmt`, `billing` |
| Product version | `1.0.0` |
| Authored packs | `cots_like_policy_admin / 1.0.0`, `cots_like_claims_mgmt / 1.0.0`, `cots_like_billing / 1.0.0` |
| Authorized authoring source | `cots_like_reference / 1.0.0` |
| Domains | Policy, Claims, Billing, and Shared dependencies |
| LOB | Personal Lines |
| Classification | Vendor-neutral synthetic knowledge |
| Permitted claim | Synthetic COTS-like resemblance only |
| Authorization state | Active for non-authoritative development only |

This suite baseline tests the governed recognition mechanism without asserting that
the source is Guidewire, Majesco, Origami, or another real product. It contains
no licensed product documentation or client material.

## Authorized evidence proposal

| Evidence | Retention | Structured retrieval | Raw prompt use | Vector index | Owner | Reviewer |
|---|---|---|---|---|---|---|
| Repository-authored synthetic reference metadata | Version controlled | Permitted for development | Prohibited | Prohibited | Data Architect | Privacy Steward |

The retained evidence is the immutable structured authoring source and its
SHA-256 content fingerprint. The exact-scope authored pack has a separate
identity and fingerprint. Raw document bodies are neither required nor retained.

## Prohibited evidence

- Proprietary or licensed COTS documentation.
- Client or production schemas and data.
- PII values and claims narratives.
- Credentials and connection strings.
- Public material without documented authorization.

These classes must be rejected before retention, profiling, indexing,
retrieval, or prompt construction.

## Controlled substitution for a licensed baseline

A real product pack may replace a corresponding synthetic module pack only when all of the following
are recorded:

1. The customer environment is authorized to retain and use the material.
2. Product, module, and version are exact and independently reviewable.
3. Every retained document has an authorization decision and fingerprint.
4. The replacement has a new immutable pack identity and version.
5. The synthetic and licensed baselines are not mixed in one inference context.
6. Cross-version fallback remains prohibited.
7. Real-vendor identification is enabled only while that exact pack is active.

## Review sequencing decision

The Sponsor directed the team to build and validate the entire non-authoritative
solution before designing the human-review workflow. Intermediate human review
therefore does not block development work packages.

The baseline is development-active, but the pack and all generated artifacts
remain `PROPOSED`. They cannot become authoritative, be promoted automatically,
or identify a real vendor. Human-review workflow design and the required final
decisions are deferred until the end-to-end technical solution is ready.

## BASELINE-AUTHORIZATION acceptance status

| Check | Status |
|---|---|
| Exactly one baseline candidate selected | PASS |
| Content fingerprint recorded and reproducible | PASS |
| Source classification, retention, retrieval, and prompt eligibility recorded | PASS |
| Owner and reviewer roles recorded | PASS |
| Proprietary documents and raw document bodies excluded | PASS |
| Controlled licensed-pack substitution defined | PASS |
| Development sequencing decision recorded | PASS |
| Exactly one development baseline active | PASS |
| Automatic authoritative promotion prohibited | PASS |
| Human-review workflow design | DEFERRED |

BASELINE-AUTHORIZATION is complete for development and KNOWLEDGE-CONTRACTS is unlocked. Authoritative use
remains blocked until the deferred review design and final decisions exist.
