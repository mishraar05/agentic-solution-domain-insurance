"""Validate governed ontology normalization and relationship integrity."""

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from common.contract_validation import (  # noqa: E402
    ContractValidationError,
)
from governed_knowledge_foundation.ontology import (  # noqa: E402
    normalize_governed_ontology,
    validate_normalized_ontology,
)
from governed_knowledge_foundation.knowledge_pack_io import (  # noqa: E402
    load_federated_ontology,
)


ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_PATH = (
    ROOT / "knowledge_packs" / "ontology" / "insurance_ontology_v1.yaml"
)


def _source_pack():
    return load_federated_ontology(ONTOLOGY_PATH)[0]


def _normalized(source_pack=None):
    pack = source_pack or _source_pack()
    _, fingerprint = load_federated_ontology(ONTOLOGY_PATH)
    return normalize_governed_ontology(
        pack,
        fingerprint=fingerprint,
        effective_from="2026-07-13",
        created_at="2026-07-13T00:00:00Z",
    )


def test_governed_ontology_emits_all_declared_domain_concepts():
    result = _normalized()
    concept_ids = [record["concept_id"] for record in result["concept_records"]]
    source_ids = [record["concept_id"] for record in _source_pack()["concepts"]]

    assert concept_ids == source_ids
    assert len(concept_ids) == 124
    assert len(result["relationship_records"]) == 167


def test_concepts_and_relationships_are_contract_valid_with_resolved_endpoints():
    result = _normalized()
    assert validate_normalized_ontology(
        result["concept_records"], result["relationship_records"]
    ) == (124, 167)

    concept_ids = {record["concept_id"] for record in result["concept_records"]}
    for relationship in result["relationship_records"]:
        assert relationship["source_concept_id"] in concept_ids
        assert relationship["target_concept_id"] in concept_ids


def test_normalization_preserves_meaning_fields_and_stable_ids():
    source = _source_pack()
    source_policy_number = next(
        item for item in source["concepts"]
        if item["concept_id"] == "Policy.PolicyNumber"
    )
    normalized = next(
        item for item in _normalized(source)["concept_records"]
        if item["concept_id"] == "Policy.PolicyNumber"
    )

    assert normalized["concept_name"] == source_policy_number["name"]
    assert normalized["definition"] == source_policy_number["definition"]
    assert normalized["concept_type"] == source_policy_number["concept_type"]
    assert normalized["synonyms"] == source_policy_number["synonyms"]
    assert normalized["physical_name_variants"] == (
        source_policy_number["physical_name_variants"]
    )
    assert normalized["temporality"] == source_policy_number["temporality"]
    assert normalized["steward_notes"] == source_policy_number["steward_notes"]


def test_privacy_mapping_is_explicit_and_not_name_inferred():
    records = {
        item["concept_id"]: item for item in _normalized()["concept_records"]
    }
    assert records["Policy.Policy"]["privacy_class"] == "INTERNAL"
    assert records["Policy.PolicyNumber"]["privacy_class"] == "PERSONAL_DATA"


def test_explicit_domain_subset_reports_cross_boundary_relationships():
    source = _source_pack()
    result = normalize_governed_ontology(
        source,
        fingerprint=load_federated_ontology(ONTOLOGY_PATH)[1],
        effective_from="2026-07-13",
        created_at="2026-07-13T00:00:00Z",
        included_domains=("Billing",),
    )
    assert {item["scope"]["domain"] for item in result["concept_records"]} == {
        "Billing"
    }
    assert result["excluded_relationships"]
    assert {item["reason"] for item in result["excluded_relationships"]} == {
        "TARGET_OUTSIDE_GOVERNED_SCOPE"
    }


def test_missing_required_concept_fails_instead_of_being_invented():
    source = _source_pack()
    source["concepts"] = [
        item for item in source["concepts"]
        if item["concept_id"] != "Shared.Party"
    ]
    with pytest.raises(ContractValidationError, match="targets are missing"):
        _normalized(source)


def test_unsupported_in_scope_relationship_type_fails_closed():
    source = deepcopy(_source_pack())
    policy = next(
        item for item in source["concepts"]
        if item["concept_id"] == "Policy.Policy"
    )
    policy["relationships"][0]["type"] = "unknown_semantics"

    with pytest.raises(ContractValidationError, match="Unsupported ontology"):
        _normalized(source)


def test_normalized_relationship_with_missing_endpoint_is_rejected():
    result = _normalized()
    relationships = deepcopy(result["relationship_records"])
    relationships[0]["target_concept_id"] = "Policy.MissingConcept"

    with pytest.raises(ContractValidationError, match="Missing target endpoint"):
        validate_normalized_ontology(result["concept_records"], relationships)
