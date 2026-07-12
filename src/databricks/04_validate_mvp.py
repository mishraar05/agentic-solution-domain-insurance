# Databricks notebook source
# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC # 04 — Validate Source Intelligence outputs and record the run
# MAGIC
# MAGIC Validates the current run's artifacts only (run-scoped, since persistence is
# MAGIC append-based), checks run-ID consistency across artifacts, and writes a
# MAGIC contract-validated `source_intelligence_run` record.

# COMMAND ----------

from datetime import datetime, timezone

from pyspark.sql import Row
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType, StructField, StructType, TimestampType

from source_intelligence.contract_validation import validate_records

# COMMAND ----------

existing_source_tables = {
    row.tableName
    for row in spark.sql(f"SHOW TABLES IN `{SOURCE_CATALOG}`.`{SOURCE_SCHEMA}`").collect()
    if not row.isTemporary
}
missing_inputs = set(SOURCE_TABLES) - existing_source_tables
assert not missing_inputs, f"Missing configured source inputs: {sorted(missing_inputs)}"

required_outputs = {"source_observation_dictionary", "review_queue"}
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
queue = spark.table(fq_output_table("review_queue")).filter(F.col("run_id") == RUN_ID)

dictionary_rows = dictionary.count()
queue_rows = queue.count()

# Run-context consistency: this run must have produced both artifacts.
assert dictionary_rows > 0, (
    f"No dictionary records for run {RUN_ID}. If tasks generated different run IDs, "
    "pass a shared run_id job parameter (si_job_{{job.run_id}})."
)
assert queue_rows > 0, f"No review-queue records for run {RUN_ID} (same run-context requirement)."

assert dictionary.filter(F.col("confidence_score").isNull()).count() == 0, \
    "Every record needs a confidence score."
assert dictionary.filter(F.col("evidence_coverage").isNull()).count() == 0, \
    "Every record needs evidence coverage."
assert dictionary.filter(F.col("formula_version").isNull()).count() == 0, \
    "Every record needs the confidence formula version."
assert dictionary.filter(F.col("approval_state") != "PROPOSED").count() == 0, \
    "The solution must not auto-approve recommendations."
assert queue.filter(F.col("queue_status") != "OPEN").count() == 0, \
    "The review queue should contain open work only."

# Mandatory key review: every key candidate must be queued for the Data Architect.
key_candidates = dictionary.filter(F.col("key_role") != "NON_KEY").count()
queued_keys = queue.filter(
    (F.col("key_role") != "NON_KEY")
    & (F.col("recommended_reviewer_role") == "DATA_ARCHITECT")
).count()
assert queued_keys >= key_candidates, (
    f"{key_candidates} key candidates but only {queued_keys} queued for the Data Architect."
)

# COMMAND ----------

completed_at = datetime.now(timezone.utc)
run_record = {
    "schema_version": SCHEMA_VERSION,
    "run_id": RUN_ID,
    "artifact_version": ARTIFACT_VERSION,
    "engagement_id": ENGAGEMENT_ID,
    "source_system": SOURCE_SYSTEM,
    "source_scope": list(SOURCE_TABLES),
    "run_status": "COMPLETED",
    "started_at": completed_at.isoformat(),
}
validate_records([run_record], "source_intelligence_run.json")

run_schema = StructType([
    StructField("schema_version", StringType(), False),
    StructField("run_id", StringType(), False),
    StructField("artifact_version", StringType(), False),
    StructField("engagement_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("source_scope", StringType(), False),
    StructField("run_status", StringType(), False),
    StructField("dictionary_rows", IntegerType(), False),
    StructField("review_queue_rows", IntegerType(), False),
    StructField("completed_at", TimestampType(), False),
])
run_df = spark.createDataFrame(
    [Row(
        schema_version=SCHEMA_VERSION, run_id=RUN_ID, artifact_version=ARTIFACT_VERSION,
        engagement_id=ENGAGEMENT_ID, source_system=SOURCE_SYSTEM,
        source_scope=",".join(SOURCE_TABLES), run_status="COMPLETED",
        dictionary_rows=dictionary_rows, review_queue_rows=queue_rows,
        completed_at=completed_at,
    )],
    schema=run_schema,
)
run_df.write.format("delta").mode("append").saveAsTable(fq_table("source_intelligence_run"))

# COMMAND ----------

summary = {
    "run_id": RUN_ID,
    "configured_source_tables": len(SOURCE_TABLES),
    "dictionary_rows": dictionary_rows,
    "review_queue_rows": queue_rows,
    "key_candidates_queued_for_architect": queued_keys,
    "low_confidence_rows": dictionary.filter(
        F.col("confidence_score") < LOW_CONFIDENCE_THRESHOLD).count(),
    "personal_data_rows": dictionary.filter(F.col("privacy_class") != "INTERNAL").count(),
}
print("Source Intelligence validation passed")
for key, value in summary.items():
    print(f"{key}: {value}")

display(dictionary.groupBy("domain", "approval_state").count().orderBy("domain", "approval_state"))
