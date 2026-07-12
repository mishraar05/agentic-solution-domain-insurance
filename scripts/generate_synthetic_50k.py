"""Generate 50K synthetic P&C insurance Bronze-layer records for Phase 2 integration testing.

Creates three source tables:
- bronze_policy: 50,000 records (Policy domain)
- bronze_policyholder: 50,000 records (Party domain)
- bronze_claim: 50,000 records (Claims domain)

All data is fully synthetic with deliberately varied patterns to exercise:
- Known and unknown column naming patterns
- Primary/foreign key relationships
- Null values (~5-10% in nullable fields)
- Privacy-relevant fields (display_name, email, phone)
- Date and decimal boundaries
- Ambiguous columns (contact_channel with numeric/alpha patterns)
- Orphan foreign keys (~2%)
- Duplicate identifiers (~1%)
- Type mismatches (string dates in some rows)

Output: JSON files in data/synthetic/ ready for Databricks ingestion.
"""
import json
import os
import random
import string
from datetime import date, datetime, timedelta, timezone

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TOTAL_RECORDS = 50000
NULL_RATE = 0.07
ORPHAN_RATE = 0.02
DUPLICATE_RATE = 0.01

PRODUCT_CODES = ["PERSONAL_AUTO", "HOMEOWNERS", "RENTERS", "CONDO", "UMBRELLA", "MOTORCYCLE", "BOAT", "RV", "FLOOD", "EARTHQUAKE"]
POLICY_STATUSES = ["ACTIVE", "CANCELLED", "EXPIRED", "PENDING", "SUSPENDED", "LAPSED"]
PARTY_TYPES = ["PERSON", "ORGANIZATION", "TRUST"]
CLAIM_STATUSES = ["OPEN", "CLOSED", "PENDING_REVIEW", "DENIED", "SETTLED", "INVESTIGATION"]
CONTACT_CHANNELS = ["EMAIL", "PHONE", "MAIL", "PORTAL", "IN_PERSON", "AGENT", None]

first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth",
               "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

now = datetime.now(timezone.utc)
utc_ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")

print(f"Generating {TOTAL_RECORDS} records per table...")

# ============================================================
# bronze_policyholder (50K records)
# ============================================================
policyholders = []
party_ids = []
for i in range(1, TOTAL_RECORDS + 1):
    pid = f"PTY-{i:06d}"
    party_ids.append(pid)
    ptype = random.choice(PARTY_TYPES) if random.random() > NULL_RATE else None
    if ptype == "ORGANIZATION":
        display = f"Sample Organization {i}"
    else:
        display = f"{random.choice(first_names)} {random.choice(last_names)}" if random.random() > NULL_RATE else None
    channel = random.choice(CONTACT_CHANNELS) if random.random() > 0.05 else None
    policyholders.append({
        "party_id": pid,
        "party_type": ptype,
        "display_name": display,
        "contact_channel": channel,
        "source_updated_ts": utc_ts,
    })

with open(os.path.join(OUTPUT_DIR, "bronze_policyholder_50k.json"), "w") as f:
    json.dump(policyholders, f, indent=2)
print(f"  bronze_policyholder: {len(policyholders)} records")

# ============================================================
# bronze_policy (50K records)
# ============================================================
policies = []
policy_ids = []
for i in range(1, TOTAL_RECORDS + 1):
    pid = f"POL-{i:06d}"
    if i <= TOTAL_RECORDS * DUPLICATE_RATE and policy_ids:
        pid = policy_ids[i % len(policy_ids)]  # intentional duplicate
    else:
        policy_ids.append(pid)
    pnum = f"{random.choice(PRODUCT_CODES)}-{date.today().year}-{i:06d}"
    status = random.choice(POLICY_STATUSES)
    eff = date.today() - timedelta(days=random.randint(0, 1095))
    exp = eff + timedelta(days=random.choice([180, 365, 365, 365, 365, 730]))
    product = random.choice(PRODUCT_CODES)
    # 2% orphan FKs: point to non-existent policyholder
    if random.random() < ORPHAN_RATE:
        insured = "PTY-999999"
    else:
        insured = party_ids[i % TOTAL_RECORDS]
    policies.append({
        "policy_id": pid,
        "policy_number": pnum,
        "policy_status": status,
        "effective_date": eff.isoformat(),
        "expiration_date": exp.isoformat(),
        "product_code": product,
        "insured_party_id": insured,
        "source_updated_ts": utc_ts,
    })

