# Databricks notebook source
"""Validate Source Intelligence outputs and persist the governed run record.

This terminal core-workflow task verifies that all configured source inputs
and required recommendation outputs exist for one shared ``run_id``. It checks
attribute and object coverage, minimized profile evidence, runtime-discovered
relationships, evidence references, mandatory key routing, no auto-approval,
Source Documentation Agent coverage, and retry idempotency.

After the assertions pass, the notebook creates a contract-validated
``source_intelligence_run`` record containing scope, reproducibility context,
an idempotency key, status, timestamps, and metrics. The record is appended
only once for the run. A failed assertion stops the job and no successful run
record is fabricated.

This notebook validates recommendation artifacts only. It does not authorize
them, change reviewer decisions, deploy schemas, or mutate source/Bronze data.
Run it after ``04_create_review_queue.py``.
"""

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 05 — Validate Source Intelligence outputs and record the run
# MAGIC
# MAGIC Run-scoped validation, run-ID consistency checks, and a `source_intelligence_run`
# MAGIC record. The persisted record IS the validated record: identical fields and
# MAGIC values; defined physical serialization only (ISO timestamps -> TIMESTAMP,
# MAGIC metrics object -> JSON string, source_scope -> ARRAY<STRING>). Retry-idempotent.

# COMMAND ----------

import hashlib
import json
from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, StringType, StructField, StructType, TimestampType

from source_intelligence.contract_validation import validate_records
from source_intelligence.source_documentation import PROMPT_VERSION

# COMMAND ----------

existing_source_tables = {
    row.tableName
    for row in spark.sql(f"SHOW TABLES IN `{SOURCE_CATALOG}`.`{SOURCE_SCHEMA}`").collect()
    if not row.isTemporary
}
missing_inputs = set(SOURCE_TABLES) - existing_source_tables
assert not missing_inputs, f"Missing configured source inputs: {sorted(missing_inputs)}"

required_outputs = {
    "source_observation_dictionary",
    "source_attribute_observation",
    "source_object_observation",
    "profile_evidence",
    "relationship_candidate",
    "source_documentation_recommendation",
    "review_queue",
    "source_intelligence_review_queue",
}
existing_outputs = {
    row.tableName
    for row in spark.sql(f"SHOW TABLES IN `{OUTPUT_CATALOG}`.`{OUTPUT_SCHEMA}`").collect()
    if not row.isTemporary
}
missing_outputs = required_outputs - existing_outputs
assert not missing_outputs, f"Missing recommendation outputs: {sorted(missing_outputs)}"

# COMMAND ----------

dictionary = spark.table(fq_output_table("source_observation_dictionary")).filter(
    F.col("run_id") == RUN_ID
)
queue = spark.table(fq_output_table("source_intelligence_review_queue")).filter(
    F.col("run_id") == RUN_ID
)
attributes = spark.table(fq_output_table("source_attribute_observation")).filter(
    F.col("run_id") == RUN_ID
)
objects = spark.table(fq_output_table("source_object_observation")).filter(
    F.col("run_id") == RUN_ID
)
profiles = spark.table(fq_output_table("profile_evidence")).filter(
    F.col("run_id") == RUN_ID
)
relationships = spark.table(fq_output_table("relationship_candidate")).filter(
    F.col("run_id") == RUN_ID
)
documentation = spark.table(
    fq_output_table("source_documentation_recommendation")
).filter(F.col("run_id") == RUN_ID)

dictionary_rows = dictionary.count()
queue_rows = queue.count()

assert dictionary_rows > 0, (
    f"No dictionary records for run {RUN_ID}. If tasks generated different run IDs, "
    "pass a shared run_id job parameter (si_job_{{job.run_id}})."
)
assert attributes.count() == dictionary_rows, \
    "Every dictionary attribute must have a canonical attribute observation."
assert documentation.count() == dictionary_rows, \
    "Every canonical attribute must have one documentation recommendation."
assert objects.count() == len(SOURCE_TABLES), \
    "Every configured source object must have an object observation."
