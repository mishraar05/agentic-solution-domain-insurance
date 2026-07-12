"""Governed confidence calculation from weighted components."""
from dataclasses import dataclass

FORMULA_VERSION = "1.0.0"
WEIGHTS = {"naming_strength": 0.35, "type_strength": 0.20, "relationship_strength": 0.25, "cots_match_strength": 0.10, "standard_consistency": 0.10}
EVIDENCE_COVERAGE_FLOOR = 0.60


@dataclass
class ConfidenceResult:
    score: float
    components: dict
    evidence_coverage: float
    formula_version: str
    confidence_reason: str
    raw_weighted_sum: float
    normalized_score: float


def compute_confidence(naming_strength, type_strength, relationship_strength,
                       cots_match_strength=None, standard_consistency=None,
                       naming_contradicted=False, type_contradicted=False,
                       relationship_contradicted=False, cots_contradicted=False,
                       standard_contradicted=False):
    """Compute governed confidence score from components.

    Each component can be AVAILABLE, NOT_AVAILABLE, or CONTRADICTED.
    CONTRADICTED components are excluded from the weighted sum and
    flagged for human review by the routing layer.
    """
    def _component(value, key, contradicted=False):
        if contradicted:
            availability = "CONTRADICTED"
        elif value is not None:
            availability = "AVAILABLE"
        else:
            availability = "NOT_AVAILABLE"
        return {"value": value, "availability": availability, "weight": WEIGHTS[key]}

    components = {
        "naming_strength": _component(naming_strength, "naming_strength", naming_contradicted),
        "type_strength": _component(type_strength, "type_strength", type_contradicted),
        "relationship_strength": _component(relationship_strength, "relationship_strength", relationship_contradicted),
        "cots_match_strength": _component(cots_match_strength, "cots_match_strength", cots_contradicted),
        "standard_consistency": _component(standard_consistency, "standard_consistency", standard_contradicted),
    }
    raw_weighted_sum = 0.0
    available_weight = 0.0
    total_weight = sum(WEIGHTS.values())
    for comp in components.values():
        if comp["availability"] == "AVAILABLE" and comp["value"] is not None:
            raw_weighted_sum += comp["value"] * comp["weight"]
            available_weight += comp["weight"]
    evidence_coverage = available_weight / total_weight if total_weight > 0 else 0.0
    normalized_score = raw_weighted_sum / available_weight if available_weight > 0 else 0.0
    score = round(normalized_score, 4)
    if evidence_coverage < EVIDENCE_COVERAGE_FLOOR:
        reason = f"Evidence coverage {evidence_coverage:.2f} below floor {EVIDENCE_COVERAGE_FLOOR}; forced review"
    else:
        avail = len([c for c in components.values() if c["availability"] == "AVAILABLE"])
        reason = f"Computed from {avail} available components"
    return ConfidenceResult(score=score, components=components, evidence_coverage=round(evidence_coverage, 4), formula_version=FORMULA_VERSION, confidence_reason=reason, raw_weighted_sum=round(raw_weighted_sum, 4), normalized_score=round(normalized_score, 4))