"""Provision the demo Bronze source schema and synthetic tables."""
from databricks.sdk import WorkspaceClient
w = WorkspaceClient(profile="DEV")
WH = "21014374f253edf2"

print("Creating schema: workspace.agentic_insurance_demo_bronze")
w.statement_execution.execute_statement(
    warehouse_id=WH,
    statement="CREATE SCHEMA IF NOT EXISTS workspace.agentic_insurance_demo_bronze",
    wait_timeout="30s",
)

stmts = [
    """CREATE TABLE IF NOT EXISTS workspace.agentic_insurance_demo_bronze.bronze_policy (
        policy_id STRING NOT NULL, policy_number STRING NOT NULL, policy_status STRING NOT NULL,
        effective_date DATE NOT NULL, expiration_date DATE NOT NULL,
        product_code STRING NOT NULL, insured_party_id STRING NOT NULL,
        source_updated_ts TIMESTAMP NOT NULL) USING DELTA""",
    """INSERT INTO workspace.agentic_insurance_demo_bronze.bronze_policy
        VALUES ("POL-0001","AUTO-2026-0001","ACTIVE",cast("2026-01-01" as date),cast("2026-12-31" as date),"PERSONAL_AUTO","PTY-0001",cast("2026-01-02T09:00:00Z" as timestamp)),
               ("POL-0002","HOME-2026-0002","CANCELLED",cast("2026-02-01" as date),cast("2027-01-31" as date),"HOMEOWNERS","PTY-0002",cast("2026-03-04T14:30:00Z" as timestamp))""",
    """CREATE TABLE IF NOT EXISTS workspace.agentic_insurance_demo_bronze.bronze_policyholder (
        party_id STRING NOT NULL, party_type STRING NOT NULL, display_name STRING NOT NULL,
        contact_channel STRING, source_updated_ts TIMESTAMP NOT NULL) USING DELTA""",
    """INSERT INTO workspace.agentic_insurance_demo_bronze.bronze_policyholder
        VALUES ("PTY-0001","PERSON","Sample Policyholder A","EMAIL",cast("2026-01-02T09:05:00Z" as timestamp)),
               ("PTY-0002","PERSON","Sample Policyholder B","PHONE",cast("2026-03-04T14:35:00Z" as timestamp))""",
    """CREATE TABLE IF NOT EXISTS workspace.agentic_insurance_demo_bronze.bronze_claim (
        claim_id STRING NOT NULL, policy_id STRING NOT NULL, loss_date DATE NOT NULL,
        claim_status STRING NOT NULL, claimed_amount DECIMAL(12,2) NOT NULL,
        source_updated_ts TIMESTAMP NOT NULL) USING DELTA""",
    """INSERT INTO workspace.agentic_insurance_demo_bronze.bronze_claim
        VALUES ("CLM-0001","POL-0001",cast("2026-02-14" as date),"OPEN",1250.00,cast("2026-02-15T10:00:00Z" as timestamp)),
               ("CLM-0002","POL-0002",cast("2026-02-20" as date),"CLOSED",300.00,cast("2026-02-23T16:15:00Z" as timestamp))""",
]

for s in stmts:
    r = w.statement_execution.execute_statement(warehouse_id=WH, statement=s, wait_timeout="30s")
    print(f"  OK: {s[:80]}...")
print("Done. 3 synthetic Bronze tables created in workspace.agentic_insurance_demo_bronze.")
