"""Review routing logic for recommendations."""

LOW_CONFIDENCE_THRESHOLD = 0.75


def route_review(confidence_score, evidence_coverage, privacy_class, relationship_evidence, ontology_concept_id, key_role, contradictions, evidence_coverage_floor=0.60):
    """Determine if a recommendation needs review and who should review it."""
    review_reason = None
    reviewer = None
    if privacy_class != "INTERNAL":
        review_reason = "Privacy classification requires review"
        reviewer = "PRIVACY_STEWARD"
    elif relationship_evidence is not None:
        review_reason = "Inferred relationship requires confirmation"
        reviewer = "DATA_ARCHITECT"
    elif ontology_concept_id is None:
        review_reason = "No approved ontology concept mapped"
        reviewer = "DOMAIN_STEWARD"
    elif contradictions is not None:
        review_reason = "Conflicting evidence requires resolution"
        reviewer = "DOMAIN_STEWARD"
    elif evidence_coverage < evidence_coverage_floor:
        review_reason = f"Evidence coverage {evidence_coverage:.2f} below floor {evidence_coverage_floor}"
        reviewer = "DOMAIN_STEWARD"
    elif confidence_score < LOW_CONFIDENCE_THRESHOLD:
        review_reason = "Confidence below configured threshold"
        reviewer = "DOMAIN_STEWARD"
    if review_reason is None:
        return {"review_reason": None, "recommended_reviewer_role": None}
    return {"review_reason": review_reason, "recommended_reviewer_role": reviewer}
