"""Tests: pack-driven classification, including AS400-style abbreviated names."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from source_intelligence.knowledge_classifier import (
    RulePackResolutionError, active_pack_versions, classify_naming_kb,
    classify_privacy_kb, check_type_compatibility_kb, resolve_rule_pack,
    segment_column_name, segment_column_name_hypotheses, load_pack,
)

EXP = load_pack("rule_packs/naming_rules_v1.yaml")["token_expansions"]


def test_active_pack_versions_come_from_manifest():
    versions = active_pack_versions({"pnc_ontology", "naming_rules"})
    assert versions == {"pnc_ontology": "1.1.0", "naming_rules": "1.1.0"}


def _write_resolver_fixture(root, definitions):
    packs = []
    for definition in definitions:
        path = f"{definition['pack_id']}.json"
        payload = {
            "pack_id": definition["pack_id"],
            "pack_version": "1.0.0",
            "selection": definition["selection"],
        }
        (root / path).write_text(json.dumps(payload), encoding="utf-8")
        packs.append({
            "pack_id": definition["pack_id"],
            "pack_version": "1.0.0",
            "path": path,
            "capability": "naming",
            "priority": definition.get("priority", 0),
        })
    (root / "manifest.json").write_text(
        json.dumps({"packs": packs}), encoding="utf-8"
    )


def test_resolver_prefers_source_specific_pack(tmp_path):
    _write_resolver_fixture(tmp_path, [
        {"pack_id": "base", "selection": {
            "source_systems": ["*"], "naming_conventions": ["snake_case"],
            "effective_date": "2026-01-01"}},
        {"pack_id": "customer", "selection": {
            "source_systems": ["customer_a"],
            "naming_conventions": ["snake_case"],
            "effective_date": "2026-01-01"}},
    ])
    result = resolve_rule_pack(
        "naming", "customer_a", "snake_case", "2026-07-13", tmp_path
    )
    assert result["pack"]["pack_id"] == "customer"


def test_resolver_fails_closed_on_equal_precedence(tmp_path):
    selection = {
        "source_systems": ["*"], "naming_conventions": ["snake_case"],
        "effective_date": "2026-01-01",
    }
    _write_resolver_fixture(tmp_path, [
        {"pack_id": "one", "selection": selection},
        {"pack_id": "two", "selection": selection},
    ])
    with pytest.raises(RulePackResolutionError, match="Ambiguous"):
        resolve_rule_pack(
            "naming", "source", "snake_case", "2026-07-13", tmp_path
        )


class TestSegmentation:
    def test_as400_continuous_names_segment(self):
        assert segment_column_name("POLNBR", EXP)[0] == ["policy", "number"]
        assert segment_column_name("CLMSTS", EXP)[0] == ["claim", "status"]
        assert segment_column_name("EFFDT", EXP)[0] == ["effective", "date"]

    def test_snake_case_with_abbreviations(self):
        tokens, rules = segment_column_name("pol_eff_dt", EXP)
        assert tokens == ["policy", "effective", "date"]
        assert len(rules) == 3  # provenance per token

    def test_unknown_tokens_pass_through(self):
        assert "gadget" in segment_column_name("gadget_cd", EXP)[0]

    def test_ambiguous_token_retains_every_hypothesis(self):
        hypotheses = segment_column_name_hypotheses("EXPAMT", EXP)
        assert {"expiration amount", "expense amount", "exposure amount"} == {
            " ".join(item["tokens"]) for item in hypotheses
        }
        assert all(item["ambiguous_tokens"] == ["EXP"] for item in hypotheses)


class TestNamingClassification:
    def test_as400_polnbr_resolves_to_policy_number(self):
        result = classify_naming_kb("POLMAST", "POLNBR")
        assert result["ontology_concept_id"] == "Policy.PolicyNumber"
        assert result["naming_strength"] >= 0.70
        assert result["provenance"], "every inference carries rule provenance"

    def test_as400_clmsts_resolves_to_claim_status(self):
        result = classify_naming_kb("CLMMAST", "CLMSTS")
        assert result["ontology_concept_id"] == "Claim.Status"
        assert result["domain"] == "Claims"

    def test_variant_exact_match_beats_everything(self):
        result = classify_naming_kb("bronze_policy", "policy_number")
        assert result["ontology_concept_id"] == "Policy.PolicyNumber"
        assert result["naming_strength"] == 0.95

    def test_unknown_column_is_unresolved_not_invented(self):
        result = classify_naming_kb("t", "widget_flavor")
        assert result["ontology_concept_id"] is None
        assert result["naming_strength"] <= 0.40
        assert "review" in result["reason"]

    def test_ambiguous_abbreviation_fails_closed(self):
        result = classify_naming_kb("CLMMAST", "EXPAMT")
        assert result["ontology_concept_id"] is None
        assert result["naming_contradicted"] is True
        assert result["requires_semantic_mapper"] is True
        assert "EXP" in result["contradictions"]

    def test_provenance_names_pack_and_rules(self):
        result = classify_naming_kb("POLMAST", "POLNBR")
        packs = {p["rule_pack_id"] for p in result["provenance"]}
        assert packs == {"naming_rules"}
        assert all("rule_id" in p and "rule_version" in p for p in result["provenance"])


class TestPrivacyClassification:
    def test_as400_dob_detected(self):
        cls, _, prov = classify_privacy_kb("INSDDOB")
        assert cls == "PERSONAL_DATA" and prov[0]["rule_id"] == "PR002"

    def test_risk_address_exception_stays_internal(self):
        cls, rationale, prov = classify_privacy_kb("risk_address")
        assert cls == "INTERNAL" and prov[0]["rule_id"] == "PX001"

    def test_person_address_is_personal(self):
        cls, _, _ = classify_privacy_kb("mailing_address")
        assert cls == "PERSONAL_DATA"

    def test_narrative_is_sensitive(self):
        cls, _, _ = classify_privacy_kb("loss_narrative")
        assert cls == "SENSITIVE"

    def test_default_internal_with_provenance(self):
        cls, _, prov = classify_privacy_kb("claim_status")
        assert cls == "INTERNAL" and prov[0]["rule_id"] == "PR999"


class TestTypeCompatibility:
    def test_measure_numeric_matches(self):
        strength, prov = check_type_compatibility_kb("DecimalType(12,2)", "MEASURE")
        assert strength == 0.85 and prov[0]["rule_pack_id"] == "type_rules"

    def test_measure_as_boolean_mismatch(self):
        strength, _ = check_type_compatibility_kb("BooleanType()", "MEASURE")
        assert strength == 0.30

    def test_date_stored_as_string_tolerated(self):
        strength, _ = check_type_compatibility_kb("StringType()", "DATE")
        assert strength == 0.55