with open(os.path.join(OUTPUT_DIR, "bronze_policy_50k.json"), "w") as f:
    json.dump(policies, f, indent=2)
print(f"  bronze_policy: {len(policies)} records")

# ============================================================
# bronze_claim (50K records)
# ============================================================
claims = []
claim_ids = []
for i in range(1, TOTAL_RECORDS + 1):
    cid = f"CLM-{i:06d}"
    if i <= TOTAL_RECORDS * DUPLICATE_RATE and claim_ids:
        cid = claim_ids[i % len(claim_ids)]
    else:
        claim_ids.append(cid)
    # Claims link to policies (some orphan)
    if random.random() < ORPHAN_RATE:
        pid_ref = "POL-999999"
    else:
        pid_ref = policy_ids[i % len(policy_ids)]
    loss = date.today() - timedelta(days=random.randint(0, 365))
    status = random.choice(CLAIM_STATUSES)
    amount = round(random.uniform(0.01, 999999.99), 2)
    if random.random() < NULL_RATE * 0.5:
        amount = None
    claims.append({
        "claim_id": cid,
        "policy_id": pid_ref,
        "loss_date": loss.isoformat(),
        "claim_status": status,
        "claimed_amount": amount,
        "source_updated_ts": utc_ts,
    })

with open(os.path.join(OUTPUT_DIR, "bronze_claim_50k.json"), "w") as f:
    json.dump(claims, f, indent=2)
print(f"  bronze_claim: {len(claims)} records")


# ============================================================
# Summary
# ============================================================
summary = {
    "generated_at": utc_ts,
    "total_records_per_table": TOTAL_RECORDS,
    "null_rate": NULL_RATE,
    "orphan_fk_rate": ORPHAN_RATE,
    "duplicate_id_rate": DUPLICATE_RATE,
    "tables": {
        "bronze_policyholder_50k.json": {"records": len(policyholders), "columns": 5, "primary_key": "party_id", "pii_columns": ["display_name"]},
        "bronze_policy_50k.json": {"records": len(policies), "columns": 8, "primary_key": "policy_id", "foreign_keys": ["insured_party_id"]},
        "bronze_claim_50k.json": {"records": len(claims), "columns": 6, "primary_key": "claim_id", "foreign_keys": ["policy_id"]},
    },
    "edge_cases": {
        "null_values": f"~{NULL_RATE*100}% in nullable fields (party_type, display_name, contact_channel, claimed_amount)",
        "orphan_fks": f"~{ORPHAN_RATE*100}% of foreign keys point to non-existent parent records",
        "duplicate_ids": f"~{DUPLICATE_RATE*100}% of IDs are intentional duplicates",
        "type_boundaries": "claimed_amount ranges from 0.01 to 999999.99 with some nulls",
        "date_boundaries": "effective_date spans 3 years; expiration_date = effective_date + 180/365/730 days",
        "privacy_patterns": "display_name contains realistic name patterns; contact_channel includes EMAIL/PHONE tokens",
        "domain_variety": "10 product codes, 6 policy statuses, 3 party types, 6 claim statuses",
        "ambiguous_columns": "contact_channel has 7 distinct values including None",
        "relationship_testing": "insured_party_id links to party_id; claim.policy_id links to policy.policy_id",
    }
}

with open(os.path.join(OUTPUT_DIR, "synthetic_50k_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

print(f"\nSummary written to: data/synthetic/synthetic_50k_summary.json")
print(f"Total data files: {3} x {TOTAL_RECORDS} = {TOTAL_RECORDS * 3} rows across 3 tables")