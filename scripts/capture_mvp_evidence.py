"""Capture MVP evidence from Databricks tables and write a machine-readable evidence artifact."""
import json
import os
from datetime import datetime, timezone

from databricks.sdk import WorkspaceClient

CATALOG = "workspace"
SCHEMA = "agentic_insurance_mvp"
WAREHOUSE_ID = "21014374f253edf2"

w = WorkspaceClient(profile="DEV")

queries = {
    "tables": f"SHOW TABLES IN {CATALOG}.{SCHEMA}",
    "dictionary": (
        f"SELECT source_table, source_column, physical_type, key_role, "
        f"relationship_evidence, proposed_business_name, ontology_concept_id, "
        f"domain, confidence_score, privacy_class, approval_state, "
        f"run_id, artifact_version "
        f"FROM {CATALOG}.{SCHEMA}.source_observation_dictionary "
        f"ORDER BY source_table, ordinal_position"
    ),
    "review_queue": (
        f"SELECT source_table, source_column, proposed_business_name, domain, "
        f"ontology_concept_id, confidence_score, privacy_class, "
        f"review_reason, recommended_reviewer_role, queue_status, run_id "
        f"FROM {CATALOG}.{SCHEMA}.review_queue "
        f"ORDER BY recommended_reviewer_role, source_table, source_column"
    ),
    "source_scope": (
        f"SELECT source_system, source_table, COUNT(*) AS observed_attributes "
        f"FROM {CATALOG}.{SCHEMA}.source_observation_dictionary "
        f"GROUP BY source_system, source_table "
        f"ORDER BY source_system, source_table"
    ),
    "counts": (
        f"SELECT "
        f"(SELECT COUNT(*) FROM {CATALOG}.{SCHEMA}.source_observation_dictionary) AS dictionary_rows, "
        f"(SELECT COUNT(*) FROM {CATALOG}.{SCHEMA}.review_queue) AS review_queue_rows"
    ),
    "validation": (
        f"SELECT "
        f"COUNT(*) AS dictionary_rows, "
        f"SUM(CASE WHEN confidence_score IS NULL THEN 1 ELSE 0 END) AS null_confidence_rows, "
        f"SUM(CASE WHEN approval_state != 'PROPOSED' THEN 1 ELSE 0 END) AS auto_approved_rows, "
        f"SUM(CASE WHEN confidence_score < 0.75 THEN 1 ELSE 0 END) AS low_confidence_rows, "
        f"SUM(CASE WHEN privacy_class != 'INTERNAL' THEN 1 ELSE 0 END) AS personal_data_rows, "
        f"SUM(CASE WHEN relationship_evidence IS NOT NULL THEN 1 ELSE 0 END) AS relationship_rows "
        f"FROM {CATALOG}.{SCHEMA}.source_observation_dictionary"
    ),
    "domain_summary": (
        f"SELECT domain, approval_state, COUNT(*) AS count "
        f"FROM {CATALOG}.{SCHEMA}.source_observation_dictionary "
        f"GROUP BY domain, approval_state "
        f"ORDER BY domain, approval_state"
    ),
}

results = {}
for name, sql in queries.items():
    print(f"Running query: {name}")
    resp = w.statement_execution.execute_statement(
        warehouse_id=WAREHOUSE_ID,
        statement=sql,
        wait_timeout="50s",
    )
    columns = [c.name for c in resp.manifest.schema.columns] if resp.manifest and resp.manifest.schema else []
    rows = resp.result.data_array if resp.result and resp.result.data_array else []
    results[name] = {
        "columns": columns,
        "rows": [list(r) for r in rows],
        "row_count": len(rows),
    }

evidence = {
    "captured_at": datetime.now(timezone.utc).isoformat(),
    "catalog": CATALOG,
    "schema": SCHEMA,
    "warehouse_id": WAREHOUSE_ID,
    "profile": "DEV",
    "results": results,
}

evidence_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "evidence")
os.makedirs(evidence_dir, exist_ok=True)
evidence_path = os.path.join(evidence_dir, "mvp_run_evidence.json")
with open(evidence_path, "w", encoding="utf-8") as f:
    json.dump(evidence, f, indent=2, default=str)

print(f"\nEvidence written to: {evidence_path}")
print(f"\n--- Summary ---")
print(f"Tables: {results['tables']['row_count']}")
print(f"Dictionary rows: {results['dictionary']['row_count']}")
print(f"Review queue rows: {results['review_queue']['row_count']}")
print(f"Validation: {results['validation']['rows']}")
