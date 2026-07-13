"""Validate governed knowledge-pack integrity and cross-references."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from governed_knowledge_foundation.knowledge_pack_io import (  # noqa: E402
    load_federated_ontology,
    load_knowledge_pack,
)

PACK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_packs")


def _load(rel):
    return load_knowledge_pack(os.path.join(PACK_DIR, rel))


def _ontology_ids():
    return {
        c["concept_id"]
        for c in _load("ontology/insurance_ontology_v1.yaml")["concepts"]
    }


class TestOntologyPack:
    def test_federated_yaml_is_the_only_registered_canonical_representation(self):
        yaml_path = os.path.join(
            PACK_DIR, "ontology", "insurance_ontology_v1.yaml"
        )
        json_path = os.path.join(
            PACK_DIR, "ontology", "insurance_ontology_v1.json"
        )
        manifest = _load("manifest.json")
        entry = next(
            item for item in manifest["packs"]
            if item["pack_id"] == "insurance_ontology"
        )

        assert os.path.isfile(yaml_path)
        assert not os.path.exists(json_path)
        assert entry["path"] == "ontology/insurance_ontology_v1.yaml"
        _, bundle_fingerprint = load_federated_ontology(yaml_path)
        assert bundle_fingerprint == entry["content_sha256"]

    def test_loads_with_unique_concept_ids(self):
        pack = _load("ontology/insurance_ontology_v1.yaml")
        ids = [c["concept_id"] for c in pack["concepts"]]
        assert len(ids) == len(set(ids))
        assert len(ids) == 124
        assert sum(
            len(concept.get("relationships", []))
            for concept in pack["concepts"]
        ) == 167
        assert pack["status"] == "PROPOSED"

    def test_relationship_targets_resolve(self):
        pack = _load("ontology/insurance_ontology_v1.yaml")
        ids = {c["concept_id"] for c in pack["concepts"]}
        for concept in pack["concepts"]:
            for rel in concept.get("relationships", []):
                assert rel["target"] in ids, f"{concept['concept_id']} -> {rel['target']}"

    def test_domains_are_declared(self):
        pack = _load("ontology/insurance_ontology_v1.yaml")
        for concept in pack["concepts"]:
            assert concept["domain"] in pack["domains"]

    def test_classifier_concepts_present(self):
        """Pack-driven classifier results must resolve to ontology concepts."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
        from source_intelligence.knowledge_classifier import classify_naming_kb
        ids = _ontology_ids()
        for table, column in (("POLMAST", "POLNBR"), ("CLMMAST", "CLMSTS")):
            concept_id = classify_naming_kb(table, column)["ontology_concept_id"]
            assert concept_id in ids, f"classifier concept {concept_id} missing from ontology"


class TestCotsPack:
    def test_all_mappings_resolve_to_ontology(self):
        pack = _load("cots_reference/cots_like_reference_v1.json")
        ids = _ontology_ids()
        for module in pack["modules"]:
            for table in module["tables"]:
                assert table["maps_to_concept"] in ids, table["table"]
                for column in table["columns"]:
                    assert column["maps_to_concept"] in ids, f"{table['table']}.{column['column']}"

    def test_declares_vendor_neutrality(self):
        pack = _load("cots_reference/cots_like_reference_v1.json")
        assert "NOT derived" in pack["description"]


class TestKpiCatalog:
    def test_unique_ids_and_required_fields(self):
        pack = _load("kpi_catalog/pnc_kpi_catalog_v1.json")
        ids = [k["kpi_id"] for k in pack["kpis"]]
        assert len(ids) == len(set(ids))
        for kpi in pack["kpis"]:
            for field in ("name", "definition", "formula", "required_concepts", "typical_grain", "direction"):
                assert kpi.get(field), f"{kpi['kpi_id']} missing {field}"

    def test_required_concepts_resolve_to_ontology(self):
        pack = _load("kpi_catalog/pnc_kpi_catalog_v1.json")
        ids = _ontology_ids()
        for kpi in pack["kpis"]:
            for concept in kpi["required_concepts"]:
                assert concept in ids, f"{kpi['kpi_id']} -> {concept}"

    def test_core_underwriting_kpis_present(self):
        names = {k["kpi_id"] for k in _load("kpi_catalog/pnc_kpi_catalog_v1.json")["kpis"]}
        for required in ("KPI.LossRatio", "KPI.CombinedRatio", "KPI.ClaimsFrequency",
                         "KPI.ClaimsSeverity", "KPI.RetentionRate", "KPI.EarnedPremium"):
            assert required in names


class TestManifest:
    def test_manifest_lists_existing_packs_with_matching_versions(self):
        manifest = _load("manifest.json")
        assert manifest["packs"], "manifest must list packs"
        for entry in manifest["packs"]:
            pack = _load(entry["path"])
            assert pack["pack_id"] == entry["pack_id"]
            assert pack["pack_version"] == entry["pack_version"]
            assert pack["status"] == entry["status"]

    def test_rule_packs_declare_resolvable_capabilities_and_selection(self):
        manifest = _load("manifest.json")
        rules = [entry for entry in manifest["packs"] if "capability" in entry]
        assert {entry["capability"] for entry in rules} == {
            "naming", "privacy", "type"
        }
        for entry in rules:
            pack = _load(entry["path"])
            assert pack["selection"]["source_systems"]
            assert pack["selection"]["effective_date"]


class TestLobTaxonomy:
    def test_loads_with_unique_lob_ids(self):
        pack = _load("lob_taxonomy/pnc_lob_taxonomy_v1.yaml")
        ids = [l["lob_id"] for l in pack["lines_of_business"]]
        assert len(ids) == len(set(ids)) and len(ids) >= 18
        assert pack["status"] == "PROPOSED"

    def test_every_lob_references_declared_segment(self):
        pack = _load("lob_taxonomy/pnc_lob_taxonomy_v1.yaml")
        segments = {s["segment_id"] for s in pack["segments"]}
        for lob in pack["lines_of_business"]:
            assert lob["segment"] in segments, lob["lob_id"]

    def test_every_lob_has_operational_details(self):
        pack = _load("lob_taxonomy/pnc_lob_taxonomy_v1.yaml")
        for lob in pack["lines_of_business"]:
            for field in ("name", "description", "typical_products", "typical_coverages", "naic_line_names"):
                assert lob.get(field), f"{lob['lob_id']} missing {field}"

    def test_taxonomy_anchored_to_ontology(self):
        pack = _load("lob_taxonomy/pnc_lob_taxonomy_v1.yaml")
        assert pack["ontology_concept"] in _ontology_ids()
