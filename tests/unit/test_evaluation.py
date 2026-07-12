"""Local Phase 2 labelled-set evaluation tests."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.evaluation import evaluate_labelled_records


def test_labelled_set_meets_local_classification_and_routing_expectations():
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "evals",
        "labelled_set",
        "source_attributes_v1.json",
    )
    with open(path, encoding="utf-8") as handle:
        labels = json.load(handle)["records"]
    result = evaluate_labelled_records(labels)

    assert result["labelled_records"] == 19
    assert result["semantic_classification_coverage"] >= 0.90
    assert result["field_match_rates"]["relationship_target"] == 1.0
    assert result["field_match_rates"]["privacy_class"] == 1.0
    assert result["field_match_rates"]["review_route"] == 1.0
