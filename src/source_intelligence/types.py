"""Score compatibility between physical types and proposed field semantics.

The rules compare a source column's PySpark type representation with transparent
name-based expectations for dates, timestamps, identifiers, measures, and
counts. The result is one confidence component rather than a semantic decision:
compatible types support a proposal, while unknown or conflicting types lower
the evidence strength and may require review.
"""

TYPE_EXPECTATIONS = {
    "DateType": ["date", "effective_date", "expiration_date", "loss_date", "birth_date"],
    "TimestampType": ["source_updated_ts", "created_at", "updated_at"],
    "StringType": ["policy_id", "policy_number", "policy_status", "claim_id", "claim_status", "party_id", "party_type", "product_code", "display_name", "contact_channel"],
    "DecimalType": ["claimed_amount", "premium_amount", "deductible_amount"],
    "IntegerType": ["count", "sequence", "version"],
    "BooleanType": ["is_active", "is_deleted", "flag"],
}


def check_type_compatibility(physical_type: str, column_name: str) -> float:
    """Check if physical type is compatible with column name semantics.
    Returns type_strength (0.0 to 1.0).
    """
    type_str = str(physical_type)
    name = column_name.lower()
    for expected_type, keywords in TYPE_EXPECTATIONS.items():
        if expected_type in type_str:
            if any(kw in name for kw in keywords):
                return 0.8
            return 0.5
    return 0.4
