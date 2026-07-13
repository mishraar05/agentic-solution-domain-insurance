"""Tests for human review lifecycle and unchanged-rejection suppression."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from common.contract_validation import validate_records
from source_intelligence.review_lifecycle import (
    create_review_decision,
    should_suppress_unchanged,
)


def _queue_item():
    return {
        "schema_version": "1.0.0",
        "queue_item_id": "si_job_12:bronze_policy:policy_id",
        "run_id": "si_job_12",
        "artifact_version": "0.3.0",
        "engagement_id": "synthetic-pilot",
        "source_table": "bronze_policy",
        "source_column": "policy_id",
        "proposed_business_name": "Policy Identifier",
        "domain": "Policy",
        "ontology_concept_id": "Policy.Identifier",
        "key_role": "PRIMARY_KEY_CANDIDATE",
        "confidence_score": 0.91,
        "evidence_coverage": 0.8,
        "privacy_class": "INTERNAL",
        "review_trigger": "KEY_CANDIDATE",
        "review_reason": "Key candidate requires architect confirmation",
        "review_priority": "HIGH",
        "recommended_reviewer_role": "DATA_ARCHITECT",
        "queue_status": "OPEN",
        "assumptions": None,
        "open_question": None,
        "queued_at": "2026-07-12T08:00:00+00:00",
    }


def test_decision_links_to_one_queue_item_and_validates():
    decision = create_review_decision(
        _queue_item(),
        "DATA_ARCHITECT",
        "APPROVED",
        "Confirmed against the synthetic pilot key design.",
        "2026-07-12T09:00:00+00:00",
    )
    assert decision["queue_item_id"] == _queue_item()["queue_item_id"]
    assert decision["queue_status"] == "CLOSED"
    assert validate_records([decision], "review_decision.json") == 1


def test_wrong_reviewer_role_is_rejected():
    with pytest.raises(ValueError, match="routed role"):
        create_review_decision(
            _queue_item(),
            "DOMAIN_STEWARD",
            "APPROVED",
            "Looks correct.",
            "2026-07-12T09:00:00+00:00",
        )


def test_rationale_is_mandatory():
    with pytest.raises(ValueError, match="rationale"):
        create_review_decision(
            _queue_item(),
            "DATA_ARCHITECT",
            "REJECTED",
            " ",
            "2026-07-12T09:00:00+00:00",
        )


def test_modified_decision_requires_targeted_invalidation():
    with pytest.raises(ValueError, match="invalidation"):
        create_review_decision(
            _queue_item(),
            "DATA_ARCHITECT",
            "MODIFIED",
            "Change the proposed key role.",
            "2026-07-12T09:00:00+00:00",
        )


def test_rejected_recommendation_cannot_reappear_unchanged():
    queue_item = _queue_item()
    decision = create_review_decision(
        queue_item,
        "DATA_ARCHITECT",
        "REJECTED",
        "The source does not guarantee uniqueness.",
        "2026-07-12T09:00:00+00:00",
    )
    assert should_suppress_unchanged(queue_item, [decision])
    changed = {**queue_item, "key_role": "NON_KEY"}
    assert not should_suppress_unchanged(changed, [decision])


def test_source_documentation_routes_to_documentation_decision_type():
    queue_item = {
        **_queue_item(),
        "queue_item_id": (
            "si_job_12:bronze_policy:policy_id:source_documentation"
        ),
        "review_trigger": "SOURCE_DOCUMENTATION",
        "recommended_reviewer_role": "DOMAIN_STEWARD",
        "assumptions": '{"column_description":"Proposed policy identifier."}',
    }
    decision = create_review_decision(
        queue_item,
        "DOMAIN_STEWARD",
        "APPROVED",
        "Description and glossary term are supported by the source context.",
        "2026-07-12T09:00:00+00:00",
    )
    assert decision["recommendation_type"] == "SOURCE_DOCUMENTATION"
    assert validate_records([decision], "review_decision.json") == 1
