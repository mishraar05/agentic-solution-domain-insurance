"""Normalize the governed insurance ontology into contract-valid table records.

The source ontology is an authoring-friendly knowledge pack: relationships are
nested under concepts and some fields use source-specific classifications.
Downstream knowledge tables require one contract-valid record per concept and
one per relationship. This module performs that mechanical normalization while
preserving stable concept IDs and refusing to invent missing endpoints or
unsupported relationship semantics.

Concepts are selected by governed domain rather than a hardcoded concept list.
The default emits every domain declared by the source ontology; callers may
request an explicit subset, with cross-boundary relationships reported as
exclusions rather than silently coerced.
"""

from copy import deepcopy

from common.contract_validation import ContractValidationError
from governed_knowledge_foundation.knowledge_contract_validation import (
    validate_knowledge_records,
)


PRIVACY_CLASS_MAP = {
    "NONE": "INTERNAL",
    "INDIRECT": "PERSONAL_DATA",
    "DIRECT": "PERSONAL_DATA",
    "SENSITIVE": "SENSITIVE",
}

RELATIONSHIP_RULES = {
    "belongs_to": ("BELONGS_TO", "ONE", "ONE"),
    "derives_from": ("DERIVES_FROM", "ONE", "ONE_OR_MORE"),
    "describes": ("DESCRIBES", "ONE", "ONE"),
    "groups": ("GROUPS", "ONE", "ONE_OR_MORE"),
    "has_many": ("HAS", "ONE", "ZERO_OR_MORE"),
    "identifies": ("IDENTIFIES", "ONE", "ONE"),
    "is_a": ("IS_A", "ONE", "ONE"),
    "measures": ("MEASURES", "ONE", "ONE"),
    "precedes": ("PRECEDES", "ONE", "ZERO_OR_ONE"),
    "reduces": ("REDUCES", "ONE", "ONE"),
    "references": ("REFERENCES", "ONE", "ZERO_OR_ONE"),
}


def _scope(source_pack, domain):
    pack_id = source_pack["pack_id"]
    return {
        "product": pack_id,
        "module": f"{pack_id.removesuffix('_ontology')}_foundation",
        "product_version": source_pack["pack_version"],
        "domain": domain,
        "line_of_business": "Multi-line",
    }


def _provenance(source_pack, fingerprint, evidence_reference, effective_from,
                created_at):
    return {
        "pack_id": source_pack["pack_id"],
        "pack_version": source_pack["pack_version"],
        "effective_from": effective_from,
        "effective_to": None,
        "approval_state": source_pack["status"],
        "owner_role": "DOMAIN_STEWARD",
        "evidence_references": [
            f"{evidence_reference}#sha256:{fingerprint}"
        ],
        "content_fingerprint": fingerprint,
        "created_at": created_at,
    }


def _privacy_class(source_value):
    try:
        return PRIVACY_CLASS_MAP[source_value]
    except KeyError as exc:
        raise ContractValidationError(
            f"Unsupported ontology privacy sensitivity: {source_value!r}"
        ) from exc


def _concept_record(concept, source_pack, fingerprint, evidence_reference,
                    effective_from, created_at):
    lob = concept.get("lob_applicability", "ALL")
    lob_values = list(lob) if isinstance(lob, list) else [lob]
    return {
        "schema_version": "1.0.0",
        "concept_id": concept["concept_id"],
        "concept_name": concept["name"],
        "definition": concept["definition"],
        "concept_type": concept["concept_type"],
        "lifecycle_state": concept["lifecycle_state"],
        "privacy_class": _privacy_class(concept["privacy_sensitivity"]),
        "synonyms": deepcopy(concept.get("synonyms", [])),
        "physical_name_variants": deepcopy(
            concept.get("physical_name_variants", [])
        ),
        "lob_applicability": lob_values,
        "temporality": concept["temporality"],
        "typical_attributes": deepcopy(concept.get("typical_attributes", [])),
        "status_values": deepcopy(concept.get("status_values", [])),
        "steward_notes": concept.get("steward_notes", ""),
        "scope": _scope(source_pack, concept["domain"]),
        "provenance": _provenance(
            source_pack,
            fingerprint,
            evidence_reference,
            effective_from,
            created_at,
        ),
    }


