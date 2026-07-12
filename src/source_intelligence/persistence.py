"""Plan safe appends to existing solution-owned Delta table schemas.

Phase 1 compatibility tables can have a narrower physical schema than the full
Phase 2 contract record. This module compares simple, dependency-free mappings
of column names to Spark type strings and returns the exact existing-table
column order when every required column is present with a compatible type.

The planner never proposes schema evolution, migration, casting, or field
invention. Missing or incompatible columns fail explicitly. Producers may use
the returned order to drop only additional incoming fields for a compatibility
write while persisting the complete contract record to its Phase 2 table.
"""


class SchemaCompatibilityError(ValueError):
    """Raised when an incoming record cannot safely fit an existing schema."""


LEGACY_CONFIDENCE_FIELDS = (
    "naming_strength",
    "type_strength",
    "relationship_strength",
)


def plan_existing_schema_alignment(incoming_types, existing_types):
    """Return existing column order after validating names and type strings."""
    missing = [name for name in existing_types if name not in incoming_types]
    if missing:
        raise SchemaCompatibilityError(
            f"Incoming data is missing existing table columns: {missing}"
        )

    mismatched = {
        name: {
            "incoming": incoming_types[name],
            "existing": existing_type,
        }
        for name, existing_type in existing_types.items()
        if incoming_types[name] != existing_type
    }
    if mismatched:
        raise SchemaCompatibilityError(
            f"Incoming and existing column types differ: {mismatched}"
        )

    return list(existing_types)