internal_attributes = attributes.filter(
    F.col("privacy_class") == "INTERNAL"
).count()
assert profiles.count() == internal_attributes * 2, (
    "Each governance-permitted internal attribute must have NULL_RATE and "
    "DISTINCT_COUNT evidence; personal attributes must have none."
)
assert relationships.filter(F.col("approval_state") != "PROPOSED").count() == 0, \
    "Relationship candidates must remain proposed until architect review."
assert relationships.filter(
    F.col("reviewer_role") != "DATA_ARCHITECT"
).count() == 0, "Every relationship candidate must route to the Data Architect."
assert attributes.filter(F.size("evidence_references") == 0).count() == 0, \
    "Every attribute observation must retain physical-metadata evidence references."
assert profiles.filter(F.col("privacy_class") != "INTERNAL").count() == 0, \
    "Personal-data columns must be rejected before value-level profiling."
assert documentation.filter(F.col("approval_state") != "PROPOSED").count() == 0, \
    "Source documentation must remain proposed until Domain Steward review."
assert documentation.filter(F.col("reviewer_role") != "DOMAIN_STEWARD").count() == 0, \
    "Every source-documentation recommendation must route to a Domain Steward."
assert documentation.filter(F.size("evidence_references") == 0).count() == 0, \
    "Every documentation recommendation must retain evidence references."
assert documentation.filter(F.col("prompt_version") != PROMPT_VERSION).count() == 0, \
    "Every documentation recommendation must record the active prompt version."
assert documentation.filter(
    F.col("model_endpoint") != DOCUMENTATION_MODEL_ENDPOINT
).count() == 0, "Every documentation recommendation must record the model endpoint."

privacy_documentation = documentation.join(
    attributes.select("source_table", "source_column", "privacy_class"),
    ["source_table", "source_column"],
).filter(F.col("privacy_class") != "INTERNAL")
assert privacy_documentation.filter(
    (F.col("generation_status") != "UNRESOLVED")
    | F.col("proposed_column_description").isNotNull()
    | F.col("proposed_glossary_definition").isNotNull()
).count() == 0, (
    "Personal or sensitive attributes must not receive LLM-generated documentation."
)

privacy_attributes = attributes.filter(
    F.col("privacy_class") != "INTERNAL"
).count()
queued_privacy = queue.filter(
    F.col("recommended_reviewer_role") == "PRIVACY_STEWARD"
).count()
assert queued_privacy >= privacy_attributes, (
    f"{privacy_attributes} privacy-relevant attributes but only "
    f"{queued_privacy} Privacy Steward queue items."
)

queued_documentation = queue.filter(
    (F.col("review_trigger") == "SOURCE_DOCUMENTATION")
    & (F.col("recommended_reviewer_role") == "DOMAIN_STEWARD")
).count()
assert queued_documentation == documentation.count(), (
    f"{documentation.count()} documentation recommendations but "
    f"{queued_documentation} Domain Steward queue items."
)

# Retry idempotency: identical rerun must not duplicate canonical attributes.
dup = (attributes.groupBy("source_table", "source_column", "artifact_version")
       .count().filter(F.col("count") > 1).count())
assert dup == 0, f"{dup} duplicate attribute records for run {RUN_ID} — idempotency violated."
documentation_dup = (
    documentation.groupBy("source_table", "source_column", "artifact_version")
    .count().filter(F.col("count") > 1).count()
)
assert documentation_dup == 0, (
    f"{documentation_dup} duplicate documentation records for run {RUN_ID}."
)

assert attributes.filter(F.col("confidence_score").isNull()).count() == 0, \
    "Every record needs a confidence score."
assert attributes.filter(F.col("evidence_coverage").isNull()).count() == 0, \
    "Every record needs evidence coverage."
assert attributes.filter(F.col("formula_version").isNull()).count() == 0, \
    "Every record needs the confidence formula version."
assert attributes.filter(F.col("approval_state") != "PROPOSED").count() == 0, \
    "The solution must not auto-approve recommendations."
assert queue.filter(F.col("queue_status") != "OPEN").count() == 0, \
    "The review queue should contain open work only."

