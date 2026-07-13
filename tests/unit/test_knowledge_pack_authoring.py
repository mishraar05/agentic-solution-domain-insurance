"""Acceptance and fail-closed tests for multi-module PACK-AUTHORING."""

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from common.contract_validation import (  # noqa: E402
    ContractValidationError,
)
from governed_knowledge_foundation.knowledge_registry import (  # noqa: E402
    assert_immutable_registration,
    load_authored_pack,
    validate_authored_pack,
    validate_manifest_registration,
)
from governed_knowledge_foundation.knowledge_pack_io import (  # noqa: E402
    load_federated_ontology,
    load_knowledge_pack,
)
from governed_knowledge_foundation.ontology import (  # noqa: E402
    normalize_governed_ontology,
)


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "knowledge_packs" / "cots_reference"
SOURCE_PATH = REFERENCE_DIR / "cots_like_reference_v1.json"
ONTOLOGY_PATH = (
    ROOT / "knowledge_packs" / "ontology" / "insurance_ontology_v1.yaml"
)
AUTHORIZATION_PATH = (
    ROOT / "docs" / "governance" /
    "08_knowledge_baseline_evidence_authorization.json"
)
MANIFEST_PATH = ROOT / "knowledge_packs" / "manifest.json"
PACK_CASES = {
    "cots_like_policy_admin": {
        "path": REFERENCE_DIR / "cots_like_policy_admin_v1.json",
        "module": "policy_admin",
        "domain": "Policy",
        "patterns": 20,
        "excluded": 2,
    },
    "cots_like_claims_mgmt": {
        "path": REFERENCE_DIR / "cots_like_claims_mgmt_v1.json",
        "module": "claims_mgmt",
        "domain": "Claims",
        "patterns": 20,
        "excluded": 0,
    },
    "cots_like_billing": {
        "path": REFERENCE_DIR / "cots_like_billing_v1.json",
        "module": "billing",
        "domain": "Billing",
        "patterns": 12,
        "excluded": 0,
    },
}


def _load(path):
    return load_knowledge_pack(path)


def _ontology_ids():
    source, fingerprint = load_federated_ontology(ONTOLOGY_PATH)
    result = normalize_governed_ontology(
        source,
        fingerprint=fingerprint,
        effective_from="2026-07-13",
        created_at="2026-07-13T00:00:00Z",
    )
    return {record["concept_id"] for record in result["concept_records"]}


def _authorization():
    record = _load(AUTHORIZATION_PATH)
    ids = {item["evidence_id"] for item in record["evidence_register"]}
    refs = {
        item["evidence_reference"] for item in record["evidence_register"]
    }
    return ids, refs


def _validate(pack_path, bundle=None):
    ids, refs = _authorization()
    return validate_authored_pack(
        bundle or load_authored_pack(pack_path),
        ontology_concept_ids=_ontology_ids(),
        authorized_evidence_ids=ids,
        authorized_evidence_references=refs,
    )


def _manifest_entry(pack_id):
    manifest = _load(MANIFEST_PATH)
    return next(
        entry for entry in manifest["packs"]
        if entry["pack_id"] == pack_id
    )


@pytest.mark.parametrize("pack_id", sorted(PACK_CASES))
def test_module_pack_is_contract_valid_and_scope_isolated(pack_id):
    case = PACK_CASES[pack_id]
    counts = _validate(case["path"])
    assert counts == {
        "documents": 1,
        "pack_versions": 1,
        "patterns": case["patterns"],
        "extension_markers": 2,
        "excluded_mappings": case["excluded"],
    }

    pack = load_authored_pack(case["path"])
    assert pack["scope"] == {
        "product": "cots_like_suite",
        "module": case["module"],
        "product_version": "1.0.0",
        "domain": case["domain"],
        "line_of_business": "Personal Lines",
    }
    assert {
        item["scope"]["module"] for item in pack["cots_structure_patterns"]
    } == {case["module"]}


def test_all_source_modules_are_covered_without_cross_module_patterns():
    source = _load(SOURCE_PATH)
    modules = {item["module"]: item for item in source["modules"]}
    for case in PACK_CASES.values():
        pack = load_authored_pack(case["path"])
        source_module = modules[case["module"]]
        expected_objects = {table["table"] for table in source_module["tables"]}
        expected_attributes = {
            (table["table"], column["column"])
            for table in source_module["tables"]
            for column in table["columns"]
        }
        object_patterns = {
            item["source_object_pattern"]
            for item in pack["cots_structure_patterns"]
            if item["pattern_type"] == "OBJECT"
        }
        attribute_patterns = {
            (item["source_object_pattern"], item["source_attribute_pattern"])
            for item in pack["cots_structure_patterns"]
            if item["pattern_type"] == "ATTRIBUTE"
        }
        excluded_attributes = {
            (item["source_object"], item["source_attribute"])
            for item in pack["excluded_source_mappings"]
        }
        assert object_patterns == expected_objects
        assert attribute_patterns | excluded_attributes == expected_attributes
        assert not (attribute_patterns & excluded_attributes)


