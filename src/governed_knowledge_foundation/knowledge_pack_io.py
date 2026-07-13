"""Load standalone and federated governed knowledge packs safely.

Most knowledge packs are one JSON or YAML document. The insurance ontology is
larger and maintained by multiple domain stewards, so its canonical YAML is a
federated bundle: one root descriptor references one concept module per
governed domain, plus an optional vocabulary module for domains that declare
controlled vocabularies or logical reference shapes. This module assembles
that bundle into the same in-memory shape used by classifiers and normalizers
while preserving exact pack identity.

Federation is deliberately strict. Module paths must remain beneath the root
ontology directory, declared concept-module domains must be covered exactly
once, and every module must repeat the root pack ID, version, status, and its
declared domain. Vocabulary modules are optional and may cover any subset of
the declared domains. The bundle fingerprint includes the relative path and
exact bytes of the root and every ordered module (concept and vocabulary),
making any content or module-layout change visible to provenance checks.
"""

import hashlib
import json
from pathlib import Path

import yaml


FEDERATED_ONTOLOGY_FORMAT = "FEDERATED_ONTOLOGY"


class KnowledgePackLoadError(ValueError):
    """Raised when a governed pack cannot be assembled without ambiguity."""


def _read_serialized(path):
    suffix = path.suffix.casefold()
    with path.open("r", encoding="utf-8") as handle:
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(handle)
        elif suffix == ".json":
            data = json.load(handle)
        else:
            raise KnowledgePackLoadError(
                f"Unsupported knowledge-pack format: {path.name}"
            )
    if not isinstance(data, dict):
        raise KnowledgePackLoadError(
            f"Knowledge pack must contain one object: {path}"
        )
    return data


def _resolve_bundle_path(root_dir, relative_path, label):
    candidate = (root_dir / relative_path).resolve()
    try:
        candidate.relative_to(root_dir)
    except ValueError as exc:
        raise KnowledgePackLoadError(
            f"{label} escapes the governed bundle: {relative_path}"
        ) from exc
    return candidate


def _federated_module_paths(root_path, descriptor):
    root_dir = root_path.parent.resolve()
    declarations = descriptor.get("module_files")
    if not isinstance(declarations, list) or not declarations:
        raise KnowledgePackLoadError(
            "Federated ontology requires a non-empty module_files list"
        )

    paths = []
    declared_domains = []
    for index, declaration in enumerate(declarations):
        if not isinstance(declaration, dict):
            raise KnowledgePackLoadError(
                f"module_files[{index}] must be an object"
            )
        domain = declaration.get("domain")
        relative_path = declaration.get("path")
        if not domain or not relative_path:
            raise KnowledgePackLoadError(
                f"module_files[{index}] requires domain and path"
            )
        candidate = _resolve_bundle_path(root_dir, relative_path, "Ontology module")
        declared_domains.append(domain)
        paths.append((domain, candidate))

    if len(declared_domains) != len(set(declared_domains)):
        raise KnowledgePackLoadError(
            "Federated ontology module domains must be unique"
        )
    if declared_domains != descriptor.get("domains"):
        raise KnowledgePackLoadError(
            "Federated ontology modules must exactly follow declared domain order"
        )
    return paths


def _federated_vocabulary_paths(root_path, descriptor):
    root_dir = root_path.parent.resolve()
    declarations = descriptor.get("vocabulary_files", [])
    if not isinstance(declarations, list):
        raise KnowledgePackLoadError(
            "Federated ontology vocabulary_files must be a list"
        )
    declared_domains = set(descriptor.get("domains", []))

    paths = []
    seen_domains = []
    for index, declaration in enumerate(declarations):
        if not isinstance(declaration, dict):
            raise KnowledgePackLoadError(
                f"vocabulary_files[{index}] must be an object"
            )
        domain = declaration.get("domain")
        relative_path = declaration.get("path")
        if not domain or not relative_path:
            raise KnowledgePackLoadError(
                f"vocabulary_files[{index}] requires domain and path"
            )
        if domain not in declared_domains:
            raise KnowledgePackLoadError(
                f"vocabulary_files[{index}] domain is not a declared ontology "
                f"domain: {domain}"
            )
        candidate = _resolve_bundle_path(
            root_dir, relative_path, "Ontology vocabulary file"
        )
        seen_domains.append(domain)
        paths.append((domain, candidate))

    if len(seen_domains) != len(set(seen_domains)):
        raise KnowledgePackLoadError(
            "Federated ontology vocabulary_files domains must be unique"
        )
    return paths


