"""Unit tests for deterministic Source Intelligence core."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.naming import classify_naming, detect_personal_data
from source_intelligence.types import check_type_compatibility
from source_intelligence.privacy import classify_privacy
from source_intelligence.relationships import (
    compute_relationship_strength,
    discover_relationship_candidates,
    infer_key_role,
    infer_key_roles,
    relationship_evidence_by_attribute,
)
from source_intelligence.confidence import compute_confidence, EVIDENCE_COVERAGE_FLOOR
from source_intelligence.routing import route_review


class TestNamingClassification:
    def test_exact_match_policy_id(self):
        name, concept, domain, strength, reason = classify_naming("bronze_policy", "policy_id")
        assert name == "Policy Identifier"
        assert concept == "Policy.Identifier"
        assert domain == "Policy"
        assert strength == 0.95

    def test_exact_match_claim_id(self):
        name, concept, domain, strength, reason = classify_naming("bronze_claim", "claim_id")
        assert name == "Claim Identifier"
        assert concept == "Claim.Identifier"
        assert domain == "Claims"
        assert strength == 0.95

    def test_unknown_column(self):
        name, concept, domain, strength, reason = classify_naming("bronze_policyholder", "display_name")
        assert concept is None
        assert domain == "Shared"
        assert strength == 0.55

    def test_personal_data_detection(self):
        assert detect_personal_data("display_name") is True
        assert detect_personal_data("email_address") is True
        assert detect_personal_data("policy_id") is False


class TestTypeCompatibility:
    def test_date_type_for_date_field(self):
        assert check_type_compatibility("DateType()", "effective_date") == 0.8

    def test_string_type_for_id_field(self):
        assert check_type_compatibility("StringType()", "policy_id") == 0.8

    def test_unknown_type(self):
        assert check_type_compatibility("UnknownType()", "some_column") == 0.4


class TestPrivacyClassification:
    def test_personal_data(self):
        privacy_class, rationale = classify_privacy("display_name")
        assert privacy_class == "PERSONAL_DATA"
        assert "personal-data" in rationale

    def test_internal_data(self):
        privacy_class, rationale = classify_privacy("policy_id")
        assert privacy_class == "INTERNAL"


class TestRelationshipInference:
    def test_core_relationship_engine_has_no_fixture_table_inventory(self):
        root = os.path.join(os.path.dirname(__file__), "..", "..")
        paths = [
            os.path.join(root, "src", "source_intelligence", "relationships.py"),
            os.path.join(
                root,
                "src",
                "workflows",
                "source_intelligence",
                "02_build_source_dictionary.py",
            ),
            os.path.join(
                root,
                "src",
                "workflows",
                "source_intelligence",
                "05_validate_source_intelligence.py",
            ),
        ]
        forbidden = ("bronze_policy", "bronze_claim", "bronze_policyholder")
        for path in paths:
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            assert not any(name in source for name in forbidden), path

    def test_table_wide_key_roles_use_runtime_columns(self):
        roles = infer_key_roles(
            "raw_customer",
            ["customer_id", "account_id", "customer_status"],
        )
        assert roles["customer_id"] == "PRIMARY_KEY_CANDIDATE"
        assert roles["account_id"] == "FOREIGN_KEY_CANDIDATE"
        assert roles["customer_status"] == "NON_KEY"

    def test_non_key(self):
        assert infer_key_role("arbitrary_file", "record_status") == "NON_KEY"

    def test_relationships_are_discovered_from_runtime_metadata(self):
        attributes = [
            {
                "source_table": "raw_customer",
                "source_column": "customer_id",
                "physical_type": "StringType()",
                "key_role": "PRIMARY_KEY_CANDIDATE",
            },
            {
                "source_table": "raw_order",
                "source_column": "order_id",
                "physical_type": "StringType()",
                "key_role": "PRIMARY_KEY_CANDIDATE",
            },
            {
                "source_table": "raw_order",
                "source_column": "customer_id",
                "physical_type": "StringType()",
                "key_role": "FOREIGN_KEY_CANDIDATE",
            },
        ]
        candidates = discover_relationship_candidates(attributes)
        assert len(candidates) == 1
        assert candidates[0]["from_table"] == "raw_order"
        assert candidates[0]["to_table"] == "raw_customer"
        evidence = relationship_evidence_by_attribute(candidates)
        assert "raw_order.customer_id" in evidence[("raw_order", "customer_id")]

    def test_unrecognized_as400_names_remain_unresolved_without_failure(self):
        roles = infer_key_roles("LIBFILE", ["POLNBR", "CLMSTS", "EFFDT"])
        assert set(roles.values()) == {"NON_KEY"}
        attributes = [
            {
                "source_table": "LIBFILE",
                "source_column": name,
                "physical_type": "StringType()",
                "key_role": role,
            }
            for name, role in roles.items()
        ]
        assert discover_relationship_candidates(attributes) == []

    def test_relationship_strength(self):
        assert compute_relationship_strength("any_child", "parent_id", True) == 0.9
        assert compute_relationship_strength("any_table", "status", False) == 0.4


class TestConfidenceCalculation:
    def test_all_components_available(self):
        result = compute_confidence(naming_strength=0.95, type_strength=0.8, relationship_strength=0.4, cots_match_strength=0.5, standard_consistency=0.7)
        assert result.evidence_coverage == 1.0
        assert 0.5 < result.score < 1.0
        assert result.formula_version == "1.0.0"

    def test_cots_not_available(self):
        result = compute_confidence(naming_strength=0.95, type_strength=0.8, relationship_strength=0.4, cots_match_strength=None, standard_consistency=0.7)
        assert result.components["cots_match_strength"]["availability"] == "NOT_AVAILABLE"
        assert result.evidence_coverage < 1.0
        assert result.evidence_coverage >= EVIDENCE_COVERAGE_FLOOR

    def test_multiple_unavailable(self):
        result = compute_confidence(naming_strength=0.55, type_strength=0.5, relationship_strength=0.4, cots_match_strength=None, standard_consistency=None)
        assert result.components["cots_match_strength"]["availability"] == "NOT_AVAILABLE"
        assert result.components["standard_consistency"]["availability"] == "NOT_AVAILABLE"
        # 3 of 5 components available = 0.80 coverage, which is above the 0.60 floor
        assert result.evidence_coverage == 0.8
        assert result.evidence_coverage >= EVIDENCE_COVERAGE_FLOOR
        # Score should be lower than if all components were available
        assert result.score < 0.6

    def test_reproducibility(self):
        kwargs = dict(naming_strength=0.9, type_strength=0.8, relationship_strength=0.9, cots_match_strength=0.5, standard_consistency=0.7)
        result1 = compute_confidence(**kwargs)
        result2 = compute_confidence(**kwargs)
        assert result1.score == result2.score
        assert result1.evidence_coverage == result2.evidence_coverage

    def test_contradicted_component_is_retained_but_not_scored(self):
        result = compute_confidence(
            naming_strength=0.95,
            type_strength=0.8,
            relationship_strength=0.4,
            cots_match_strength=0.5,
            standard_consistency=0.7,
            relationship_contradicted=True,
        )
        component = result.components["relationship_strength"]
        assert component["availability"] == "CONTRADICTED"
        assert component["value"] == 0.4
        assert result.evidence_coverage == 0.75
        assert "require review" in result.confidence_reason


class TestReviewRouting:
    def test_privacy_routes_to_privacy_steward(self):
        result = route_review(confidence_score=0.95, evidence_coverage=1.0, privacy_class="PERSONAL_DATA", relationship_evidence=None, ontology_concept_id="Party.Identifier", key_role="NON_KEY", contradictions=None)
        assert result["recommended_reviewer_role"] == "PRIVACY_STEWARD"
        assert "Privacy" in result["review_reason"]

    def test_relationship_routes_to_architect(self):
        result = route_review(confidence_score=0.95, evidence_coverage=1.0, privacy_class="INTERNAL", relationship_evidence="some relationship", ontology_concept_id="Policy.Identifier", key_role="FOREIGN_KEY_CANDIDATE", contradictions=None)
        assert result["recommended_reviewer_role"] == "DATA_ARCHITECT"

    def test_low_confidence_routes_to_steward(self):
        result = route_review(confidence_score=0.55, evidence_coverage=1.0, privacy_class="INTERNAL", relationship_evidence=None, ontology_concept_id=None, key_role="NON_KEY", contradictions=None)
        assert result["recommended_reviewer_role"] == "DOMAIN_STEWARD"

    def test_no_review_needed(self):
        result = route_review(confidence_score=0.95, evidence_coverage=1.0, privacy_class="INTERNAL", relationship_evidence=None, ontology_concept_id="Policy.Identifier", key_role="NON_KEY", contradictions=None)
        assert result["review_reason"] is None

    def test_low_evidence_coverage_routes_to_steward(self):
        result = route_review(confidence_score=0.95, evidence_coverage=0.40, privacy_class="INTERNAL", relationship_evidence=None, ontology_concept_id="Policy.Identifier", key_role="NON_KEY", contradictions=None)
        assert result["recommended_reviewer_role"] == "DOMAIN_STEWARD"
        assert "coverage" in result["review_reason"].lower()


class TestLabelledSet:
    def test_labelled_set_loads(self):
        import json
        labelled_path = os.path.join(os.path.dirname(__file__), "..", "..", "evals", "labelled_set", "source_attributes_v1.json")
        with open(labelled_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["schema_version"] == "1.0.0"
        assert data["set_name"] == "source_attributes_v1"
        assert len(data["records"]) == 19

    def test_labelled_set_has_strata(self):
        import json
        labelled_path = os.path.join(os.path.dirname(__file__), "..", "..", "evals", "labelled_set", "source_attributes_v1.json")
        with open(labelled_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for record in data["records"]:
            assert "strata" in record
            assert "domain" in record["strata"]
            assert "privacy" in record["strata"]
            assert "ambiguity" in record["strata"]


class TestProhibitedEvidence:
    FORBIDDEN_SENTINEL = "FORBIDDEN_TEST_SENTINEL"

    def test_sentinel_not_in_naming(self):
        from source_intelligence.naming import EXACT_MATCHES, PII_TOKENS
        for key, val in EXACT_MATCHES.items():
            assert self.FORBIDDEN_SENTINEL not in key
            assert self.FORBIDDEN_SENTINEL not in str(val)
        for token in PII_TOKENS:
            assert self.FORBIDDEN_SENTINEL not in token

    def test_sentinel_not_in_confidence(self):
        from source_intelligence.confidence import WEIGHTS, FORMULA_VERSION
        assert self.FORBIDDEN_SENTINEL not in FORMULA_VERSION
        for key in WEIGHTS:
            assert self.FORBIDDEN_SENTINEL not in key


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
