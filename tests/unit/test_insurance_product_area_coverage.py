"""Validate governed coverage of Motor, Home, Commercial Property, and Pensions."""

import os
from pathlib import Path
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from governed_knowledge_foundation.knowledge_pack_io import (  # noqa: E402
    load_federated_ontology,
    load_knowledge_pack,
)


ROOT = Path(__file__).resolve().parents[2]
PACK_DIR = ROOT / "knowledge_packs"
ONTOLOGY_PATH = PACK_DIR / "ontology" / "insurance_ontology_v1.yaml"

# Concept IDs from the retired pnc_ontology/1.1.0 pack (Policy, Claims, Billing,
# Shared domains). insurance_ontology/1.0.0 superseded that pack; this frozen
# set guards against any of those stable IDs being renamed or dropped now that
# the legacy pack no longer exists on disk to diff against.
LEGACY_PNC_CONCEPT_IDS = frozenset({
    "Billing.Account",
    "Billing.Balance",
    "Billing.Charge",
    "Billing.Delinquency",
    "Billing.Disbursement",
    "Billing.Installment",
    "Billing.Invoice",
    "Billing.Payment",
    "Billing.PaymentPlan",
    "Claim.Adjuster",
    "Claim.CatastropheCode",
    "Claim.CauseOfLoss",
    "Claim.Claim",
    "Claim.Claimant",
    "Claim.ClaimedAmount",
    "Claim.ClosedDate",
    "Claim.Exposure",
    "Claim.Identifier",
    "Claim.IncurredLoss",
    "Claim.LAE",
    "Claim.Litigation",
    "Claim.LossDate",
    "Claim.LossEvent",
    "Claim.Payment",
    "Claim.PaymentType",
    "Claim.Recovery",
    "Claim.ReportedDate",
    "Claim.Reserve",
    "Claim.ReserveType",
    "Claim.Status",
    "Coverage.Deductible",
    "Coverage.Limit",
    "Party.Identifier",
    "Party.Type",
    "Policy.Commission",
    "Policy.EarnedPremium",
    "Policy.EffectiveDate",
    "Policy.Endorsement",
    "Policy.ExpirationDate",
    "Policy.Identifier",
    "Policy.InsuredObject",
    "Policy.PoliciesInForce",
    "Policy.Policy",
    "Policy.PolicyNumber",
    "Policy.PolicyTerm",
    "Policy.PolicyTransaction",
    "Policy.Quote",
    "Policy.RatingFactor",
    "Policy.Renewal",
    "Policy.Status",
    "Policy.TransactionType",
    "Policy.UnearnedPremium",
    "Policy.WrittenPremium",
    "Product.Code",
    "Shared.Coverage",
    "Shared.Dwelling",
    "Shared.Insured",
    "Shared.LineOfBusiness",
    "Shared.Location",
    "Shared.Party",
    "Shared.Producer",
    "Shared.Product",
    "Shared.Vehicle",
    "Technical.SourceUpdatedTimestamp",
})

PRODUCT_AREAS = {
    "MOTOR": {
        "domain": "Motor",
        "lobs": {"PERS_AUTO", "COMM_AUTO", "MOTORCYCLE_RV"},
        "concept_count": 10,
        "vocabulary_prefix": "MOTOR_",
        "shape_prefix": "MOTOR_",
    },
    "HOME": {
        "domain": "Home",
        "lobs": {"HOMEOWNERS", "RENTERS_CONDO", "DWELLING_FIRE"},
        "concept_count": 10,
        "vocabulary_prefix": "HOME_",
        "shape_prefix": "HOME_",
    },
    "COMMERCIAL_PROPERTY": {
        "domain": "CommercialProperty",
        "lobs": {"COMM_PROPERTY", "BOP"},
        "concept_count": 11,
        "vocabulary_prefix": "COMMERCIAL_PROPERTY_",
        "shape_prefix": "COMMERCIAL_PROPERTY_",
    },
    "PENSIONS": {
        "domain": "Pensions",
        "lobs": {"PENSIONS"},
        "concept_count": 13,
        "vocabulary_prefix": "PENSIONS_",
        "shape_prefix": "PENSION_",
    },
}


def _ontology():
    return load_federated_ontology(ONTOLOGY_PATH)[0]