def _relationship_record(source_concept, relationship, source_pack,
                         fingerprint, evidence_reference, effective_from,
                         created_at):
    source_type = relationship["type"]
    try:
        normalized_type, source_cardinality, target_cardinality = (
            RELATIONSHIP_RULES[source_type]
        )
    except KeyError as exc:
        raise ContractValidationError(
            f"Unsupported ontology relationship type: {source_type!r}"
        ) from exc

    source_id = source_concept["concept_id"]
    target_id = relationship["target"]
    return {
        "schema_version": "1.0.0",
        "relationship_id": (
            f"REL.{source_id}.{normalized_type}.{target_id}"
        ),
        "source_concept_id": source_id,
        "target_concept_id": target_id,
        "relationship_type": normalized_type,
        "source_relationship_type": source_type,
        "source_cardinality": source_cardinality,
        "target_cardinality": target_cardinality,
        "definition": (
            f"Source ontology relationship {source_type!r} from "
            f"{source_id} to {target_id}."
        ),
        "lifecycle_state": source_concept["lifecycle_state"],
        "scope": _scope(source_pack, source_concept["domain"]),
        "provenance": _provenance(
            source_pack,
            fingerprint,
            evidence_reference,
            effective_from,
            created_at,
        ),
    }


def normalize_governed_ontology(source_pack, fingerprint, effective_from,
                                created_at, included_domains=None,
                                evidence_reference=(
                                    "knowledge_packs/ontology/"
                                    "insurance_ontology_v1.yaml"
                                )):
    """Return contract-valid records for the selected governed domains."""
    source_concepts = source_pack.get("concepts", [])
    source_ids = [concept["concept_id"] for concept in source_concepts]
    if len(source_ids) != len(set(source_ids)):
        raise ContractValidationError("Source ontology concept IDs are not unique")

    source_by_id = {concept["concept_id"]: concept for concept in source_concepts}
    missing_targets = sorted({
        relationship["target"]
        for concept in source_concepts
        for relationship in concept.get("relationships", [])
        if relationship["target"] not in source_by_id
    })
    if missing_targets:
        raise ContractValidationError(
            f"Source ontology relationship targets are missing: {missing_targets}"
        )

    declared_domains = set(source_pack.get("domains", []))
    selected_domains = (
        declared_domains if included_domains is None else set(included_domains)
    )
    unsupported_domains = selected_domains - declared_domains
    if unsupported_domains:
        raise ContractValidationError(
            f"Requested ontology domains are not declared: {sorted(unsupported_domains)}"
        )
    selected_ids = [
        concept["concept_id"] for concept in source_concepts
        if concept["domain"] in selected_domains
    ]
    selected = set(selected_ids)
    concept_records = [
        _concept_record(
            source_by_id[concept_id],
            source_pack,
            fingerprint,
            evidence_reference,
            effective_from,
            created_at,
        )
        for concept_id in selected_ids
    ]

    relationship_records = []
    excluded_relationships = []
    for concept_id in selected_ids:
        concept = source_by_id[concept_id]
        for relationship in concept.get("relationships", []):
            if relationship["target"] not in selected:
                excluded_relationships.append({
                    "source_concept_id": concept_id,
                    "source_relationship_type": relationship["type"],
                    "target_concept_id": relationship["target"],
                    "reason": "TARGET_OUTSIDE_GOVERNED_SCOPE",
                })
                continue
            relationship_records.append(_relationship_record(
                concept,
                relationship,
                source_pack,
                fingerprint,
                evidence_reference,
                effective_from,
                created_at,
            ))

    validate_normalized_ontology(concept_records, relationship_records)
    return {
        "concept_records": concept_records,
        "relationship_records": relationship_records,
        "excluded_relationships": excluded_relationships,
    }


def validate_normalized_ontology(concept_records, relationship_records):
    """Validate record contracts, unique IDs, and relationship endpoints."""
    validate_knowledge_records(concept_records, "knowledge_concept.json")
    validate_knowledge_records(
        relationship_records, "ontology_relationship.json"
    )

    concept_ids = [record["concept_id"] for record in concept_records]
    if len(concept_ids) != len(set(concept_ids)):
        raise ContractValidationError("Normalized concept IDs are not unique")
    relationship_ids = [
        record["relationship_id"] for record in relationship_records
    ]
    if len(relationship_ids) != len(set(relationship_ids)):
        raise ContractValidationError("Normalized relationship IDs are not unique")

    endpoints = set(concept_ids)
    for record in relationship_records:
        if record["source_concept_id"] not in endpoints:
            raise ContractValidationError(
                f"Missing source endpoint: {record['source_concept_id']}"
            )
        if record["target_concept_id"] not in endpoints:
            raise ContractValidationError(
                f"Missing target endpoint: {record['target_concept_id']}"
            )
    return len(concept_records), len(relationship_records)
