"""Compute governed confidence from explicit, inspectable evidence components.

The score is a deterministic weighted calculation rather than an LLM opinion.
Each component records its value, configured weight, and whether evidence is
available, unavailable, or contradicted. Missing and contradicted evidence is
excluded from score normalization but reduces evidence coverage; routing uses
that coverage and any contradiction to require human review. Confidence never
changes a recommendation from ``PROPOSED`` to an approved state.
"""
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


def compute_confidence(
    naming_strength,
    type_strength,
    relationship_strength,
    cots_match_strength=None,
    standard_consistency=None,
    naming_contradicted=False,
    type_contradicted=False,
    relationship_contradicted=False,
    cots_contradicted=False,
    standard_contradicted=False,
):
    """Compute confidence while retaining unavailable and conflicting evidence."""

    def _component(value, key, contradicted=False):
        if contradicted:
            availability = "CONTRADICTED"
        elif value is None:
            availability = "NOT_AVAILABLE"
        else:
            availability = "AVAILABLE"
        return {"value": value, "availability": availability, "weight": WEIGHTS[key]}

    components = {
        "naming_strength": _component(
            naming_strength, "naming_strength", naming_contradicted
        ),
        "type_strength": _component(
            type_strength, "type_strength", type_contradicted
        ),
        "relationship_strength": _component(
            relationship_strength,
            "relationship_strength",
            relationship_contradicted,
        ),
        "cots_match_strength": _component(
            cots_match_strength, "cots_match_strength", cots_contradicted
        ),
        "standard_consistency": _component(
            standard_consistency, "standard_consistency", standard_contradicted
        ),
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
        available = sum(
            component["availability"] == "AVAILABLE"
            for component in components.values()
        )
        contradicted = sum(
            component["availability"] == "CONTRADICTED"
            for component in components.values()
        )
        reason = f"Computed from {available} available components"
        if contradicted:
            reason += f"; {contradicted} contradicted component(s) require review"
    return ConfidenceResult(
        score=score,
        components=components,
        evidence_coverage=round(evidence_coverage, 4),
        formula_version=FORMULA_VERSION,
        confidence_reason=reason,
        raw_weighted_sum=round(raw_weighted_sum, 4),
        normalized_score=round(normalized_score, 4),
    )
