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


def compute_confidence(naming_strength, type_strength, relationship_strength, cots_match_strength=None, standard_consistency=None):
    """Compute governed confidence score from components."""
    components = {
        "naming_strength": {"value": naming_strength, "availability": "AVAILABLE", "weight": WEIGHTS["naming_strength"]},
        "type_strength": {"value": type_strength, "availability": "AVAILABLE", "weight": WEIGHTS["type_strength"]},
        "relationship_strength": {"value": relationship_strength, "availability": "AVAILABLE", "weight": WEIGHTS["relationship_strength"]},
    }
    if cots_match_strength is not None:
        components["cots_match_strength"] = {"value": cots_match_strength, "availability": "AVAILABLE", "weight": WEIGHTS["cots_match_strength"]}
    else:
        components["cots_match_strength"] = {"value": None, "availability": "NOT_AVAILABLE", "weight": WEIGHTS["cots_match_strength"]}
    if standard_consistency is not None:
        components["standard_consistency"] = {"value": standard_consistency, "availability": "AVAILABLE", "weight": WEIGHTS["standard_consistency"]}
    else:
        components["standard_consistency"] = {"value": None, "availability": "NOT_AVAILABLE", "weight": WEIGHTS["standard_consistency"]}
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
