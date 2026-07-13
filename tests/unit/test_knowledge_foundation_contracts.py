"""Positive, negative, isolation, and compatibility tests for KNOWLEDGE-CONTRACTS."""

from copy import deepcopy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from common.contract_validation import (  # noqa: E402
    ContractValidationError,
    load_contract,
)
from governed_knowledge_foundation.knowledge_contract_validation import (  # noqa: E402
    ContractCompatibilityError,
    KNOWLEDGE_FOUNDATION_CONTRACTS,
    assert_contract_backward_compatible,
    validate_knowledge_records,
)


SCOPE = {
    "product": "cots_like_suite",
    "module": "policy_admin",
    "product_version": "1.0.0",
    "domain": "Policy",
    "line_of_business": "Personal Lines",
}
PROVENANCE = {
    "pack_id": "cots_like_reference",
    "pack_version": "1.0.0",
    "effective_from": "2026-07-13",
    "effective_to": None,
    "approval_state": "PROPOSED",
    "owner_role": "DATA_ARCHITECT",
    "evidence_references": ["EVIDENCE.KNOWLEDGE.COTS_LIKE_POLICY_ADMIN.1"],
    "content_fingerprint": "a" * 64,
    "created_at": "2026-07-13T00:00:00Z",
}


def _confidence(value, availability="AVAILABLE"):
    return {
        "value": value,
        "availability": availability,
        "evidence_reference": "EVIDENCE.KNOWLEDGE.COTS_LIKE_POLICY_ADMIN.1",
        "weight": 0.2,
    }


def valid_records():
    return {
        "knowledge_document.json": {
            "schema_version": "1.0.0",
            "document_id": "EVIDENCE.KNOWLEDGE.COTS_LIKE_POLICY_ADMIN.1",
            "title": "Synthetic policy administration reference metadata",
            "evidence_class": "SYNTHETIC_GOVERNED_KNOWLEDGE",
            "source_classification": "SYNTHETIC_VENDOR_NEUTRAL",
            "authorization_basis": "Repository-authored synthetic metadata.",
            "retention_class": "VERSION_CONTROLLED_METADATA",
            "structured_retrieval_eligible": True,
            "prompt_eligible": False,
            "vector_index_eligible": False,
            "raw_document_body_retained": False,
            "scope": deepcopy(SCOPE),
            "provenance": deepcopy(PROVENANCE),
        },
        "knowledge_concept.json": {
            "schema_version": "1.0.0",
            "concept_id": "Policy.PolicyNumber",
            "concept_name": "Policy Number",
            "definition": "A business identifier assigned to a policy.",
            "concept_type": "ATTRIBUTE",
            "lifecycle_state": "Standard",
            "privacy_class": "INTERNAL",
            "synonyms": ["Policy Identifier"],
            "physical_name_variants": ["policy_number", "POLNBR"],
            "lob_applicability": ["ALL"],
            "temporality": "STATIC",
            "typical_attributes": [],
            "status_values": [],
            "steward_notes": "Business identifier, distinct from the system key.",
            "scope": deepcopy(SCOPE),
            "provenance": deepcopy(PROVENANCE),
        },
        "ontology_relationship.json": {
            "schema_version": "1.0.0",
            "relationship_id": "REL.Policy.HasCoverage",
            "source_concept_id": "Policy.Policy",
            "target_concept_id": "Coverage.Coverage",
            "relationship_type": "HAS",
            "source_relationship_type": "has_many",
            "source_cardinality": "ONE",
            "target_cardinality": "ZERO_OR_MORE",
            "definition": "A policy may contain governed coverage records.",
            "lifecycle_state": "Standard",
            "scope": deepcopy(SCOPE),
            "provenance": deepcopy(PROVENANCE),
        },
        "cots_structure_pattern.json": {
            "schema_version": "1.0.0",
            "pattern_id": "PATTERN.Policy.PolicyNumber",
            "pattern_type": "ATTRIBUTE",
            "source_object_pattern": "pa_policy",
            "source_attribute_pattern": "policy_number",
            "ontology_concept_id": "Policy.PolicyNumber",
            "expected_physical_types": ["string"],
            "required_for_object_match": True,
            "expected_confidence": 0.95,
            "match_evidence": ["Exact governed attribute name"],
            "lifecycle_state": "Standard",
            "scope": deepcopy(SCOPE),
            "provenance": deepcopy(PROVENANCE),
        },
        "knowledge_pack_version.json": {
            "schema_version": "1.0.0",
            "pack_id": "cots_like_reference",
            "pack_version": "1.0.0",
            "pack_status": "DEVELOPMENT",
            "parent_pack_version": None,
            "description": "Synthetic policy administration baseline.",
            "changelog": ["Initial governed development version."],
            "scope": deepcopy(SCOPE),
            "provenance": deepcopy(PROVENANCE),
        },
        "cots_match_assessment.json": {
            "schema_version": "1.0.0",
            "assessment_id": "cots_match_" + "b" * 32,
            "run_id": "si_job_123",
            "engagement_id": "pilot",
            "source_system": "synthetic_insurance_source",
            "source_table": "pa_policy",
            "source_column": "policy_number",
            "pattern_id": "PATTERN.Policy.PolicyNumber",
            "ontology_concept_id": "Policy.PolicyNumber",
            "match_outcome": "MATCHED",
            "proposed_lifecycle_state": "Standard",
            "confidence_score": 0.95,
            "confidence_components": {
                "object_name_match": _confidence(1.0),
                "attribute_coverage": _confidence(1.0),
                "type_compatibility": _confidence(1.0),
                "relationship_shape": _confidence(None, "NOT_AVAILABLE"),
                "extension_marker": _confidence(0.0),
            },
            "assumptions": [],
            "contradictions": [],
            "open_questions": [],
            "scope": deepcopy(SCOPE),
            "provenance": deepcopy(PROVENANCE),
            "approval_state": "PROPOSED",
            "created_at": "2026-07-13T00:00:00Z",
        },
        "knowledge_context.json": {
            "schema_version": "1.0.0",
            "context_id": "knowledge_context_" + "c" * 32,
            "engagement_id": "pilot",
            "source_system": "synthetic_insurance_source",
            "effective_at": "2026-07-13",
            "usage_mode": "DEVELOPMENT",
            "required_approval_state": "PROPOSED",
            "scope": deepcopy(SCOPE),
            "pack_id": "cots_like_reference",
            "pack_version": "1.0.0",
            "knowledge_items": [{
                "record_type": "PATTERN",
                "record_id": "PATTERN.Policy.PolicyNumber",
                "scope": deepcopy(SCOPE),
                "pack_id": "cots_like_reference",
                "pack_version": "1.0.0",
                "approval_state": "PROPOSED",
                "effective_from": "2026-07-13",
                "effective_to": None,
                "evidence_references": ["EVIDENCE.KNOWLEDGE.COTS_LIKE_POLICY_ADMIN.1"],
                "content_fingerprint": "d" * 64,
            }],
            "context_fingerprint": "e" * 64,
            "created_at": "2026-07-13T00:00:00Z",
        },
    }


