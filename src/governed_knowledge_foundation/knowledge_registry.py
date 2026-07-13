"""Load and validate immutable governed knowledge-pack registrations.

Authored pack bundles group records that each remain governed by one of the
seven knowledge contracts. This module validates those records, then enforces
cross-record rules that JSON Schema cannot express: one exact scope and pack
identity, unique stable pattern IDs, authorized evidence only, resolvable
ontology concepts, and immutable manifest fingerprints.

The registry never publishes data or mutates a source. Publication workflows
consume its validated records in a later work package.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from common.contract_validation import ContractValidationError
from governed_knowledge_foundation.knowledge_contract_validation import (
    validate_knowledge_records,
)


PACK_BUNDLE_FIELDS = {
    "schema_version",
    "pack_id",
    "pack_version",
    "status",
    "scope",
    "authoring_source",
    "knowledge_document",
    "knowledge_pack_version",
    "cots_structure_patterns",
    "excluded_source_mappings",
}


def file_sha256(path):
    """Return the lowercase SHA-256 digest of a file without modifying it."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_authored_pack(path):
    """Load one authored JSON pack bundle."""
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _require_equal(actual, expected, path):
    if actual != expected:
        raise ContractValidationError(
            f"{path} must equal {expected!r}; received {actual!r}"
        )


def _validate_record_identity(record, pack_id, pack_version, scope, path):
    _require_equal(record["scope"], scope, f"{path}.scope")
    provenance = record["provenance"]
    _require_equal(provenance["pack_id"], pack_id, f"{path}.provenance.pack_id")
    _require_equal(
        provenance["pack_version"],
        pack_version,
        f"{path}.provenance.pack_version",
    )


def validate_authored_pack(
    bundle,
    ontology_concept_ids,
    authorized_evidence_ids,
    authorized_evidence_references,
):
    """Validate an authored pack bundle and return deterministic record counts."""
    fields = set(bundle)
    if fields != PACK_BUNDLE_FIELDS:
        missing = sorted(PACK_BUNDLE_FIELDS - fields)
        extra = sorted(fields - PACK_BUNDLE_FIELDS)
        raise ContractValidationError(
            f"Authored pack fields differ; missing={missing}, extra={extra}"
        )

    pack_id = bundle["pack_id"]
    pack_version = bundle["pack_version"]
    scope = bundle["scope"]
    document = bundle["knowledge_document"]
    version_record = bundle["knowledge_pack_version"]
    patterns = bundle["cots_structure_patterns"]

    validate_knowledge_records([document], "knowledge_document.json")
    validate_knowledge_records([version_record], "knowledge_pack_version.json")
    validate_knowledge_records(patterns, "cots_structure_pattern.json")

    _require_equal(bundle["status"], "PROPOSED", "$.status")
    _require_equal(version_record["pack_id"], pack_id, "$.knowledge_pack_version.pack_id")
    _require_equal(
        version_record["pack_version"],
        pack_version,
        "$.knowledge_pack_version.pack_version",
    )

    records = [("$.knowledge_document", document),
               ("$.knowledge_pack_version", version_record)]
    records.extend(
        (f"$.cots_structure_patterns[{index}]", record)
        for index, record in enumerate(patterns)
    )
    allowed_refs = set(authorized_evidence_references) | set(
        authorized_evidence_ids
    )
    authoring_source = bundle["authoring_source"]
    if authoring_source not in authorized_evidence_references:
        raise ContractValidationError(
            "$.authoring_source is not an authorized evidence reference"
        )
    source_fingerprint = authoring_source.rsplit("#sha256:", 1)[-1]
    document_id = document["document_id"]
    for path, record in records:
        _validate_record_identity(record, pack_id, pack_version, scope, path)
        evidence_refs = set(record["provenance"]["evidence_references"])
        if not evidence_refs.issubset(allowed_refs):
            raise ContractValidationError(
                f"{path} contains an unauthorized evidence reference"
            )
        if document_id not in evidence_refs:
            raise ContractValidationError(
                f"{path} does not cite the pack evidence ID"
            )
        if authoring_source not in evidence_refs:
            raise ContractValidationError(
                f"{path} does not cite the exact authoring source"
            )
        if record["provenance"]["content_fingerprint"] != source_fingerprint:
            raise ContractValidationError(
                f"{path} content fingerprint differs from the authoring source"
            )

    if document_id not in authorized_evidence_ids:
        raise ContractValidationError(
            "$.knowledge_document.document_id is not authorized"
        )

    pattern_ids = [record["pattern_id"] for record in patterns]
    if len(pattern_ids) != len(set(pattern_ids)):
        raise ContractValidationError("COTS pattern IDs are not unique")

    concepts = set(ontology_concept_ids)
    extension_count = 0
    for index, pattern in enumerate(patterns):
        path = f"$.cots_structure_patterns[{index}]"
        if pattern["pattern_type"] == "EXTENSION_MARKER":
            extension_count += 1
            if pattern["ontology_concept_id"] is not None:
                raise ContractValidationError(
                    f"{path} extension marker must not invent a concept"
                )
            if pattern["lifecycle_state"] != "Source extension":
                raise ContractValidationError(
                    f"{path} extension marker must use Source extension lifecycle"
                )
        elif pattern["ontology_concept_id"] not in concepts:
            raise ContractValidationError(
                f"{path} references an unavailable ontology concept"
            )

    exclusions = bundle["excluded_source_mappings"]
    required_exclusion_fields = {
        "source_object",
        "source_attribute",
        "source_concept_id",
        "reason",
    }
    for index, exclusion in enumerate(exclusions):
        if set(exclusion) != required_exclusion_fields:
            raise ContractValidationError(
                f"$.excluded_source_mappings[{index}] has an invalid shape"
            )
        if exclusion["reason"] != "ONTOLOGY_CONCEPT_OUTSIDE_AUTHORIZED_SCOPE":
            raise ContractValidationError(
                f"$.excluded_source_mappings[{index}] has an unsupported reason"
            )

    return {
        "documents": 1,
        "pack_versions": 1,
        "patterns": len(patterns),
        "extension_markers": extension_count,
        "excluded_mappings": len(exclusions),
    }


def validate_manifest_registration(pack_path, manifest_entry):
    """Validate manifest identity and content digest for one authored pack."""
    bundle = load_authored_pack(pack_path)
    for field in ("pack_id", "pack_version", "status"):
        _require_equal(bundle[field], manifest_entry[field], f"manifest.{field}")
    expected_digest = manifest_entry.get("content_sha256")
    if expected_digest is None:
        raise ContractValidationError("Manifest entry requires content_sha256")
    _require_equal(file_sha256(pack_path), expected_digest, "manifest.content_sha256")
    return True


def assert_immutable_registration(existing_entry, candidate_entry):
    """Reject content or path replacement under an existing pack identity."""
    existing = deepcopy(existing_entry)
    candidate = deepcopy(candidate_entry)
    identity = ("pack_id", "pack_version")
    if all(existing.get(key) == candidate.get(key) for key in identity):
        for field in ("path", "content_sha256"):
            if existing.get(field) != candidate.get(field):
                raise ContractValidationError(
                    "Existing pack identity cannot be registered with changed "
                    f"{field}"
                )
    return True
