"""Validate the BASELINE-AUTHORIZATION baseline selection and evidence authorization record."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION_PATH = (
    ROOT / "docs" / "governance" /
    "08_knowledge_baseline_evidence_authorization.json"
)


def _load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_knowledge_baseline_has_three_exact_module_scopes():
    record = _load(AUTHORIZATION_PATH)

    assert record["work_package_id"] == "BASELINE-AUTHORIZATION"
    assert record["selected_suite"] is True
    assert {
        (item["module"], item["domain"], item["pack_id"])
        for item in record["baselines"]
    } == {
        ("policy_admin", "Policy", "cots_like_policy_admin"),
        ("claims_mgmt", "Claims", "cots_like_claims_mgmt"),
        ("billing", "Billing", "cots_like_billing"),
    }
    assert {item["product"] for item in record["baselines"]} == {
        "cots_like_suite"
    }
    assert {item["product_version"] for item in record["baselines"]} == {
        "1.0.0"
    }
    assert record["source_classification"] == "SYNTHETIC_VENDOR_NEUTRAL"
    assert record["prohibited_claim"] == "REAL_VENDOR_IDENTIFICATION"


def test_baseline_identity_and_fingerprint_match_the_registered_pack():
    record = _load(AUTHORIZATION_PATH)
    for pack_metadata in record["baselines"]:
        pack_path = ROOT / pack_metadata["path"]
        pack = _load(pack_path)
        digest = hashlib.sha256(pack_path.read_bytes()).hexdigest()

        assert pack["pack_id"] == pack_metadata["pack_id"]
        assert pack["pack_version"] == pack_metadata["pack_version"]
        assert pack["scope"]["module"] == pack_metadata["module"]
        assert digest == pack_metadata["content_sha256"]


def test_evidence_register_is_minimized_and_governed():
    record = _load(AUTHORIZATION_PATH)
    assert len(record["evidence_register"]) == 3
    assert len({item["evidence_id"] for item in record["evidence_register"]}) == 3
    for evidence in record["evidence_register"]:
        assert evidence["classification"] == "SYNTHETIC_GOVERNED_KNOWLEDGE"
        assert evidence["authorization_basis"]
        assert evidence["retention_class"]
        assert evidence["structured_retrieval_eligible_for_development"] is True
        assert evidence["raw_document_prompt_eligible"] is False
        assert evidence["vector_index_eligible"] is False
        assert evidence["raw_document_body_retained"] is False
        assert evidence["owner_role"] == "DATA_ARCHITECT"
        assert evidence["reviewer_role"] == "PRIVACY_STEWARD"
        assert not ({"content", "body", "raw_text"} & set(evidence))


def test_prohibited_evidence_and_substitution_controls_fail_closed():
    record = _load(AUTHORIZATION_PATH)
    prohibited = set(record["prohibited_evidence_classes"])
    substitution = record["controlled_substitution"]

    assert "PROPRIETARY_COTS_DOCUMENTATION" in prohibited
    assert "CLIENT_OR_PRODUCTION_DATA" in prohibited
    assert "PII_VALUES" in prohibited
    assert substitution["requires_exact_product_module_version"] is True
    assert substitution["requires_document_level_authorization"] is True
    assert substitution["cross_version_fallback_permitted"] is False
    assert substitution["simultaneous_scope_mixing_permitted"] is False
    assert substitution["real_vendor_claim_permitted_without_active_pack"] is False


def test_baseline_is_development_only_until_deferred_review_is_designed():
    record = _load(AUTHORIZATION_PATH)
    review_policy = record["review_policy"]

    assert record["status"] == "PROPOSED"
    assert record["build_status"] == "COMPLETE"
    assert record["development_use_active"] is True
    assert record["authoritative_use_active"] is False
    assert review_policy["status"] == "DEFERRED"
    assert review_policy["intermediate_human_review_required"] is False
    assert review_policy["all_generated_artifacts_remain_proposed"] is True
    assert review_policy["automatic_authoritative_promotion_permitted"] is False
    assert set(record["authoritative_activation_requirements"]) == {
        "HUMAN_REVIEW_WORKFLOW_DESIGNED",
        "REQUIRED_HUMAN_DECISIONS_RECORDED",
        "CONTENT_FINGERPRINT_VERIFIED",
    }
    assert record["development_decision"]["decided_by_role"] == "SPONSOR"
