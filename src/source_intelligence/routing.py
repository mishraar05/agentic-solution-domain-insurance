"""Route one recommendation to one coherent human-review decision.

Routing evaluates mandatory governance triggers in priority order and returns
the trigger, reason, reviewer role, and priority together so those fields cannot
drift apart. Privacy, key, relationship, contradiction, unmapped-concept,
evidence-coverage, and confidence conditions are handled explicitly. Primary-
and foreign-key candidates always reach the Data Architect regardless of their
confidence score, and no routing result grants approval.
"""

LOW_CONFIDENCE_THRESHOLD = 0.75


def route_review(confidence_score, evidence_coverage, privacy_class,
                 relationship_evidence, ontology_concept_id, key_role,
                 contradictions, evidence_coverage_floor=0.60,
                 low_confidence_threshold=LOW_CONFIDENCE_THRESHOLD):
    """Return one atomic routing decision.

    Precedence: privacy > key candidate > relationship > contradictions >
    missing ontology concept > evidence coverage > low confidence.
    """
    decision = None
    if privacy_class != "INTERNAL":
        decision = ("PRIVACY", "Privacy classification requires review", "PRIVACY_STEWARD", "HIGH")
    elif key_role in ("PRIMARY_KEY_CANDIDATE", "FOREIGN_KEY_CANDIDATE"):
        decision = ("KEY_CANDIDATE", f"{key_role.replace('_', ' ').title()} requires data-architect review", "DATA_ARCHITECT", "HIGH")
    elif relationship_evidence is not None:
        decision = ("RELATIONSHIP", "Inferred relationship requires confirmation", "DATA_ARCHITECT", "MEDIUM")
    elif contradictions is not None:
        decision = ("CONTRADICTION", "Conflicting evidence requires resolution", "DOMAIN_STEWARD", "HIGH")
    elif ontology_concept_id is None:
        decision = ("UNMAPPED_CONCEPT", "No approved ontology concept mapped", "DOMAIN_STEWARD", "MEDIUM")
    elif evidence_coverage < evidence_coverage_floor:
        decision = ("LOW_EVIDENCE_COVERAGE", f"Evidence coverage {evidence_coverage:.2f} below floor {evidence_coverage_floor}", "DOMAIN_STEWARD", "MEDIUM")
    elif confidence_score < low_confidence_threshold:
        decision = ("LOW_CONFIDENCE", "Confidence below configured threshold", "DOMAIN_STEWARD", "MEDIUM")

    if decision is None:
        return {"review_trigger": None, "review_reason": None,
                "recommended_reviewer_role": None, "review_priority": None}
    trigger, reason, reviewer, priority = decision
    return {"review_trigger": trigger, "review_reason": reason,
            "recommended_reviewer_role": reviewer, "review_priority": priority}
