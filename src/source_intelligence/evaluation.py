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
    discover_relationship_candidates,
    infer_key_roles,
    relationship_evidence_by_attribute,
)
from source_intelligence.routing import route_review


def _runtime_relationship_context(records):
    tables = {}
    for position, record in enumerate(records, start=1):
        tables.setdefault(record["source_table"], []).append({
            "name": record["source_column"],
            "nullable": False,
            "ordinal_position": position,
        })
    roles = {
        table_name: infer_key_roles(table_name, columns)
        for table_name, columns in tables.items()
    }
    attributes = [
        {
            "source_table": record["source_table"],
            "source_column": record["source_column"],
            "physical_type": "LABELLED_SET_TYPE_NOT_AVAILABLE",
            "key_role": roles[record["source_table"]][record["source_column"]],
        }
        for record in records
    ]
    candidates = discover_relationship_candidates(attributes)
    evidence = relationship_evidence_by_attribute(candidates)
    targets = {}
    for candidate in candidates:
        key = (candidate["from_table"], candidate["from_column"])
        target = f"{candidate['to_table']}.{candidate['to_column']}"
        targets.setdefault(key, []).append(target)
    resolved_targets = {
        key: values[0] if len(values) == 1 else "|".join(sorted(values))
        for key, values in targets.items()
    }
    return roles, evidence, resolved_targets


def evaluate_labelled_records(records):
    """Evaluate deterministic semantics and routing without claiming label approval."""
    results = []
    roles, relationships, targets = _runtime_relationship_context(records)
    for label in records:
        table_name = label["source_table"]
        column_name = label["source_column"]
        business_name, concept, domain, _, _ = classify_naming(
            table_name, column_name
        )
        privacy_class, _ = classify_privacy(column_name)
        key_role = roles[table_name][column_name]
        relationship = relationships.get((table_name, column_name))
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
            "relationship_target": targets.get((table_name, column_name)),
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