def _lob_ids():
    pnc = load_knowledge_pack(
        PACK_DIR / "lob_taxonomy" / "pnc_lob_taxonomy_v1.yaml"
    )
    pensions = load_knowledge_pack(
        PACK_DIR / "lob_taxonomy" / "pensions_taxonomy_v1.yaml"
    )
    return {
        item["lob_id"]
        for pack in (pnc, pensions)
        for item in pack["lines_of_business"]
    }


def test_all_four_product_areas_have_concepts_vocabularies_and_shapes():
    ontology = _ontology()
    declared = {
        area["product_area_id"]: area
        for area in ontology["product_areas"]
    }
    vocabularies = ontology["controlled_vocabularies"]
    shapes = ontology["reference_shapes"]

    assert set(declared) == set(PRODUCT_AREAS)
    for area_id, expected in PRODUCT_AREAS.items():
        area = declared[area_id]
        assert area["domain"] == expected["domain"]
        assert set(area["line_of_business_ids"]) == expected["lobs"]
        assert sum(
            concept["domain"] == expected["domain"]
            for concept in ontology["concepts"]
        ) == expected["concept_count"]
        assert any(
            item["vocabulary_id"].startswith(expected["vocabulary_prefix"])
            for item in vocabularies
        )
        assert any(
            item["shape_id"].startswith(expected["shape_prefix"])
            for item in shapes
        )


def test_every_product_area_lob_resolves_to_a_governed_taxonomy():
    available = _lob_ids()
    requested = {
        lob
        for area in _ontology()["product_areas"]
        for lob in area["line_of_business_ids"]
    }
    assert requested <= available


def test_existing_pnc_concept_ids_are_preserved_in_broader_ontology():
    current_ids = {concept["concept_id"] for concept in _ontology()["concepts"]}
    assert LEGACY_PNC_CONCEPT_IDS <= current_ids


def test_pensions_remains_isolated_from_pnc_transaction_domains():
    prohibited_prefixes = ("Policy.", "Claim.", "Billing.", "Motor.", "Home.")
    pensions = [
        concept for concept in _ontology()["concepts"]
        if concept["domain"] == "Pensions"
    ]
    assert pensions
    for concept in pensions:
        for relationship in concept.get("relationships", []):
            assert not relationship["target"].startswith(prohibited_prefixes)


def test_controlled_vocabularies_are_nonempty_and_unique():
    vocabularies = _ontology()["controlled_vocabularies"]
    ids = [item["vocabulary_id"] for item in vocabularies]
    assert len(ids) == len(set(ids))
    for item in vocabularies:
        assert item["name"]
        assert item["values"]
        assert len(item["values"]) == len(set(item["values"]))
        assert item["steward_note"]


def test_synthetic_examples_resolve_without_sensitive_values():
    concepts_by_id = {
        concept["concept_id"]: concept for concept in _ontology()["concepts"]
    }
    expected_areas = set(PRODUCT_AREAS)
    observed_areas = set()
    for path in sorted((ROOT / "examples" / "ontology").glob("*_example_v1.yaml")):
        example = yaml.safe_load(path.read_text(encoding="utf-8"))
        observed_areas.add(example["product_area"])
        assert example["classification"] == "SYNTHETIC_NON_PERSONAL_EXAMPLE"
        assert example["ontology_pack"] == "insurance_ontology/1.0.0"
        assert all(
            item["concept_id"] in concepts_by_id
            for item in example["concept_instances"]
        )
        assert all(
            item["synthetic_reference"].startswith("SYNTHETIC_")
            for item in example["concept_instances"]
        )
        for item in example["concept_instances"]:
            concept = concepts_by_id[item["concept_id"]]
            if concept["privacy_sensitivity"] == "DIRECT":
                assert "sample_instance" not in item, (
                    f"{path.name}: DIRECT concept {item['concept_id']} must not "
                    "carry a sample_instance"
                )
    assert observed_areas == expected_areas


def test_mapping_templates_enforce_recommendation_only_unresolved_behavior():
    paths = [
        PACK_DIR / "mapping_templates" / "source_to_ontology_v1.yaml",
        PACK_DIR / "mapping_templates" / "document_term_to_ontology_v1.yaml",
    ]
    for path in paths:
        pack = load_knowledge_pack(path)
        assert pack["status"] == "PROPOSED"
        assert pack["template"]["proposed_concept_id"] is None
        assert pack["template"]["candidate_concept_ids"] == []
        assert pack["template"]["approval_state"] == "PROPOSED"
        assert pack["rules"]