@pytest.mark.parametrize("contract_name", sorted(KNOWLEDGE_FOUNDATION_CONTRACTS))
def test_valid_knowledge_foundation_record_passes(contract_name):
    record = valid_records()[contract_name]
    assert validate_knowledge_records([record], contract_name) == 1


def test_all_knowledge_foundation_contracts_use_draft_2020_12_and_closed_shapes():
    for contract_name in KNOWLEDGE_FOUNDATION_CONTRACTS:
        schema = load_contract(contract_name)
        assert schema["$schema"].endswith("draft/2020-12/schema")
        assert schema["additionalProperties"] is False


@pytest.mark.parametrize("missing_field", ["pack_version", "evidence_references"])
def test_missing_provenance_fails(missing_field):
    record = valid_records()["knowledge_concept.json"]
    del record["provenance"][missing_field]
    with pytest.raises(ContractValidationError, match="missing required"):
        validate_knowledge_records([record], "knowledge_concept.json")


def test_generated_match_cannot_claim_approval():
    record = valid_records()["cots_match_assessment.json"]
    record["approval_state"] = "APPROVED"
    with pytest.raises(ContractValidationError, match="expected constant"):
        validate_knowledge_records([record], "cots_match_assessment.json")


def test_invalid_lifecycle_state_fails():
    record = valid_records()["knowledge_concept.json"]
    record["lifecycle_state"] = "Automatically approved"
    with pytest.raises(ContractValidationError, match="not in enum"):
        validate_knowledge_records([record], "knowledge_concept.json")


def test_unauthorized_or_raw_document_fails():
    record = valid_records()["knowledge_document.json"]
    record["evidence_class"] = "PROPRIETARY_COTS_DOCUMENTATION"
    with pytest.raises(ContractValidationError, match="not in enum"):
        validate_knowledge_records([record], "knowledge_document.json")

    record = valid_records()["knowledge_document.json"]
    record["raw_document_body_retained"] = True
    with pytest.raises(ContractValidationError, match="expected constant"):
        validate_knowledge_records([record], "knowledge_document.json")


def test_cross_version_context_fails_closed():
    record = valid_records()["knowledge_context.json"]
    record["knowledge_items"][0]["pack_version"] = "2.0.0"
    with pytest.raises(ContractValidationError, match="selected pack version"):
        validate_knowledge_records([record], "knowledge_context.json")


def test_cross_product_scope_context_fails_closed():
    record = valid_records()["knowledge_context.json"]
    record["knowledge_items"][0]["scope"]["product"] = "different_product"
    with pytest.raises(ContractValidationError, match="requested context scope"):
        validate_knowledge_records([record], "knowledge_context.json")


def test_authoritative_context_requires_approved_knowledge():
    record = valid_records()["knowledge_context.json"]
    record["usage_mode"] = "AUTHORITATIVE"
    with pytest.raises(ContractValidationError, match="requires APPROVED"):
        validate_knowledge_records([record], "knowledge_context.json")


def test_unresolved_match_cannot_retain_invented_mapping():
    record = valid_records()["cots_match_assessment.json"]
    record["match_outcome"] = "UNRESOLVED"
    record["proposed_lifecycle_state"] = "Unresolved"
    with pytest.raises(ContractValidationError, match="must not invent"):
        validate_knowledge_records([record], "cots_match_assessment.json")


def test_compatible_optional_addition_is_accepted():
    previous = {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}
    candidate = deepcopy(previous)
    candidate["properties"]["description"] = {"type": "string"}
    assert assert_contract_backward_compatible(previous, candidate)


@pytest.mark.parametrize("mutation", ["remove", "require", "narrow_enum", "change_type"])
def test_breaking_schema_changes_are_detected(mutation):
    previous = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "state": {"type": "string", "enum": ["PROPOSED", "APPROVED"]},
        },
        "required": ["id"],
    }
    candidate = deepcopy(previous)
    if mutation == "remove":
        del candidate["properties"]["id"]
    elif mutation == "require":
        candidate["required"].append("state")
    elif mutation == "narrow_enum":
        candidate["properties"]["state"]["enum"] = ["APPROVED"]
    else:
        candidate["properties"]["id"]["type"] = "integer"

    with pytest.raises(ContractCompatibilityError):
        assert_contract_backward_compatible(previous, candidate)