key_candidates = attributes.filter(F.col("key_role") != "NON_KEY").count()
queued_keys = queue.filter(
    (F.col("key_role") != "NON_KEY")
    & (F.col("recommended_reviewer_role") == "DATA_ARCHITECT")
).count()
assert queued_keys >= key_candidates, (
    f"{key_candidates} key candidates but only {queued_keys} queued for the Data Architect."
)

# COMMAND ----------

completed_at = datetime.now(timezone.utc)
idempotency_key = hashlib.sha256(json.dumps({
    "source_system": SOURCE_SYSTEM,
    "source_scope": list(SOURCE_TABLES),
    "artifact_version": ARTIFACT_VERSION,
    "schema_version": SCHEMA_VERSION,
    "knowledge_pack_versions": {},
    "documentation_model_endpoint": DOCUMENTATION_MODEL_ENDPOINT,
    "documentation_prompt_version": PROMPT_VERSION,
}, sort_keys=True).encode()).hexdigest()

run_record = {
    "schema_version": SCHEMA_VERSION,
    "run_id": RUN_ID,
    "artifact_version": ARTIFACT_VERSION,
    "engagement_id": ENGAGEMENT_ID,
    "source_system": SOURCE_SYSTEM,
    "source_scope": list(SOURCE_TABLES),
    "knowledge_pack_versions": {},
    "task_contract_version": SCHEMA_VERSION,
    "idempotency_key": idempotency_key,
    "run_status": "SUCCEEDED",
    "started_at": RUN_STARTED_AT.isoformat(),
    "completed_at": completed_at.isoformat(),
    "metrics": {
        "objects_observed": objects.count(),
        "attributes_observed": attributes.count(),
        "relationships_inferred": relationships.count(),
        "documentation_recommendations": documentation.count(),
        "privacy_classifications": attributes.filter(
            F.col("privacy_class") != "INTERNAL").count(),
        "review_items_created": queue_rows,
        "policy_violations": 0,
    },
    "error_info": None,
}
# The record persisted below is EXACTLY this validated record.
validate_records([run_record], "source_intelligence_run.json")
print("Run-record contract validation passed")

# COMMAND ----------

run_table = fq_table("source_intelligence_run")
run_exists = (
    spark.catalog.tableExists(run_table)
    and spark.table(run_table).filter(F.col("run_id") == RUN_ID).count() > 0
)
if run_exists:
    print(f"Idempotent skip: run record for {RUN_ID} already exists.")
else:
    run_schema = StructType([
        StructField("schema_version", StringType(), False),
        StructField("run_id", StringType(), False),
        StructField("artifact_version", StringType(), False),
        StructField("engagement_id", StringType(), False),
        StructField("source_system", StringType(), False),
        StructField("source_scope", ArrayType(StringType()), False),
        StructField("knowledge_pack_versions", StringType(), False),
        StructField("task_contract_version", StringType(), False),
        StructField("idempotency_key", StringType(), False),
        StructField("run_status", StringType(), False),
        StructField("started_at", TimestampType(), False),
        StructField("completed_at", TimestampType(), False),
        StructField("metrics", StringType(), False),
        StructField("error_info", StringType(), True),
    ])
    # Defined physical serialization of the validated record — no other changes.
    run_df = spark.createDataFrame([Row(**{
        **run_record,
        "knowledge_pack_versions": json.dumps(run_record["knowledge_pack_versions"]),
        "metrics": json.dumps(run_record["metrics"]),
        "started_at": RUN_STARTED_AT,
        "completed_at": completed_at,
    })], schema=run_schema)
    run_df.write.format("delta").mode("append").saveAsTable(run_table)

# COMMAND ----------

print("Source Intelligence validation passed")
for key in ("run_id", "run_status", "started_at", "completed_at"):
    print(f"{key}: {run_record[key]}")
for key, value in run_record["metrics"].items():
    print(f"{key}: {value}")

display(attributes.groupBy("domain", "approval_state").count().orderBy("domain", "approval_state"))