def test_all_pattern_ids_are_unique_across_module_packs():
    pattern_ids = [
        item["pattern_id"]
        for case in PACK_CASES.values()
        for item in load_authored_pack(case["path"])["cots_structure_patterns"]
    ]
    assert len(pattern_ids) == len(set(pattern_ids))


def test_every_concept_pattern_resolves_and_cites_authorized_evidence():
    concept_ids = _ontology_ids()
    evidence_ids, evidence_refs = _authorization()
    allowed = evidence_ids | evidence_refs

    for case in PACK_CASES.values():
        pack = load_authored_pack(case["path"])
        for pattern in pack["cots_structure_patterns"]:
            if pattern["pattern_type"] != "EXTENSION_MARKER":
                assert pattern["ontology_concept_id"] in concept_ids
            refs = set(pattern["provenance"]["evidence_references"])
            assert refs <= allowed
            assert refs & evidence_ids


def test_policy_pack_retains_historical_scope_exclusions():
    pack = load_authored_pack(PACK_CASES["cots_like_policy_admin"]["path"])
    excluded = {
        (item["source_object"], item["source_attribute"], item["source_concept_id"])
        for item in pack["excluded_source_mappings"]
    }
    assert excluded == {
        ("pa_policy", "update_time", "Technical.SourceUpdatedTimestamp"),
        ("pa_policy_term", "written_premium_amt", "Policy.WrittenPremium"),
    }


@pytest.mark.parametrize("pack_id", sorted(PACK_CASES))
def test_manifest_identity_version_and_fingerprint_match_pack(pack_id):
    assert validate_manifest_registration(
        PACK_CASES[pack_id]["path"], _manifest_entry(pack_id)
    )


def test_legacy_authoring_source_remains_immutable_and_separately_registered():
    source_digest = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    assert source_digest == (
        "9764cf01db7df9f3369fef9d46fa331d220721b8f020d9abe276edfd801e2742"
    )
    legacy = _manifest_entry("cots_like_reference")
    assert legacy["path"] == "cots_reference/cots_like_reference_v1.json"


def test_unknown_concept_fails_closed():
    path = PACK_CASES["cots_like_claims_mgmt"]["path"]
    pack = load_authored_pack(path)
    pattern = next(
        item for item in pack["cots_structure_patterns"]
        if item["pattern_type"] == "ATTRIBUTE"
    )
    pattern["ontology_concept_id"] = "Claims.InventedConcept"
    with pytest.raises(ContractValidationError, match="unavailable ontology"):
        _validate(path, pack)


def test_unauthorized_evidence_fails_closed():
    path = PACK_CASES["cots_like_billing"]["path"]
    pack = load_authored_pack(path)
    pack["cots_structure_patterns"][0]["provenance"]["evidence_references"] = [
        "EVIDENCE.UNAUTHORIZED"
    ]
    with pytest.raises(ContractValidationError, match="unauthorized evidence"):
        _validate(path, pack)


def test_authorized_evidence_from_another_module_fails_closed():
    path = PACK_CASES["cots_like_claims_mgmt"]["path"]
    pack = load_authored_pack(path)
    pack["cots_structure_patterns"][0]["provenance"]["evidence_references"] = [
        "EVIDENCE.KNOWLEDGE.COTS_LIKE_BILLING.1",
        pack["authoring_source"],
    ]
    with pytest.raises(ContractValidationError, match="pack evidence ID"):
        _validate(path, pack)


def test_scope_or_version_drift_fails_closed():
    path = PACK_CASES["cots_like_claims_mgmt"]["path"]
    pack = load_authored_pack(path)
    pack["cots_structure_patterns"][0]["scope"]["product_version"] = "2.0.0"
    with pytest.raises(ContractValidationError, match="scope must equal"):
        _validate(path, pack)


def test_duplicate_pattern_id_fails_closed():
    path = PACK_CASES["cots_like_billing"]["path"]
    pack = load_authored_pack(path)
    pack["cots_structure_patterns"][1]["pattern_id"] = (
        pack["cots_structure_patterns"][0]["pattern_id"]
    )
    with pytest.raises(ContractValidationError, match="not unique"):
        _validate(path, pack)


@pytest.mark.parametrize("pack_id", sorted(PACK_CASES))
def test_existing_pack_identity_cannot_be_repointed_or_rewritten(pack_id):
    existing = _manifest_entry(pack_id)
    for field, value in (
        ("path", "cots_reference/replacement.json"),
        ("content_sha256", "0" * 64),
    ):
        candidate = deepcopy(existing)
        candidate[field] = value
        with pytest.raises(ContractValidationError, match="cannot be registered"):
            assert_immutable_registration(existing, candidate)
