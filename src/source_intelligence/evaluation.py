"""Evaluate deterministic predictions against the synthetic labelled set.

This module runs naming, privacy, key, relationship, and review-routing rules
for each labelled attribute and reports classification coverage plus exact
field-match counts and rates. The result is useful local gate evidence, but it
does not claim the labels are independently approved. Human relabelling and
confidence calibration remain separate governance requirements.
"""

from source_intelligence.naming import classify_naming
from source_intelligence.privacy import classify_privacy
from source_intelligence.relationships import (
    KNOWN_RELATIONSHIPS,
    infer_key_role,
    infer_relationship,
)
from source_intelligence.routing import route_review


def _relationship_target(table_name, column_name):
    target = KNOWN_RELATIONSHIPS.get((table_name, column_name))
    return ".".join(target) if target else None


def evaluate_labelled_records(records):
    """Evaluate deterministic semantics and routing without claiming label approval."""
    results = []
    for label in records:
        table_name = label["source_table"]
        column_name = label["source_column"]
        business_name, concept, domain, _, _ = classify_naming(
            table_name, column_name
        )
        privacy_class, _ = classify_privacy(column_name)
        key_role = infer_key_role(table_name, column_name)
        relationship = infer_relationship(table_name, column_name)
        route = route_review(
            confidence_score=1.0,
            evidence_coverage=1.0,
            privacy_class=privacy_class,
            relationship_evidence=relationship,
            ontology_concept_id=concept,
            key_role=key_role,
            contradictions=None,
        )["recommended_reviewer_role"] or "NONE"
        predicted = {
            "business_name": business_name,
            "ontology_concept": concept,
            "domain": domain,
            "privacy_class": privacy_class,
            "key_role": key_role,
            "relationship_target": _relationship_target(table_name, column_name),
            "review_route": route,
        }
        expected = {
            "business_name": label["expected_business_name"],
            "ontology_concept": label["expected_ontology_concept"],
            "domain": label["expected_domain"],
            "privacy_class": label["expected_privacy_class"],
            "key_role": label["expected_key_role"],
            "relationship_target": label["expected_relationship_target"],
            "review_route": label["expected_review_route"],
        }
        results.append({
            "record_id": label["record_id"],
            "classified": bool(business_name and domain),
            "matches": {
                field: predicted[field] == expected[field]
                for field in expected
            },
        })

    total = len(results)
    field_matches = {
        field: sum(result["matches"][field] for result in results)
        for field in results[0]["matches"]
    } if results else {}
    classified = sum(result["classified"] for result in results)
    return {
        "labelled_records": total,
        "semantic_classification_coverage": (
            classified / total if total else 0.0
        ),
        "field_match_counts": field_matches,
        "field_match_rates": {
            field: matches / total if total else 0.0
            for field, matches in field_matches.items()
        },
        "mismatched_record_ids": [
            result["record_id"]
            for result in results
            if not all(result["matches"].values())
        ],
    }
