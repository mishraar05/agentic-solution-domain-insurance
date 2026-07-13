"""Validate strict loading and provenance for federated ontology YAML."""

from copy import deepcopy
import os
from pathlib import Path
import shutil
import sys

import pytest
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from governed_knowledge_foundation.knowledge_pack_io import (  # noqa: E402
    KnowledgePackLoadError,
    fingerprint_pack,
    load_federated_ontology,
    load_knowledge_pack,
)


ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_ROOT = ROOT / "knowledge_packs" / "ontology"
DESCRIPTOR = ONTOLOGY_ROOT / "insurance_ontology_v1.yaml"


def _descriptor():
    return yaml.safe_load(DESCRIPTOR.read_text(encoding="utf-8"))


def test_federated_ontology_assembles_in_declared_domain_order():
    ontology, fingerprint = load_federated_ontology(DESCRIPTOR)

    assert ontology["domains"] == [
        "Policy",
        "Claims",
        "Billing",
        "Shared",
        "Risk",
        "Document",
        "Motor",
        "Home",
        "CommercialProperty",
        "Pensions",
    ]
    assert len(ontology["concepts"]) == 124
    assert sum(
        len(concept.get("relationships", []))
        for concept in ontology["concepts"]
    ) == 167
    assert len(fingerprint) == 64
    assert fingerprint_pack(DESCRIPTOR) == fingerprint
    concept_domains = [concept["domain"] for concept in ontology["concepts"]]
    assert concept_domains == sorted(
        concept_domains,
        key=ontology["domains"].index,
    )


def test_each_module_contains_only_its_declared_domain():
    descriptor = _descriptor()
    assert len(descriptor["module_files"]) == len(descriptor["domains"])
    for declaration in descriptor["module_files"]:
        module = load_knowledge_pack(
            ONTOLOGY_ROOT / declaration["path"]
        )
        assert module["domain"] == declaration["domain"]
        assert {concept["domain"] for concept in module["concepts"]} == {
            declaration["domain"]
        }


def test_cross_version_module_is_rejected(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    declaration = _descriptor()["module_files"][1]
    module_path = copied_root / declaration["path"]
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["pack_version"] = "9.9.9"
    module_path.write_text(
        yaml.safe_dump(module, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="pack_version"):
        load_federated_ontology(copied_descriptor)


def test_missing_module_is_rejected(tmp_path):
    descriptor = deepcopy(_descriptor())
    descriptor["module_files"][0]["path"] = "modules/missing.yaml"
    descriptor_path = tmp_path / "insurance_ontology_v1.yaml"
    descriptor_path.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="does not exist"):
        load_federated_ontology(descriptor_path)


def test_duplicate_module_domain_is_rejected(tmp_path):
    descriptor = deepcopy(_descriptor())
    descriptor["module_files"][1]["domain"] = "Policy"
    descriptor_path = tmp_path / "insurance_ontology_v1.yaml"
    descriptor_path.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="domains must be unique"):
        load_federated_ontology(descriptor_path)


def test_concept_in_the_wrong_domain_module_is_rejected(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    declaration = _descriptor()["module_files"][0]
    module_path = copied_root / declaration["path"]
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["concepts"][0]["domain"] = "Claims"
    module_path.write_text(
        yaml.safe_dump(module, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="outside Policy"):
        load_federated_ontology(copied_descriptor)


def test_module_path_cannot_escape_bundle(tmp_path):
    descriptor = deepcopy(_descriptor())
    descriptor["module_files"][0]["path"] = "../outside.yaml"
    descriptor_path = tmp_path / "insurance_ontology_v1.yaml"
    descriptor_path.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="escapes"):
        load_federated_ontology(descriptor_path)


def test_bundle_fingerprint_changes_when_a_module_changes(tmp_path):
    _, original = load_federated_ontology(DESCRIPTOR)
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    declaration = _descriptor()["module_files"][0]
    module_path = copied_root / declaration["path"]
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["description"] += " Clarified."
    module_path.write_text(
        yaml.safe_dump(module, sort_keys=False),
        encoding="utf-8",
    )

    _, changed = load_federated_ontology(copied_descriptor)
    assert changed != original


def test_duplicate_controlled_vocabulary_is_rejected(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    descriptor = _descriptor()
    vocab_path = copied_root / descriptor["vocabulary_files"][0]["path"]
    vocab_module = yaml.safe_load(vocab_path.read_text(encoding="utf-8"))
    vocab_module["controlled_vocabularies"].append(
        deepcopy(vocab_module["controlled_vocabularies"][0])
    )
    vocab_path.write_text(
        yaml.safe_dump(vocab_module, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="vocabulary IDs"):
        load_federated_ontology(copied_descriptor)


def test_reference_shape_with_unknown_concept_is_rejected(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    descriptor = _descriptor()
    vocab_path = copied_root / descriptor["vocabulary_files"][1]["path"]
    vocab_module = yaml.safe_load(vocab_path.read_text(encoding="utf-8"))
    vocab_module["reference_shapes"][0]["optional_concept_ids"].append(
        "Home.UnknownConcept"
    )
    vocab_path.write_text(
        yaml.safe_dump(vocab_module, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="unavailable concepts"):
        load_federated_ontology(copied_descriptor)


def test_each_vocabulary_file_contains_only_its_declared_domain():
    descriptor = _descriptor()
    for declaration in descriptor["vocabulary_files"]:
        module = load_knowledge_pack(
            ONTOLOGY_ROOT / declaration["path"]
        )
        assert module["domain"] == declaration["domain"]
        assert module["pack_id"] == descriptor["pack_id"]
        assert module["pack_version"] == descriptor["pack_version"]
        assert module["status"] == descriptor["status"]


def test_missing_vocabulary_file_is_rejected(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    descriptor = _descriptor()
    descriptor["vocabulary_files"][0]["path"] = "insurance_modules/missing.yaml"
    copied_descriptor.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="vocabulary file does not exist"):
        load_federated_ontology(copied_descriptor)


def test_vocabulary_file_domain_must_be_declared(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    descriptor = _descriptor()
    descriptor["vocabulary_files"][0]["domain"] = "NotADomain"
    copied_descriptor.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(KnowledgePackLoadError, match="not a declared ontology domain"):
        load_federated_ontology(copied_descriptor)


def test_duplicate_vocabulary_file_domain_is_rejected(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    descriptor = _descriptor()
    descriptor["vocabulary_files"].append(deepcopy(descriptor["vocabulary_files"][0]))
    copied_descriptor.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(
        KnowledgePackLoadError, match="vocabulary_files domains must be unique"
    ):
        load_federated_ontology(copied_descriptor)


def test_vocabulary_files_are_optional(tmp_path):
    copied_root = tmp_path / "ontology"
    shutil.copytree(ONTOLOGY_ROOT, copied_root)
    copied_descriptor = copied_root / DESCRIPTOR.name
    descriptor = _descriptor()
    del descriptor["vocabulary_files"]
    copied_descriptor.write_text(
        yaml.safe_dump(descriptor, sort_keys=False),
        encoding="utf-8",
    )

    ontology, _ = load_federated_ontology(copied_descriptor)
    assert "controlled_vocabularies" not in ontology
    assert "reference_shapes" not in ontology
