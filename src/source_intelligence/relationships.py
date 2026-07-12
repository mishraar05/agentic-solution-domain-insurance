"""Relationship inference from key naming and type patterns."""

PRIMARY_KEYS = {
    "bronze_policy": "policy_id",
    "bronze_policyholder": "party_id",
    "bronze_claim": "claim_id",
}

KNOWN_RELATIONSHIPS = {
    ("bronze_claim", "policy_id"): ("bronze_policy", "policy_id"),
    ("bronze_policy", "insured_party_id"): ("bronze_policyholder", "party_id"),
}


def infer_key_role(table_name: str, column_name: str) -> str:
    """Infer the key role of a column."""
    if PRIMARY_KEYS.get(table_name) == column_name:
        return "PRIMARY_KEY_CANDIDATE"
    if column_name.endswith("_id"):
        return "FOREIGN_KEY_CANDIDATE"
    return "NON_KEY"


def infer_relationship(table_name: str, column_name: str):
    """Infer relationship evidence for a column."""
    key = (table_name, column_name)
    if key in KNOWN_RELATIONSHIPS:
        target_table, target_column = KNOWN_RELATIONSHIPS[key]
        return f"Inferred relationship: {table_name}.{column_name} -> {target_table}.{target_column}"
    return None


def compute_relationship_strength(table_name: str, column_name: str, has_relationship: bool) -> float:
    """Compute relationship evidence strength."""
    if has_relationship:
        return 0.9
    if column_name.endswith("_id"):
        return 0.5
    return 0.4