def load_federated_ontology(path):
    """Return one assembled ontology dictionary and its bundle fingerprint."""
    root_path = Path(path).resolve()
    descriptor = _read_serialized(root_path)
    if descriptor.get("format") != FEDERATED_ONTOLOGY_FORMAT:
        raise KnowledgePackLoadError(
            f"Not a federated ontology descriptor: {root_path}"
        )

    concepts = []
    controlled_vocabularies = []
    reference_shapes = []
    bundle_paths = [root_path]
    for declared_domain, module_path in _federated_module_paths(
        root_path, descriptor
    ):
        if not module_path.is_file():
            raise KnowledgePackLoadError(
                f"Ontology module does not exist: {module_path}"
            )
        module = _read_serialized(module_path)
        expected = {
            "pack_id": descriptor.get("pack_id"),
            "pack_version": descriptor.get("pack_version"),
            "status": descriptor.get("status"),
            "domain": declared_domain,
        }
        for field, expected_value in expected.items():
            if module.get(field) != expected_value:
                raise KnowledgePackLoadError(
                    f"Ontology module {module_path.name} {field} must be "
                    f"{expected_value!r}, found {module.get(field)!r}"
                )
        module_concepts = module.get("concepts")
        if not isinstance(module_concepts, list) or not module_concepts:
            raise KnowledgePackLoadError(
                f"Ontology module has no concepts: {module_path.name}"
            )
        wrong_domain = [
            concept.get("concept_id", "<missing>")
            for concept in module_concepts
            if concept.get("domain") != declared_domain
        ]
        if wrong_domain:
            raise KnowledgePackLoadError(
                f"Ontology module {module_path.name} contains concepts outside "
                f"{declared_domain}: {wrong_domain}"
            )
        concepts.extend(module_concepts)
        module_vocabularies = module.get("controlled_vocabularies", [])
        module_shapes = module.get("reference_shapes", [])
        if not isinstance(module_vocabularies, list):
            raise KnowledgePackLoadError(
                f"Ontology module controlled_vocabularies must be a list: "
                f"{module_path.name}"
            )
        if not isinstance(module_shapes, list):
            raise KnowledgePackLoadError(
                f"Ontology module reference_shapes must be a list: "
                f"{module_path.name}"
            )
        controlled_vocabularies.extend(module_vocabularies)
        reference_shapes.extend(module_shapes)
        bundle_paths.append(module_path)

    for declared_domain, vocab_path in _federated_vocabulary_paths(
        root_path, descriptor
    ):
        if not vocab_path.is_file():
            raise KnowledgePackLoadError(
                f"Ontology vocabulary file does not exist: {vocab_path}"
            )
        vocab_module = _read_serialized(vocab_path)
        expected = {
            "pack_id": descriptor.get("pack_id"),
            "pack_version": descriptor.get("pack_version"),
            "status": descriptor.get("status"),
            "domain": declared_domain,
        }
        for field, expected_value in expected.items():
            if vocab_module.get(field) != expected_value:
                raise KnowledgePackLoadError(
                    f"Ontology vocabulary file {vocab_path.name} {field} must "
                    f"be {expected_value!r}, found {vocab_module.get(field)!r}"
                )
        vocab_vocabularies = vocab_module.get("controlled_vocabularies", [])
        vocab_shapes = vocab_module.get("reference_shapes", [])
        if not isinstance(vocab_vocabularies, list):
            raise KnowledgePackLoadError(
                "Ontology vocabulary file controlled_vocabularies must be a "
                f"list: {vocab_path.name}"
            )
        if not isinstance(vocab_shapes, list):
            raise KnowledgePackLoadError(
                f"Ontology vocabulary file reference_shapes must be a list: "
                f"{vocab_path.name}"
            )
        if not vocab_vocabularies and not vocab_shapes:
            raise KnowledgePackLoadError(
                "Ontology vocabulary file has no vocabularies or shapes: "
                f"{vocab_path.name}"
            )
        controlled_vocabularies.extend(vocab_vocabularies)
        reference_shapes.extend(vocab_shapes)
        bundle_paths.append(vocab_path)

    assembled = {
        key: value for key, value in descriptor.items()
        if key not in {"format", "module_files"}
    }
    assembled["concepts"] = concepts
    concept_ids = [concept.get("concept_id") for concept in concepts]
    if len(concept_ids) != len(set(concept_ids)):
        raise KnowledgePackLoadError(
            "Federated ontology concept IDs must be unique across modules"
        )
    supported_types = set(descriptor.get("enums", {}).get("concept_type", []))
    unsupported_types = sorted({
        concept.get("concept_type") for concept in concepts
        if concept.get("concept_type") not in supported_types
    })
    if unsupported_types:
        raise KnowledgePackLoadError(
            f"Ontology concepts use undeclared concept types: {unsupported_types}"
        )

    vocabulary_ids = [
        item.get("vocabulary_id") for item in controlled_vocabularies
    ]
    if len(vocabulary_ids) != len(set(vocabulary_ids)):
        raise KnowledgePackLoadError(
            "Controlled vocabulary IDs must be unique across modules"
        )
    shape_ids = [item.get("shape_id") for item in reference_shapes]
    if len(shape_ids) != len(set(shape_ids)):
        raise KnowledgePackLoadError(
            "Reference shape IDs must be unique across modules"
        )
    available = set(concept_ids)
    missing_shape_concepts = sorted({
        concept_id
        for shape in reference_shapes
        for concept_id in (
            [shape.get("root_concept_id")]
            + list(shape.get("required_concept_ids", []))
            + list(shape.get("optional_concept_ids", []))
        )
        if concept_id not in available
    })
    if missing_shape_concepts:
        raise KnowledgePackLoadError(
            "Reference shapes use unavailable concepts: "
            f"{missing_shape_concepts}"
        )
    if controlled_vocabularies:
        assembled["controlled_vocabularies"] = controlled_vocabularies
    if reference_shapes:
        assembled["reference_shapes"] = reference_shapes
    return assembled, fingerprint_pack(root_path, bundle_paths=bundle_paths)


def fingerprint_pack(path, bundle_paths=None):
    """Return an exact byte-and-path fingerprint for one pack or bundle."""
    root_path = Path(path).resolve()
    if bundle_paths is None:
        descriptor = _read_serialized(root_path)
        if descriptor.get("format") == FEDERATED_ONTOLOGY_FORMAT:
            return load_federated_ontology(root_path)[1]
    paths = bundle_paths or [root_path]
    digest = hashlib.sha256()
    for item in paths:
        item = Path(item).resolve()
        relative = item.relative_to(root_path.parent).as_posix().encode("utf-8")
        content = item.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def load_knowledge_pack(path):
    """Load a standalone pack or assemble a federated ontology descriptor."""
    pack_path = Path(path)
    data = _read_serialized(pack_path)
    if data.get("format") == FEDERATED_ONTOLOGY_FORMAT:
        return load_federated_ontology(pack_path)[0]
    return data
