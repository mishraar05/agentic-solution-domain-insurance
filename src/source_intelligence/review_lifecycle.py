"""Create governed human decisions and preserve rejection history.

Decision creation verifies that a queue item is open, the acting role matches
the routed reviewer role, the decision is permitted, and rationale is present.
Modified decisions must describe targeted invalidation. A stable fingerprint
of material recommendation content allows later runs to suppress an unchanged
recommendation that a human previously rejected, while still permitting a
meaningfully changed proposal to return for review.
"""

import hashlib
import json


VALID_DECISIONS = {"APPROVED", "MODIFIED", "REJECTED", "DEFERRED"}
RECOMMENDATION_FIELDS = (
    "source_table",
    "source_column",
    "proposed_business_name",
    "domain",
    "ontology_concept_id",
    "key_role",
    "privacy_class",
)


def recommendation_fingerprint(recommendation):
    """Hash only material recommendation content, never reviewer metadata."""
    payload = {
        field: recommendation.get(field)
        for field in RECOMMENDATION_FIELDS
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _recommendation_type(review_trigger):
    return {
        "PRIVACY": "PRIVACY",
        "KEY_CANDIDATE": "KEY_ROLE",
        "RELATIONSHIP": "RELATIONSHIP",
        "CONTRADICTION": "SEMANTIC_MAPPING",
        "UNMAPPED_CONCEPT": "ONTOLOGY",
        "LOW_EVIDENCE_COVERAGE": "SEMANTIC_MAPPING",
        "LOW_CONFIDENCE": "SEMANTIC_MAPPING",
    }[review_trigger]


def create_review_decision(
    queue_item,
    reviewer_role,
    reviewer_decision,
    reviewer_rationale,
    decided_at,
    invalidation_impact=None,
):
    """Close one open queue item with a role-authorized human decision."""
    if queue_item.get("queue_status") != "OPEN":
        raise ValueError("Only an OPEN queue item can receive a decision.")
    if reviewer_role != queue_item.get("recommended_reviewer_role"):
        raise ValueError("Reviewer role does not match the routed role.")
    if reviewer_decision not in VALID_DECISIONS:
        raise ValueError(f"Unsupported reviewer decision: {reviewer_decision}")
    if not reviewer_rationale or not reviewer_rationale.strip():
        raise ValueError("Reviewer rationale is mandatory.")
    if reviewer_decision == "MODIFIED" and not invalidation_impact:
        raise ValueError("Modified decisions must describe targeted invalidation.")

    queue_item_id = queue_item["queue_item_id"]
    fingerprint = recommendation_fingerprint(queue_item)
    return {
        "decision_id": f"decision:{queue_item_id}:{fingerprint[:12]}",
        "queue_item_id": queue_item_id,
        "schema_version": queue_item["schema_version"],
        "run_id": queue_item["run_id"],
        "artifact_version": queue_item["artifact_version"],
        "source_table": queue_item["source_table"],
        "source_column": queue_item["source_column"],
        "recommendation_type": _recommendation_type(
            queue_item["review_trigger"]
        ),
        "review_reason": queue_item["review_reason"],
        "recommended_reviewer_role": queue_item["recommended_reviewer_role"],
        "reviewer_role": reviewer_role,
        "reviewer_decision": reviewer_decision,
        "reviewer_rationale": reviewer_rationale.strip(),
        "prior_recommendation_version": queue_item["artifact_version"],
        "recommendation_fingerprint": fingerprint,
        "invalidation_impact": invalidation_impact,
        "queue_status": "CLOSED",
        "decided_at": decided_at,
        "queued_at": queue_item["queued_at"],
    }


def should_suppress_unchanged(recommendation, prior_decisions):
    """Return True when an identical recommendation was previously rejected."""
    fingerprint = recommendation_fingerprint(recommendation)
    return any(
        decision.get("reviewer_decision") == "REJECTED"
        and decision.get("recommendation_fingerprint") == fingerprint
        for decision in prior_decisions
    )
