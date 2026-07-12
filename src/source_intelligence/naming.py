"""Propose business semantics from transparent table and column-name rules.

Known synthetic attributes map to explicit business names, ontology concepts,
domains, and naming strengths. Unknown attributes receive only a readable name,
an unresolved concept, a cautious strength, and a reason that states the result
is naming-pattern inference. These proposals are deterministic candidates, not
steward-approved truth, and unresolved meaning remains unresolved.
"""

EXACT_MATCHES = {
    "policy_id": ("Policy Identifier", "Policy.Identifier", "Policy", 0.95),
    "policy_number": ("Policy Number", "Policy.PolicyNumber", "Policy", 0.95),
    "policy_status": ("Policy Status", "Policy.Status", "Policy", 0.90),
    "effective_date": ("Policy Effective Date", "Policy.EffectiveDate", "Policy", 0.90),
    "expiration_date": ("Policy Expiration Date", "Policy.ExpirationDate", "Policy", 0.90),
    "product_code": ("Insurance Product Code", "Product.Code", "Shared", 0.85),
    "insured_party_id": ("Insured Party Identifier", "Party.Identifier", "Shared", 0.85),
    "party_id": ("Party Identifier", "Party.Identifier", "Shared", 0.95),
    "party_type": ("Party Type", "Party.Type", "Shared", 0.90),
    "claim_id": ("Claim Identifier", "Claim.Identifier", "Claims", 0.95),
    "loss_date": ("Loss Date", "Claim.LossDate", "Claims", 0.90),
    "claim_status": ("Claim Status", "Claim.Status", "Claims", 0.90),
    "claimed_amount": ("Claimed Amount", "Claim.ClaimedAmount", "Claims", 0.85),
    "source_updated_ts": ("Source Updated Timestamp", "Technical.SourceUpdatedTimestamp", "Shared", 0.95),
}

PII_TOKENS = ("display_name", "email", "phone", "address", "birth", "ssn", "name")


def classify_naming(table_name, column_name):
    name = column_name.lower()
    table = table_name.lower().replace("bronze_", "")
    proposed_name = column_name.replace("_", " ").title()
    ontology_concept = None
    domain = "Shared"
    naming_strength = 0.55
    reason = "Naming-pattern inference only"

    if "policyholder" in table or "party" in table:
        domain = "Shared"
    elif "policy" in table or name.startswith("policy_"):
        domain = "Policy"
    elif "claim" in table or name.startswith("claim_") or name == "loss_date":
        domain = "Claims"
    elif "party" in name or "insured" in name:
        domain = "Shared"

    if name in EXACT_MATCHES:
        proposed_name, ontology_concept, domain, naming_strength = EXACT_MATCHES[name]
        reason = "Deterministic candidate rule (not steward-approved)"

    return proposed_name, ontology_concept, domain, naming_strength, reason


def detect_personal_data(column_name):
    name = column_name.lower()
    return any(token in name for token in PII_TOKENS)
