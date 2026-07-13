"""Validate Governed Knowledge Foundation knowledge records beyond their JSON field shapes.

The repository's JSON contracts define required fields, types, enums, and
closed record shapes. Some governance rules compare values in different parts
of the same record and cannot be expressed portably with ordinary JSON Schema.
This module is the single validation boundary for those rules. Producers call
``validate_knowledge_records`` before persistence; a malformed or cross-version
context therefore fails before it can become retained recommendation evidence.

The compatibility helpers are intentionally conservative. They detect common
breaking schema changes that would invalidate already persisted records:
removing properties, making optional fields required, changing types or
constants, narrowing enums, and tightening open-object behavior.
"""

from copy import deepcopy
from datetime import date

from common.contract_validation import (
    ContractValidationError,
    validate_records,
)


KNOWLEDGE_FOUNDATION_CONTRACTS = {
    "knowledge_document.json",
    "knowledge_concept.json",
    "ontology_relationship.json",
    "cots_structure_pattern.json",
    "knowledge_pack_version.json",
    "cots_match_assessment.json",
    "knowledge_context.json",
}


class ContractCompatibilityError(AssertionError):
    """Raised when a candidate schema breaks persisted-record compatibility."""


def _validate_pack_version_identity(record):
    provenance = record["provenance"]
    if record["pack_id"] != provenance["pack_id"]:
        raise ContractValidationError(
            "$.pack_id must equal $.provenance.pack_id"
        )
    if record["pack_version"] != provenance["pack_version"]:
        raise ContractValidationError(
            "$.pack_version must equal $.provenance.pack_version"
        )


def _validate_cots_structure_pattern(record):
    pattern_type = record["pattern_type"]
    concept_id = record["ontology_concept_id"]
    attribute_pattern = record["source_attribute_pattern"]
    if pattern_type == "EXTENSION_MARKER":
        if concept_id is not None:
            raise ContractValidationError(
                "EXTENSION_MARKER must not invent an ontology concept"
            )
    elif concept_id is None:
        raise ContractValidationError(
            f"{pattern_type} pattern requires an ontology concept"
        )
    if pattern_type == "ATTRIBUTE" and attribute_pattern is None:
        raise ContractValidationError(
            "ATTRIBUTE pattern requires source_attribute_pattern"
        )
    if pattern_type == "OBJECT" and attribute_pattern is not None:
        raise ContractValidationError(
            "OBJECT pattern must not define source_attribute_pattern"
        )


def _validate_match_assessment(record):
    outcome = record["match_outcome"]
    lifecycle = record["proposed_lifecycle_state"]
    if outcome == "UNRESOLVED":
        if record["pattern_id"] is not None or record["ontology_concept_id"] is not None:
            raise ContractValidationError(
                "UNRESOLVED assessment must not invent a pattern or concept"
            )
        if lifecycle != "Unresolved":
            raise ContractValidationError(
                "UNRESOLVED assessment must use lifecycle state Unresolved"
            )
    elif outcome == "MATCHED":
        if not record["pattern_id"] or not record["ontology_concept_id"]:
            raise ContractValidationError(
                "MATCHED assessment requires a pattern and ontology concept"
            )
    elif lifecycle != "Source extension":
        raise ContractValidationError(
            "LIKELY_CUSTOM_EXTENSION must use lifecycle state Source extension"
        )


def _parse_date(value, path):
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ContractValidationError(f"{path}: invalid ISO date {value!r}") from exc


def _validate_knowledge_context(record):
    if (
        record["usage_mode"] == "AUTHORITATIVE"
        and record["required_approval_state"] != "APPROVED"
    ):
        raise ContractValidationError(
            "AUTHORITATIVE context requires APPROVED knowledge"
        )

    selected_scope = record["scope"]
    effective_at = _parse_date(record["effective_at"], "$.effective_at")
    for index, item in enumerate(record["knowledge_items"]):
        path = f"$.knowledge_items[{index}]"
        if item["scope"] != selected_scope:
            raise ContractValidationError(
                f"{path}.scope does not match the requested context scope"
            )
        if item["pack_id"] != record["pack_id"]:
            raise ContractValidationError(
                f"{path}.pack_id does not match the selected pack"
            )
        if item["pack_version"] != record["pack_version"]:
            raise ContractValidationError(
                f"{path}.pack_version does not match the selected pack version"
            )
        if item["approval_state"] != record["required_approval_state"]:
            raise ContractValidationError(
                f"{path}.approval_state does not match required approval state"
            )
        effective_from = _parse_date(item["effective_from"], f"{path}.effective_from")
        effective_to = item["effective_to"]
        if effective_from > effective_at:
            raise ContractValidationError(f"{path} is not yet effective")
        if effective_to is not None and _parse_date(
            effective_to, f"{path}.effective_to"
        ) < effective_at:
            raise ContractValidationError(f"{path} is expired")


def validate_knowledge_records(records, contract_name, contracts_dir=None):
    """Validate Governed Knowledge Foundation record shape and cross-field governance invariants."""
    if contract_name not in KNOWLEDGE_FOUNDATION_CONTRACTS:
        raise ValueError(f"Unsupported Governed Knowledge Foundation contract: {contract_name}")
    validated = validate_records(records, contract_name, contracts_dir)
    for record in records:
        if contract_name == "cots_structure_pattern.json":
            _validate_cots_structure_pattern(record)
        elif contract_name == "knowledge_pack_version.json":
            _validate_pack_version_identity(record)
        elif contract_name == "cots_match_assessment.json":
            _validate_match_assessment(record)
        elif contract_name == "knowledge_context.json":
            _validate_knowledge_context(record)
    return validated


def find_breaking_schema_changes(previous, candidate, path="$"):
    """Return conservative compatibility findings for two JSON schemas."""
    findings = []
    previous_type = previous.get("type")
    candidate_type = candidate.get("type")
    if previous_type != candidate_type:
        findings.append(f"{path}: type changed from {previous_type!r} to {candidate_type!r}")

    if "const" in previous and previous.get("const") != candidate.get("const"):
        findings.append(f"{path}: constant changed")

    previous_enum = set(previous.get("enum", []))
    candidate_enum = set(candidate.get("enum", []))
    if previous_enum and not previous_enum.issubset(candidate_enum):
        findings.append(f"{path}: enum values were removed")

    previous_properties = previous.get("properties", {})
    candidate_properties = candidate.get("properties", {})
    removed = set(previous_properties) - set(candidate_properties)
    for field in sorted(removed):
        findings.append(f"{path}.{field}: property was removed")

    newly_required = set(candidate.get("required", [])) - set(
        previous.get("required", [])
    )
    for field in sorted(newly_required):
        findings.append(f"{path}.{field}: optional property became required")

    if previous.get("additionalProperties") is not False and (
        candidate.get("additionalProperties") is False
    ):
        findings.append(f"{path}: additional properties are no longer accepted")

    for field in sorted(set(previous_properties) & set(candidate_properties)):
        findings.extend(find_breaking_schema_changes(
            previous_properties[field],
            candidate_properties[field],
            f"{path}.{field}",
        ))
    return findings


def assert_contract_backward_compatible(previous, candidate):
    """Raise with all detected breaking changes; return ``True`` otherwise."""
    findings = find_breaking_schema_changes(deepcopy(previous), deepcopy(candidate))
    if findings:
        raise ContractCompatibilityError("; ".join(findings))
    return True
